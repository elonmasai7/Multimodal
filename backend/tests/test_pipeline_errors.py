import asyncio
import json
import unittest
from unittest.mock import patch

from app.core.errors import EncodingError, StorageError, TimeoutError
from app.models.schemas import VideoOptions
from app.services import ai_orchestrator
from app.services.ai_orchestrator import stream_multimodal_events


def _collect_sse(prompt: str, session_type: str) -> list[str]:
    async def _run() -> list[str]:
        chunks: list[str] = []
        async for chunk in stream_multimodal_events(
            prompt=prompt,
            session_type=session_type,
            video_options=VideoOptions(),
            request_id="test-request",
        ):
            chunks.append(chunk)
            if "event: done\n" in chunk:
                break
        return chunks

    return asyncio.run(_run())


def _extract_error_payload(chunks: list[str]) -> dict:
    for chunk in chunks:
        if chunk.startswith("event: error"):
            for line in chunk.splitlines():
                if line.startswith("data: "):
                    return json.loads(line.replace("data: ", ""))
    raise AssertionError("No error event found")


class PipelineErrorTests(unittest.TestCase):
    def test_model_timeout(self) -> None:
        with patch.object(ai_orchestrator.engine, "generate_lesson_plan", side_effect=TimeoutError("model timeout")):
            chunks = _collect_sse("test prompt", "lesson")
        payload = _extract_error_payload(chunks)
        error = payload["error"]
        self.assertEqual(error["type"], "TimeoutError")
        self.assertEqual(error["stage"], "inference")

    def test_storage_failure(self) -> None:
        with patch.object(ai_orchestrator.engine, "generate_lesson_plan", return_value={"narration": "test"}):
            with patch.object(ai_orchestrator.engine, "generate_image", side_effect=StorageError("upload failed")):
                chunks = _collect_sse("test prompt", "story")
        payload = _extract_error_payload(chunks)
        error = payload["error"]
        self.assertEqual(error["type"], "StorageError")
        self.assertEqual(error["stage"], "storage")

    def test_encoding_failure(self) -> None:
        async def _raise_encoding(*args, **kwargs):
            raise EncodingError("corrupted frames")

        with patch.object(ai_orchestrator.engine, "generate_lesson_plan", return_value={"narration": "test"}):
            with patch.object(ai_orchestrator.engine, "generate_image", return_value={"signed_url": "image"}):
                with patch.object(ai_orchestrator.engine, "synthesize_audio", return_value={"signed_url": "audio"}):
                    with patch.object(ai_orchestrator.engine, "generate_video", side_effect=_raise_encoding):
                        chunks = _collect_sse("test prompt", "lesson")
        payload = _extract_error_payload(chunks)
        error = payload["error"]
        self.assertEqual(error["type"], "EncodingError")
        self.assertEqual(error["stage"], "encoding")
