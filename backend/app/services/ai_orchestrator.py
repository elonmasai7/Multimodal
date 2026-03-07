import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from app.core.config import settings
from app.services.gcs_media import GCSMediaService

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
            raise RuntimeError("GCP_PROJECT_ID is required for non-mock AI mode")
        if vertexai is None or GenerativeModel is None or ImageGenerationModel is None:
            raise RuntimeError("Vertex AI SDK not installed correctly")

        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
        self.text_model = GenerativeModel(settings.vertex_model_text)
        self.image_model = ImageGenerationModel.from_pretrained(settings.vertex_model_image)
        self.tts_client = texttospeech.TextToSpeechClient() if texttospeech else None
        self.gcs = GCSMediaService() if settings.gcs_media_bucket else None
        self._ready = True

    def generate_text(self, prompt: str, session_type: str) -> str:
        self._init_clients()
        response = self.text_model.generate_content(
            f"Create a concise {session_type} explanation for: {prompt}. Include clear pedagogy and one quiz question."
        )
        return getattr(response, "text", "") or "Generated educational explanation."

    def generate_image_reference(self, prompt: str) -> dict:
        self._init_clients()
        images = self.image_model.generate_images(prompt=f"Educational diagram for: {prompt}", number_of_images=1)
        image = images[0]
        filename = f"/tmp/{uuid.uuid4()}.png"
        image.save(location=filename)
        payload: dict[str, str] = {"local_path": filename, "caption": "Generated with Imagen"}
        if self.gcs:
            uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="images", content_type="image/png")
            payload.update({"gcs_uri": uploaded.gcs_uri, "signed_url": uploaded.signed_url})
        return payload

    def synthesize_audio(self, text: str) -> dict | None:
        self._init_clients()
        if not self.tts_client:
            return None

        synthesis_input = texttospeech.SynthesisInput(text=text[:5000])
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Neural2-C")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        filename = f"/tmp/{uuid.uuid4()}.mp3"
        with open(filename, "wb") as f:
            f.write(response.audio_content)
        payload: dict[str, str] = {"local_path": filename}
        if self.gcs:
            uploaded = self.gcs.upload_file_and_sign(local_path=filename, prefix="audio", content_type="audio/mpeg")
            payload.update({"gcs_uri": uploaded.gcs_uri, "signed_url": uploaded.signed_url})
        return payload


engine = VertexMultimodalEngine()


async def stream_multimodal_events(prompt: str, session_type: str) -> AsyncGenerator[str, None]:
    if settings.mock_ai:
        script = [
            ("narration", f"Starting {session_type}: {prompt}"),
            ("text", "Learning objective: understand core concepts with examples."),
            ("image", {"url": "https://placehold.co/1024x768/png", "caption": "Generated diagram"}),
            ("video", {"url": "https://example.com/video.mp4", "duration": 8}),
            (
                "quiz",
                {
                    "id": "q1",
                    "question": "What is the key idea from this section?",
                    "options": ["A", "B", "C", "D"],
                    "correct": "B",
                },
            ),
        ]

        for event, data in script:
            yield _sse(event, session_type, data)
            await asyncio.sleep(1)
        yield _sse("done", session_type, {"status": "completed"})
        return

    try:
        yield _sse("status", session_type, {"message": "Generating lesson text with Gemini"})
        text = await asyncio.to_thread(engine.generate_text, prompt, session_type)
        yield _sse("text", session_type, {"content": text})

        yield _sse("status", session_type, {"message": "Generating educational diagram with Imagen"})
        image_payload = await asyncio.to_thread(engine.generate_image_reference, prompt)
        yield _sse("image", session_type, image_payload)

        yield _sse("status", session_type, {"message": "Synthesizing narration audio"})
        audio_payload = await asyncio.to_thread(engine.synthesize_audio, text)
        if audio_payload:
            yield _sse("audio", session_type, audio_payload)

        yield _sse(
            "quiz",
            session_type,
            {
                "id": "q1",
                "question": "What best summarizes this lesson?",
                "options": ["A", "B", "C", "D"],
                "correct": "B",
            },
        )
        yield _sse("done", session_type, {"status": "completed"})
    except Exception as exc:
        yield _sse("error", session_type, {"message": str(exc)})
        yield _sse("done", session_type, {"status": "failed"})
