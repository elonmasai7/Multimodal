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
from app.services.genai_client import get_genai_client
from app.services.gcs_media import GCSMediaService
from app.services.redis_state import RedisStateManager

try:
    from google.genai import types as genai_types
except Exception:
    genai_types = None

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


class GenAIMultimodalEngine:
    def __init__(self) -> None:
        self._ready = False
        self.gcs: GCSMediaService | None = None
        self.text_model_backup: str | None = None
        self.image_model_backup: str | None = None
        self.genai = None

    def _init_clients(self) -> None:
        if self._ready:
            return

        if genai_types is None:
            raise AIIntegrationError("Google GenAI SDK not installed correctly")
        if not settings.gcs_media_bucket:
            raise MediaGenerationError("GCS_MEDIA_BUCKET is required")
        self.genai = get_genai_client()
        self.text_model = settings.vertex_model_text
        self.image_model = settings.vertex_model_image
        if settings.vertex_model_text_backup:
            self.text_model_backup = settings.vertex_model_text_backup
        if settings.vertex_model_image_backup:
            self.image_model_backup = settings.vertex_model_image_backup
        self.tts_client = texttospeech.TextToSpeechClient() if texttospeech else None
        self.gcs = GCSMediaService()
        self._ready = True

    def generate_interleaved_content(self, *, prompt: str, session_type: str) -> dict:
        """
        Single Gemini call with response_modalities=["TEXT","IMAGE"] that produces
        a fluid mix of narration paragraphs and inline diagrams — the core of the
        interleaved multimodal pipeline described in the challenge brief.

        Returns:
            {
                "parts": [{"type": "text"|"image", ...}, ...],
                "title": str,
                "narration": str,   # full text for TTS
                "video_prompt": str,
                "quiz": {...},
            }
        """
        import base64

        self._init_clients()
        set_stage("inference")

        instruction = (
            f"You are a creative director producing an immersive {session_type} experience.\n"
            f"Topic: {prompt}\n\n"
            "Generate a rich, flowing educational narrative that INTERLEAVES explanatory text "
            "paragraphs with relevant diagrams and illustrations. After every 1-2 paragraphs, "
            "generate an inline illustration that visually supports what was just described.\n\n"
            "CRITICAL IMAGE RULES — every generated image MUST follow these strictly:\n"
            "1. Images must be purely visual scenes or illustrations — NO text, words, letters, "
            "labels, captions, titles, watermarks, or any written characters embedded in the "
            "image pixels whatsoever.\n"
            "2. Style: painterly storybook illustration or cinematic concept art. Clean, expressive, "
            "no UI overlays, no diagrams with text annotations.\n"
            "3. If the scene naturally involves a book, sign, or screen, show it as a visual prop "
            "only — do not render legible text on it.\n\n"
            "At the very end of your response, output ONLY the following JSON block on its own "
            "line (no markdown, no extra text before or after it):\n"
            '{"title":"...","narration":"...one paragraph for TTS...","video_prompt":"...one cinematic sentence...","quiz":{"id":"q1","question":"...","options":["A","B","C","D"],"correct":"B"}}'
        )

        try:
            response = self.genai.models.generate_content(
                model=settings.vertex_model_interleaved,
                contents=instruction,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )
        except Exception as exc:
            # Model not available on this project — fall back to text-only with vertex_model_text
            if "404" in str(exc) or "NOT_FOUND" in str(exc):
                logger.warning(
                    "interleaved_model_unavailable_fallback",
                    extra={"model": settings.vertex_model_interleaved, "fallback": self.text_model},
                )
                response = self.genai.models.generate_content(
                    model=self.text_model,
                    contents=instruction,
                    config=genai_types.GenerateContentConfig(
                        response_modalities=["TEXT"],
                    ),
                )
            else:
                raise

        parts: list[dict] = []
        raw_text_accumulator = ""
        metadata: dict = {}

        candidates = getattr(response, "candidates", None) or []
        response_parts = []
        if candidates:
            content = getattr(candidates[0], "content", None)
            response_parts = getattr(content, "parts", None) or []

        for rp in response_parts:
            text = getattr(rp, "text", None)
            inline_data = getattr(rp, "inline_data", None)

            if text:
                raw_text_accumulator += text
                # Detect the trailing JSON metadata block
                stripped = text.strip()
                if stripped.startswith("{") and "narration" in stripped:
                    try:
                        metadata = json.loads(stripped)
                        continue  # don't add metadata JSON as a visible content part
                    except json.JSONDecodeError:
                        pass
                if stripped:
                    parts.append({"type": "text", "content": stripped})

            elif inline_data:
                mime = getattr(inline_data, "mime_type", None) or "image/png"
                raw = getattr(inline_data, "data", None)
                if raw:
                    try:
                        img_bytes = base64.b64decode(raw) if isinstance(raw, str) else bytes(raw)
                        uploaded = self.gcs.upload_bytes_and_sign(
                            data=img_bytes,
                            prefix="interleaved",
                            content_type=mime,
                        )
                        parts.append({
                            "type": "image",
                            "gcs_uri": uploaded.gcs_uri,
                            "signed_url": uploaded.signed_url,
                        })
                    except Exception as exc:
                        logger.warning("inline_image_upload_failed", extra={"error": str(exc)})

        # Fallback: if the model returned only text (no inline images), extract metadata
        # from the accumulated text and synthesise a minimal parts list
        if not metadata and raw_text_accumulator:
            acc = raw_text_accumulator.strip()
            # Try to extract trailing JSON
            brace_idx = acc.rfind("{")
            if brace_idx != -1:
                try:
                    metadata = json.loads(acc[brace_idx:])
                    # Remove metadata JSON from visible parts
                    parts = [p for p in parts if not (p["type"] == "text" and p["content"].strip().startswith("{"))]
                except json.JSONDecodeError:
                    pass

        title = metadata.get("title") or f"{session_type.title()} — {prompt[:60]}"
        narration = metadata.get("narration") or raw_text_accumulator[:2000]
        video_prompt = metadata.get("video_prompt") or f"Cinematic visual explainer about {prompt}"
        quiz = metadata.get("quiz") or {
            "id": "q1",
            "question": "What is the key concept covered?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": "B",
        }

        # If no parts were produced at all (model returned nothing), fall back to plain text
        if not parts:
            parts = [{"type": "text", "content": narration}]

        return {
            "parts": parts,
            "title": title,
            "narration": narration,
            "video_prompt": video_prompt,
            "quiz": quiz,
        }

    def generate_lesson_plan(self, prompt: str, session_type: str) -> dict:
        self._init_clients()
        instruction = (
            "Return strict JSON only with keys: title, narration, sections, image_prompt, video_prompt, quiz. "
            "quiz must include id, question, options (array), correct. "
            f"Build a {session_type} learning experience for prompt: {prompt}"
        )
        set_stage("inference")

        def _call(model_name: str) -> dict:
            response = self.genai.models.generate_content(
                model=model_name,
                contents=instruction,
                config=genai_types.GenerateContentConfig(response_mime_type="application/json"),
            )
            text = getattr(response, "text", "") or ""
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

        def _run_with_model(model_name: str) -> dict:
            return retry_sync(
                lambda: _call(model_name),
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

    def _extract_image_from_response(self, response: object) -> object | None:
        parts = getattr(response, "parts", None)
        if not parts:
            candidates = getattr(response, "candidates", None)
            if candidates:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None) if content else None
        if not parts:
            return None
        for part in parts:
            if getattr(part, "inline_data", None):
                try:
                    return part.as_image()
                except Exception:
                    return None
        return None

    def generate_image(self, image_prompt: str) -> dict:
        self._init_clients()
        set_stage("rendering")

        def _call_generate(model_name: str) -> dict:
            response = self.genai.models.generate_images(
                model=model_name,
                prompt=image_prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_gcs_uri=f"gs://{settings.gcs_media_bucket}/images",
                ),
            )
            generated = getattr(response, "generated_images", None)
            if not generated:
                raise MediaGenerationError("Image generation returned no images")
            gcs_uri = getattr(generated[0].image, "gcs_uri", None)
            if not gcs_uri:
                raise MediaGenerationError("Image response missing GCS URI")
            signed_url = self.gcs.sign_gcs_uri(gcs_uri)
            return {"gcs_uri": gcs_uri, "signed_url": signed_url, "caption": image_prompt}

        try:
            return _call_generate(self.image_model)
        except StorageError:
            raise
        except Exception as exc:
            if self.image_model_backup is not None:
                logger.warning("primary_image_model_failed_fallback", extra={"error": str(exc)})
                return _call_generate(self.image_model_backup)
            if _is_gpu_error(exc):
                raise MediaGenerationError("GPU memory exhausted during image generation", stage="rendering") from exc
            raise MediaGenerationError(str(exc)) from exc

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

    def _aspect_ratio(self, resolution: str) -> str:
        width, _, height = resolution.partition("x")
        try:
            w = int(width)
            h = int(height)
        except ValueError:
            return "16:9"
        if w == 0 or h == 0:
            return "16:9"
        return "16:9" if w >= h else "9:16"

    def _generate_single_video_clip(self, *, video_prompt: str, resolution: str) -> dict:
        import time

        if not settings.gcs_media_bucket:
            raise MediaGenerationError("GCS_MEDIA_BUCKET is required for video output")

        config = genai_types.GenerateVideosConfig(
            number_of_videos=1,
            duration_seconds=8,
            aspect_ratio=self._aspect_ratio(resolution),
            output_gcs_uri=f"gs://{settings.gcs_media_bucket}/videos",
        )
        operation = self.genai.models.generate_videos(
            model=settings.vertex_model_video,
            prompt=video_prompt,
            config=config,
        )
        while not operation.done:
            time.sleep(10)
            operation = self.genai.operations.get(operation)

        op_error = getattr(operation, "error", None)
        if op_error:
            raise MediaGenerationError(f"Veo operation failed: {op_error}")

        result = getattr(operation, "result", None)
        generated = getattr(result, "generated_videos", None) if result else None
        if not generated:
            raise MediaGenerationError(
                f"GenAI video generation returned no videos (operation={operation!r})"
            )

        video = generated[0].video
        gcs_uri = getattr(video, "uri", None) or getattr(video, "gcs_uri", None)
        if not gcs_uri:
            raise MediaGenerationError("Veo video response missing URI")
        signed_url = self.gcs.sign_gcs_uri(gcs_uri)
        return {"gcs_uri": gcs_uri, "signed_url": signed_url}

    def _generate_video_genai(self, *, video_prompt: str, options: VideoOptions) -> dict:
        import math
        import concurrent.futures

        # Use 8-second clips (Veo max); determine how many clips for desired total duration
        clip_duration = 8
        desired_total = max(options.duration_seconds, clip_duration)
        num_clips = math.ceil(desired_total / clip_duration)

        if num_clips == 1:
            result = self._generate_single_video_clip(
                video_prompt=video_prompt,
                resolution=options.resolution,
            )
            return {**result, "clips": [result]}

        # Vary each clip prompt slightly for a coherent sequence
        continuation_prefixes = [
            "",
            "Continuing: ",
            "Further exploration of ",
            "Final segment of ",
            "Conclusion showing ",
        ]

        def _gen_clip(index: int) -> dict:
            prefix = continuation_prefixes[index % len(continuation_prefixes)]
            prompt = f"{prefix}{video_prompt}" if prefix else video_prompt
            return self._generate_single_video_clip(
                video_prompt=prompt,
                resolution=options.resolution,
            )

        logger.info("video_clip_chain_start", extra={"num_clips": num_clips, "total_seconds": num_clips * clip_duration})
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_clips) as executor:
            futures = [executor.submit(_gen_clip, i) for i in range(num_clips)]
            clips = [f.result() for f in futures]

        return {
            "clips": clips,
            "signed_url": clips[0]["signed_url"],
            "gcs_uri": clips[0]["gcs_uri"],
        }

    def _generate_video_sync(self, *, video_prompt: str, options: VideoOptions) -> dict:
        endpoint = settings.videofx_endpoint
        if endpoint:
            try:
                return self._videofx_request(endpoint=str(endpoint), video_prompt=video_prompt, options=options)
            except Exception as exc:
                fallback_endpoint = settings.videofx_fallback_endpoint
                if fallback_endpoint:
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
                logger.warning("videofx_primary_failed_genai_fallback", extra={"error": str(exc)})
                return self._generate_video_genai(video_prompt=video_prompt, options=options)

        return self._generate_video_genai(video_prompt=video_prompt, options=options)

    async def generate_video(self, *, video_prompt: str, options: VideoOptions | None = None) -> dict:
        self._init_clients()
        set_stage("inference")
        resolved_options = options or VideoOptions()
        return await asyncio.to_thread(self._generate_video_sync, video_prompt=video_prompt, options=resolved_options)


engine = GenAIMultimodalEngine()
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
        logger.info("pipeline_started", extra={"session_type": session_type, "request_id": request_id or ""})

        # ── Step 1: Single Gemini interleaved call ────────────────────────────
        # One model invocation produces the full narrative: text paragraphs and
        # inline diagrams woven together, plus narration / video_prompt / quiz.
        yield _sse("status", session_type, {"message": "Weaving text and visuals with Gemini…"})

        async def _run_interleaved():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(
                        engine.generate_interleaved_content,
                        prompt=validated_prompt,
                        session_type=session_type,
                    ),
                    timeout=settings.model_inference_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise TimeoutError("Interleaved generation timed out", stage="inference") from exc

        interleaved = await retry_async(
            _run_interleaved,
            attempts=settings.retry_max_attempts,
            base_delay=settings.retry_base_delay_seconds,
            max_delay=settings.retry_max_delay_seconds,
            stage="inference",
            retry_on=(TimeoutError, ModelInferenceError, AIIntegrationError),
        )

        title = interleaved["title"]
        narration = interleaved["narration"]
        video_prompt_text = interleaved["video_prompt"]
        quiz_payload = interleaved["quiz"]

        # ── Step 2: Stream interleaved parts as they were produced ────────────
        # Each part is either {"type":"text","content":"..."} or
        # {"type":"image","signed_url":"...","gcs_uri":"..."}.
        # Streaming them in order gives the "creative director" interleaved flow.
        image_payload = None
        text_payload = {"title": title, "content": narration, "sections": []}

        yield _sse("text", session_type, text_payload)

        for part in interleaved["parts"]:
            if part["type"] == "text":
                yield _sse("narration", session_type, {"content": part["content"]})
            elif part["type"] == "image":
                img_evt = {"signed_url": part["signed_url"], "gcs_uri": part["gcs_uri"], "caption": ""}
                if image_payload is None:
                    image_payload = img_evt  # keep first image for cache
                yield _sse("image", session_type, img_evt)
            await asyncio.sleep(0.04)

        # ── Step 3: Launch Veo video concurrently while TTS runs ─────────────
        logger.info("pipeline_stage", extra={"stage": "video", "session_type": session_type, "request_id": request_id or ""})
        yield _sse("status", session_type, {"message": "Generating Veo video…"})

        video_task = asyncio.create_task(
            engine.generate_video(video_prompt=video_prompt_text, options=options)
        )

        # ── Step 4: TTS narration audio ──────────────────────────────────────
        logger.info("pipeline_stage", extra={"stage": "audio", "session_type": session_type, "request_id": request_id or ""})
        yield _sse("status", session_type, {"message": "Generating narration audio…"})

        audio_payload = None
        try:
            async def _run_audio():
                try:
                    return await asyncio.wait_for(
                        asyncio.to_thread(engine.synthesize_audio, narration),
                        timeout=settings.media_generation_timeout_seconds,
                    )
                except asyncio.TimeoutError as exc:
                    raise TimeoutError("Audio generation timed out", stage="rendering") from exc

            audio_payload = await retry_async(
                _run_audio,
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="rendering",
                retry_on=(TimeoutError, MediaGenerationError, StorageError),
            )
            yield _sse("audio", session_type, audio_payload)
        except Exception as audio_exc:
            logger.warning("audio_generation_skipped", extra={"reason": str(audio_exc)})

        # ── Step 5: Await video result ────────────────────────────────────────
        video_payload = None
        try:
            video_payload = await video_task
            yield _sse("video", session_type, video_payload)
        except Exception as video_exc:
            logger.warning("video_generation_skipped", extra={"reason": str(video_exc)})

        # ── Step 6: Quiz ──────────────────────────────────────────────────────
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
