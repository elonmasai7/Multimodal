import asyncio
import hashlib
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.core.errors import AIIntegrationError, MediaGenerationError
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


class VertexMultimodalEngine:
    def __init__(self) -> None:
        self._ready = False
        self.gcs: GCSMediaService | None = None

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
        response = self.text_model.generate_content(instruction)
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

    def generate_image(self, image_prompt: str) -> dict:
        self._init_clients()
        images = self.image_model.generate_images(prompt=image_prompt, number_of_images=1)
        image = images[0]
        filename = f"/tmp/{uuid.uuid4()}.png"
        image.save(location=filename)

        uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="images", content_type="image/png")
        return {
            "gcs_uri": uploaded.gcs_uri,
            "signed_url": uploaded.signed_url,
            "caption": image_prompt,
        }

    def synthesize_audio(self, text: str) -> dict:
        self._init_clients()
        if not self.tts_client:
            raise MediaGenerationError("Google Text-to-Speech client unavailable")

        synthesis_input = texttospeech.SynthesisInput(text=text[:5000])
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Neural2-C")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        filename = f"/tmp/{uuid.uuid4()}.mp3"
        with open(filename, "wb") as f:
            f.write(response.audio_content)

        uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="audio", content_type="audio/mpeg")
        return {
            "gcs_uri": uploaded.gcs_uri,
            "signed_url": uploaded.signed_url,
        }

    def _generate_video_sync(self, *, video_prompt: str) -> dict:
        import time
        from google import genai as google_genai
        from google.genai import types as genai_types

        client = google_genai.Client(project=settings.gcp_project_id, location=settings.gcp_region)
        source = genai_types.GenerateVideosSource(prompt=video_prompt)
        config = genai_types.GenerateVideosConfig(
            aspect_ratio="16:9",
            number_of_videos=1,
            duration_seconds=8,
            person_generation="allow_all",
            generate_audio=False,
            resolution="720p",
            output_gcs_uri=f"gs://{settings.gcs_media_bucket}/videos",
        )
        operation = client.models.generate_videos(model="veo-3.1-generate-001", source=source, config=config)
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)

        response = operation.result
        if not response or not response.generated_videos:
            raise MediaGenerationError("Veo returned no videos")

        video = response.generated_videos[0].video
        gcs_uri = video.uri
        signed_url = self.gcs.sign_gcs_uri(gcs_uri)
        return {"gcs_uri": gcs_uri, "signed_url": signed_url}

    async def generate_video(self, *, video_prompt: str) -> dict:
        self._init_clients()
        return await asyncio.to_thread(self._generate_video_sync, video_prompt=video_prompt)


engine = VertexMultimodalEngine()
redis_state = RedisStateManager()


def _cache_key(prompt: str, session_type: str) -> str:
    return hashlib.sha256(f"{session_type}:{prompt}".encode()).hexdigest()


async def stream_multimodal_events(prompt: str, session_type: str) -> AsyncGenerator[str, None]:
    key = _cache_key(prompt, session_type)
    cached = await redis_state.get_ai_cache(key=key)
    if cached:
        yield _sse("status", session_type, {"message": "Loaded cached generation"})
        for event_name in ["text", "image", "video", "audio", "quiz"]:
            if event_name in cached:
                yield _sse(event_name, session_type, cached[event_name])
        yield _sse("done", session_type, {"status": "completed", "cached": True})
        return

    start = datetime.now(UTC)
    try:
        yield _sse("status", session_type, {"message": "Generating structured lesson plan with Gemini"})
        plan = await asyncio.to_thread(engine.generate_lesson_plan, prompt, session_type)

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
        image_payload = await asyncio.to_thread(engine.generate_image, str(plan.get("image_prompt", prompt)))
        yield _sse("image", session_type, image_payload)

        yield _sse("status", session_type, {"message": "Generating video with VideoFX"})
        try:
            video_payload = await engine.generate_video(video_prompt=str(plan.get("video_prompt", prompt)))
            yield _sse("video", session_type, video_payload)
        except Exception as video_exc:
            logger.warning("video_generation_skipped reason=%s", video_exc)
            video_payload = None

        yield _sse("status", session_type, {"message": "Generating narration audio"})
        audio_payload = await asyncio.to_thread(engine.synthesize_audio, narration)
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
        logger.info("generation_complete session_type=%s elapsed_ms=%s", session_type, elapsed_ms)
        yield _sse("done", session_type, {"status": "completed", "elapsed_ms": elapsed_ms})
    except Exception as exc:
        logger.exception("generation_failed session_type=%s", session_type)
        yield _sse("error", session_type, {"message": str(exc)})
        yield _sse("done", session_type, {"status": "failed"})
