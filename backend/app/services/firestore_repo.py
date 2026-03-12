from datetime import UTC, datetime

from google.cloud.firestore_v1 import AsyncClient

from app.core.errors import ExternalServiceError


class FirestoreRepository:
    def __init__(self, *, project_id: str | None = None) -> None:
        self.client: AsyncClient | None = None
        self._init_error: Exception | None = None
        try:
            self.client = AsyncClient(project=project_id) if project_id else AsyncClient()
        except Exception as exc:
            self._init_error = exc

    def _ensure_ready(self) -> None:
        if self.client is None:
            raise ExternalServiceError("Firestore client is not configured") from self._init_error

    async def create_story_session(self, *, user_id: str, session_id: str, prompt: str, duration: int) -> None:
        self._ensure_ready()
        doc = self.client.collection("story_sessions").document(session_id)
        await doc.set(
            {
                "user_id": user_id,
                "prompt": prompt,
                "duration": duration,
                "current_scene": "scene_01",
                "history": [],
                "media_assets": [],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    async def get_story_session(self, *, session_id: str) -> dict | None:
        self._ensure_ready()
        snap = await self.client.collection("story_sessions").document(session_id).get()
        if not snap.exists:
            return None
        return snap.to_dict()

    async def append_story_choice(self, *, session_id: str, scene_id: str, choice_text: str, next_scene: str) -> None:
        self._ensure_ready()
        doc = self.client.collection("story_sessions").document(session_id)
        snap = await doc.get()
        if not snap.exists:
            return

        payload = snap.to_dict() or {}
        history = payload.get("history", [])
        history.append({"scene_id": scene_id, "choice_text": choice_text, "timestamp": datetime.now(UTC).isoformat()})
        await doc.update({"history": history, "current_scene": next_scene, "updated_at": datetime.now(UTC)})

    async def create_lesson_session(self, *, user_id: str, lesson_id: str, prompt: str, duration: int) -> None:
        self._ensure_ready()
        doc = self.client.collection("lesson_sessions").document(lesson_id)
        await doc.set(
            {
                "user_id": user_id,
                "prompt": prompt,
                "duration": duration,
                "quiz_attempts": [],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    async def get_lesson_session(self, *, lesson_id: str) -> dict | None:
        self._ensure_ready()
        snap = await self.client.collection("lesson_sessions").document(lesson_id).get()
        if not snap.exists:
            return None
        return snap.to_dict()

    async def append_quiz_attempt(
        self,
        *,
        lesson_id: str,
        question_id: str,
        answer: str,
        correct: bool,
    ) -> None:
        self._ensure_ready()
        doc = self.client.collection("lesson_sessions").document(lesson_id)
        snap = await doc.get()
        if not snap.exists:
            return
        payload = snap.to_dict() or {}
        attempts = payload.get("quiz_attempts", [])
        attempts.append(
            {
                "question_id": question_id,
                "answer": answer,
                "correct": correct,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        await doc.update({"quiz_attempts": attempts, "updated_at": datetime.now(UTC)})
