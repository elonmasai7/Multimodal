import asyncio
import hashlib
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.core.errors import (
    AIIntegrationError,
    AppError,
    ExternalServiceError,
    MediaGenerationError,
    ModelInferenceError,
    StorageError,
    TimeoutError,
)
from app.core.logging import set_stage
from app.core.metrics import emit_failure_metric, emit_success_metric
from app.core.observability import get_tracer
from app.core.retry import retry_async, retry_sync
from app.core.validation import fallback_resolutions, validate_prompt, validate_resolution
from app.models.schemas import VideoOptions
from app.services.gcs_media import GCSMediaService
from app.services.redis_state import RedisStateManager

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from vertexai.preview.vision_models import ImageGenerationModel
except Exception:
    vertexai = None
    GenerativeModel = None
    ImageGenerationModel = None

try:
    from google.cloud import texttospeech
except Exception:
    texttospeech = None

logger = logging.getLogger("ai.orchestrator")


GPU_ERROR_MARKERS = (
    "CUDA out of memory",
    "RESOURCE_EXHAUSTED",
    "out of memory",
    "OOM",
    "device lost",
)


def new_session_id() -> str:
    return str(uuid.uuid4())


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _sse(event: str, session_type: str, data: object) -> str:
    payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": _timestamp(),
        "session_type": session_type,
        "data": data,
    }
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _safe_unlink(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        logger.warning("temp_cleanup_failed", extra={"path": path})


def _is_gpu_error(exc: Exception) -> bool:
    message = str(exc)
    return any(marker.lower() in message.lower() for marker in GPU_ERROR_MARKERS)


class VertexMultimodalEngine:
    def __init__(self) -> None:
        self._ready = False
        self.gcs: GCSMediaService | None = None
        self.text_model_backup = None
        self.image_model_backup = None

    def _init_clients(self) -> None:
        if self._ready:
            return

        if not settings.gcp_project_id:
            raise AIIntegrationError("GCP_PROJECT_ID is required")
        if not settings.gcs_media_bucket:
            raise MediaGenerationError("GCS_MEDIA_BUCKET is required")
        if not settings.videofx_endpoint:
            raise MediaGenerationError("VIDEOFX_ENDPOINT is required")
        if vertexai is None or GenerativeModel is None or ImageGenerationModel is None:
            raise AIIntegrationError("Vertex AI SDK not installed correctly")

        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
        self.text_model = GenerativeModel(settings.vertex_model_text)
        self.image_model = ImageGenerationModel.from_pretrained(settings.vertex_model_image)
        if settings.vertex_model_text_backup:
            self.text_model_backup = GenerativeModel(settings.vertex_model_text_backup)
        if settings.vertex_model_image_backup:
            self.image_model_backup = ImageGenerationModel.from_pretrained(settings.vertex_model_image_backup)
        self.tts_client = texttospeech.TextToSpeechClient() if texttospeech else None
        self.gcs = GCSMediaService()
        self._ready = True

    def generate_lesson_plan(self, prompt: str, session_type: str) -> dict:
        self._init_clients()
        instruction = (
            "Return strict JSON only with keys: title, narration, sections, image_prompt, video_prompt, quiz. "
            "quiz must include id, question, options (array), correct. "
            f"Build a {session_type} learning experience for prompt: {prompt}"
        )
        set_stage("inference")

        def _call(model) -> dict:
            response = model.generate_content(instruction)
            text = getattr(response, "text", "")
            if not text:
                raise AIIntegrationError("Gemini returned empty content")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            # Gemini often wraps JSON in markdown code blocks — strip and retry
            stripped = text.strip()
            if stripped.startswith("```"):
                stripped = stripped.split("\n", 1)[-1]
                stripped = stripped.rsplit("```", 1)[0].strip()
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    pass
            logger.warning("Gemini JSON parse failed; applying fallback extractor")
            return {
                "title": f"{session_type.title()} Session",
                "narration": text,
                "sections": ["Introduction", "Visual concept", "Practice", "Quiz"],
                "image_prompt": f"Educational diagram about {prompt}",
                "video_prompt": f"Short explanation video about {prompt}",
                "quiz": {
                    "id": "q1",
                    "question": "Which choice best summarizes the concept?",
                    "options": ["A", "B", "C", "D"],
                    "correct": "B",
                },
            }

        def _run_with_model(model) -> dict:
            return retry_sync(
                lambda: _call(model),
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="inference",
                retry_on=(Exception,),
            )

        try:
            return _run_with_model(self.text_model)
        except Exception as exc:
            if self.text_model_backup is not None:
                logger.warning("primary_text_model_failed_fallback", extra={"error": str(exc)})
                return _run_with_model(self.text_model_backup)
            if _is_gpu_error(exc):
                raise ModelInferenceError(str(exc), safe_message="GPU memory exhausted during inference") from exc
            raise ModelInferenceError(str(exc)) from exc

    def generate_image(self, image_prompt: str) -> dict:
        self._init_clients()
        set_stage("rendering")
        filename = f"/tmp/{uuid.uuid4()}.png"
        try:
            images = self.image_model.generate_images(prompt=image_prompt, number_of_images=1)
            image = images[0]
            image.save(location=filename)

            uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="images", content_type="image/png")
            return {
                "gcs_uri": uploaded.gcs_uri,
                "signed_url": uploaded.signed_url,
                "caption": image_prompt,
            }
        except StorageError:
            raise
        except Exception as exc:
            if self.image_model_backup is not None:
                logger.warning("primary_image_model_failed_fallback", extra={"error": str(exc)})
                images = self.image_model_backup.generate_images(prompt=image_prompt, number_of_images=1)
                image = images[0]
                image.save(location=filename)
                uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="images", content_type="image/png")
                return {
                    "gcs_uri": uploaded.gcs_uri,
                    "signed_url": uploaded.signed_url,
                    "caption": image_prompt,
                }
            if _is_gpu_error(exc):
                raise MediaGenerationError("GPU memory exhausted during image generation", stage="rendering") from exc
            raise MediaGenerationError(str(exc)) from exc
        finally:
            _safe_unlink(filename)

    def synthesize_audio(self, text: str) -> dict:
        self._init_clients()
        if not self.tts_client:
            raise MediaGenerationError("Google Text-to-Speech client unavailable")

        set_stage("rendering")
        filename = f"/tmp/{uuid.uuid4()}.mp3"
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text[:5000])
            voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Neural2-C")
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            with open(filename, "wb") as f:
                f.write(response.audio_content)

            uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="audio", content_type="audio/mpeg")
            return {
                "gcs_uri": uploaded.gcs_uri,
                "signed_url": uploaded.signed_url,
            }
        except StorageError:
            raise
        except Exception as exc:
            raise MediaGenerationError(str(exc)) from exc
        finally:
            _safe_unlink(filename)

    def _extract_video_urls(self, data: object) -> tuple[str | None, str | None]:
        if not isinstance(data, dict):
            return None, None

        def _pick(d: dict, keys: tuple[str, ...]) -> str | None:
            for key in keys:
                value = d.get(key)
                if isinstance(value, str) and value:
                    return value
            return None

        gcs_uri = _pick(data, ("gcs_uri", "gcsUri", "output_gcs_uri", "outputGcsUri", "uri"))
        signed_url = _pick(
            data,
            ("signed_url", "signedUrl", "url", "video_url", "videoUrl", "download_url", "downloadUrl"),
        )
        return gcs_uri, signed_url

    def _parse_videofx_response(self, response: httpx.Response) -> dict | None:
        content_type = response.headers.get("content-type", "")
        text = response.text.strip()

        if "application/json" in content_type:
            try:
                data = response.json()
            except Exception:
                data = None
            if isinstance(data, dict):
                # Common nesting patterns
                for key in ("video", "data", "result", "payload", "output"):
                    nested = data.get(key)
                    if isinstance(nested, dict):
                        gcs_uri, signed_url = self._extract_video_urls(nested)
                        if gcs_uri or signed_url:
                            if gcs_uri and not signed_url:
                                signed_url = self.gcs.sign_gcs_uri(str(gcs_uri))
                            return {"gcs_uri": gcs_uri, "signed_url": signed_url} if gcs_uri else {"signed_url": signed_url}

                gcs_uri, signed_url = self._extract_video_urls(data)
                if gcs_uri or signed_url:
                    if gcs_uri and not signed_url:
                        signed_url = self.gcs.sign_gcs_uri(str(gcs_uri))
                    return {"gcs_uri": gcs_uri, "signed_url": signed_url} if gcs_uri else {"signed_url": signed_url}

                # List-based response: outputs/videos/generated_videos
                for key in ("outputs", "videos", "generated_videos"):
                    items = data.get(key)
                    if isinstance(items, list) and items:
                        first = items[0]
                        if isinstance(first, dict):
                            gcs_uri, signed_url = self._extract_video_urls(first)
                            if gcs_uri or signed_url:
                                if gcs_uri and not signed_url:
                                    signed_url = self.gcs.sign_gcs_uri(str(gcs_uri))
                                return {"gcs_uri": gcs_uri, "signed_url": signed_url} if gcs_uri else {"signed_url": signed_url}

        if text.startswith("gs://"):
            return {"gcs_uri": text, "signed_url": self.gcs.sign_gcs_uri(text)}
        if text.startswith("http://") or text.startswith("https://"):
            return {"signed_url": text}
        return None

    def _videofx_request(
        self,
        *,
        endpoint: str,
        video_prompt: str,
        options: VideoOptions,
        use_alt_schema: bool = False,
    ) -> dict:
        headers = {"Content-Type": "application/json"}
        if settings.videofx_api_key:
            headers["Authorization"] = f"Bearer {settings.videofx_api_key}"

        if use_alt_schema:
            payload: dict[str, object] = {
                "textPrompt": video_prompt,
                "durationSeconds": options.duration_seconds,
                "resolution": options.resolution,
                "fps": options.fps,
                "format": options.format,
            }
        else:
            payload = {
                "prompt": video_prompt,
                "duration_seconds": options.duration_seconds,
                "resolution": options.resolution,
                "fps": options.fps,
                "format": options.format,
            }
        if settings.gcs_media_bucket:
            if use_alt_schema:
                payload["outputGcsUri"] = f"gs://{settings.gcs_media_bucket}/videos"
            else:
                payload["output_gcs_uri"] = f"gs://{settings.gcs_media_bucket}/videos"

        with httpx.Client(timeout=settings.videofx_timeout_seconds) as client:
            response = client.post(endpoint, headers=headers, json=payload)

        if response.status_code in {400, 422} and not use_alt_schema:
            return self._videofx_request(
                endpoint=endpoint,
                video_prompt=video_prompt,
                options=options,
                use_alt_schema=True,
            )

        if response.status_code >= 400:
            raise MediaGenerationError(
                f"VideoFX endpoint returned {response.status_code}",
                details={"status_code": response.status_code, "body": response.text[:500]},
                stage="rendering",
            )

        parsed = self._parse_videofx_response(response)
        if parsed:
            return parsed
        raise MediaGenerationError("VideoFX response missing video URL", details={"body": response.text[:500]})

    def _generate_video_sync(self, *, video_prompt: str, options: VideoOptions) -> dict:
        endpoint = settings.videofx_endpoint
        if not endpoint:
            raise MediaGenerationError("VIDEOFX_ENDPOINT is required")
        try:
            return self._videofx_request(endpoint=str(endpoint), video_prompt=video_prompt, options=options)
        except Exception as exc:
            fallback_endpoint = settings.videofx_fallback_endpoint
            if not fallback_endpoint:
                raise
            logger.warning("videofx_primary_failed_fallback", extra={"error": str(exc)})
            fallback_options = VideoOptions(
                duration_seconds=settings.videofx_fallback_duration_seconds,
                resolution=settings.videofx_fallback_resolution,
                fps=options.fps,
                format=options.format,
            )
            return self._videofx_request(
                endpoint=str(fallback_endpoint),
                video_prompt=video_prompt,
                options=fallback_options,
            )

    async def generate_video(self, *, video_prompt: str, options: VideoOptions | None = None) -> dict:
        self._init_clients()
        set_stage("inference")
        resolved_options = options or VideoOptions()
        return await asyncio.to_thread(self._generate_video_sync, video_prompt=video_prompt, options=resolved_options)


engine = VertexMultimodalEngine()
redis_state = RedisStateManager()


def _cache_key(prompt: str, session_type: str) -> str:
    return hashlib.sha256(f"{session_type}:{prompt}".encode()).hexdigest()


async def stream_multimodal_events(
    prompt: str,
    session_type: str,
    *,
    video_options: VideoOptions | None = None,
    request_id: str | None = None,
) -> AsyncGenerator[str, None]:
    tracer = get_tracer()
    span_manager = None
    if tracer:
        span_manager = tracer.start_as_current_span(
            "pipeline.generate",
            attributes={
                "session_type": session_type,
                "request_id": request_id or "",
            },
        )
    if span_manager:
        span_manager.__enter__()

    try:
        validated_prompt = validate_prompt(prompt)
        options = video_options or VideoOptions()
        validate_resolution(options.resolution)

        options_key = json.dumps(options.model_dump(), sort_keys=True)
        key = _cache_key(f"{validated_prompt}:{options_key}", session_type)
        cached = await redis_state.get_ai_cache(key=key)
        if cached:
            yield _sse("status", session_type, {"message": "Loaded cached generation"})
            for event_name in ["text", "image", "video", "audio", "quiz"]:
                if event_name in cached:
                    yield _sse(event_name, session_type, cached[event_name])
            yield _sse("done", session_type, {"status": "completed", "cached": True})
            return
    except AppError as exc:
        yield _sse("error", session_type, exc.to_payload(request_id=request_id))
        yield _sse("done", session_type, {"status": "failed"})
        return

    start = datetime.now(UTC)
    try:
        yield _sse("status", session_type, {"message": "Generating structured lesson plan with Gemini"})
        async def _run_plan():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(engine.generate_lesson_plan, validated_prompt, session_type),
                    timeout=settings.model_inference_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise TimeoutError("Text model timed out", stage="inference") from exc

        if tracer:
            with tracer.start_as_current_span("pipeline.text", attributes={"stage": "inference"}):
                plan = await retry_async(
                    _run_plan,
                    attempts=settings.retry_max_attempts,
                    base_delay=settings.retry_base_delay_seconds,
                    max_delay=settings.retry_max_delay_seconds,
                    stage="inference",
                    retry_on=(TimeoutError, ModelInferenceError, AIIntegrationError),
                )
        else:
            plan = await retry_async(
                _run_plan,
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="inference",
                retry_on=(TimeoutError, ModelInferenceError, AIIntegrationError),
            )

        narration = str(plan.get("narration", ""))
        title = str(plan.get("title", f"{session_type.title()} Session"))
        for chunk in [title, *[s.strip() for s in narration.split(".") if s.strip()]]:
            yield _sse("narration", session_type, {"content": chunk})
            await asyncio.sleep(0.05)

        text_payload = {
            "title": title,
            "content": narration,
            "sections": plan.get("sections", []),
        }
        yield _sse("text", session_type, text_payload)

        yield _sse("status", session_type, {"message": "Generating image with Imagen"})
        async def _run_image():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(engine.generate_image, str(plan.get("image_prompt", validated_prompt))),
                    timeout=settings.media_generation_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise TimeoutError("Image generation timed out", stage="rendering") from exc

        if tracer:
            with tracer.start_as_current_span("pipeline.image", attributes={"stage": "rendering"}):
                image_payload = await retry_async(
                    _run_image,
                    attempts=settings.retry_max_attempts,
                    base_delay=settings.retry_base_delay_seconds,
                    max_delay=settings.retry_max_delay_seconds,
                    stage="rendering",
                    retry_on=(TimeoutError, MediaGenerationError, StorageError),
                )
        else:
            image_payload = await retry_async(
                _run_image,
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="rendering",
                retry_on=(TimeoutError, MediaGenerationError, StorageError),
            )
        yield _sse("image", session_type, image_payload)

        yield _sse("status", session_type, {"message": "Generating video with Veo"})
        video_payload = None
        try:
            if tracer:
                with tracer.start_as_current_span("pipeline.video", attributes={"stage": "inference"}):
                    video_payload = await asyncio.wait_for(
                        engine.generate_video(
                            video_prompt=str(plan.get("video_prompt", validated_prompt)),
                            options=options,
                        ),
                        timeout=settings.videofx_timeout_seconds + 10,
                    )
            else:
                video_payload = await asyncio.wait_for(
                    engine.generate_video(
                        video_prompt=str(plan.get("video_prompt", validated_prompt)),
                        options=options,
                    ),
                    timeout=settings.videofx_timeout_seconds + 10,
                )
            yield _sse("video", session_type, video_payload)
        except Exception as video_exc:
            logger.warning("video_generation_skipped", extra={"reason": str(video_exc)})

        yield _sse("status", session_type, {"message": "Generating narration audio"})
        async def _run_audio():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(engine.synthesize_audio, narration),
                    timeout=settings.media_generation_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise TimeoutError("Audio generation timed out", stage="rendering") from exc

        if tracer:
            with tracer.start_as_current_span("pipeline.audio", attributes={"stage": "rendering"}):
                audio_payload = await retry_async(
                    _run_audio,
                    attempts=settings.retry_max_attempts,
                    base_delay=settings.retry_base_delay_seconds,
                    max_delay=settings.retry_max_delay_seconds,
                    stage="rendering",
                    retry_on=(TimeoutError, MediaGenerationError, StorageError),
                )
        else:
            audio_payload = await retry_async(
                _run_audio,
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="rendering",
                retry_on=(TimeoutError, MediaGenerationError, StorageError),
            )
        yield _sse("audio", session_type, audio_payload)

        quiz_payload = plan.get("quiz", {
            "id": "q1",
            "question": "Select the best summary",
            "options": ["A", "B", "C", "D"],
            "correct": "B",
        })
        yield _sse("quiz", session_type, quiz_payload)

        await redis_state.set_ai_cache(
            key=key,
            payload={
                "text": text_payload,
                "image": image_payload,
                "video": video_payload,
                "audio": audio_payload,
                "quiz": quiz_payload,
            },
            ttl_seconds=3600,
        )

        elapsed_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
        logger.info("generation_complete", extra={"session_type": session_type, "elapsed_ms": elapsed_ms})
        emit_success_metric(stage="response", duration_ms=elapsed_ms)
        yield _sse("done", session_type, {"status": "completed", "elapsed_ms": elapsed_ms})
    except Exception as exc:
        app_error = exc if isinstance(exc, AppError) else ExternalServiceError(str(exc), stage="response")
        logger.exception(
            "generation_failed",
            extra={
                "session_type": session_type,
                "request_id": request_id,
                "stage": app_error.stage,
                "error_type": app_error.type,
            },
        )
        emit_failure_metric(stage=app_error.stage, error_type=app_error.type)
        yield _sse("error", session_type, app_error.to_payload(request_id=request_id))
        yield _sse("done", session_type, {"status": "failed"})
    finally:
        if span_manager:
            span_manager.__exit__(None, None, None)
