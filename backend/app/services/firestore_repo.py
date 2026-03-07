from datetime import UTC, datetime

from google.cloud.firestore_v1 import AsyncClient

from app.core.config import settings


def firestore_client() -> AsyncClient:
    if settings.gcp_project_id:
        return AsyncClient(project=settings.gcp_project_id)
    return AsyncClient()


class FirestoreRepository:
    def __init__(self) -> None:
        self.client: AsyncClient | None = None
        self.story_sessions: dict[str, dict] = {}
        self.lesson_sessions: dict[str, dict] = {}

    def _enabled(self) -> bool:
        return settings.firestore_enabled

    def _ensure_client(self) -> AsyncClient | None:
        if not self._enabled():
            return None
        if self.client is None:
            try:
                self.client = firestore_client()
            except Exception:
                self.client = None
        return self.client

    async def create_story_session(self, *, user_id: str, session_id: str, prompt: str, duration: int) -> None:
        payload = {
            "user_id": user_id,
            "prompt": prompt,
            "duration": duration,
            "current_scene": "scene_01",
            "history": [],
            "media_assets": [],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        client = self._ensure_client()
        if client is None:
            self.story_sessions[session_id] = payload
            return

        doc = client.collection("story_sessions").document(session_id)
        await doc.set(payload)

    async def get_story_session(self, *, session_id: str) -> dict | None:
        client = self._ensure_client()
        if client is None:
            return self.story_sessions.get(session_id)

        snap = await client.collection("story_sessions").document(session_id).get()
        if not snap.exists:
            return None
        return snap.to_dict()

    async def append_story_choice(self, *, session_id: str, scene_id: str, choice_text: str, next_scene: str) -> None:
        client = self._ensure_client()
        if client is None:
            payload = self.story_sessions.get(session_id)
            if payload is None:
                return
            history = payload.get("history", [])
            history.append({"scene_id": scene_id, "choice_text": choice_text, "timestamp": datetime.now(UTC).isoformat()})
            payload["history"] = history
            payload["current_scene"] = next_scene
            payload["updated_at"] = datetime.now(UTC)
            return

        doc = client.collection("story_sessions").document(session_id)
        snap = await doc.get()
        if not snap.exists:
            return

        payload = snap.to_dict() or {}
        history = payload.get("history", [])
        history.append({"scene_id": scene_id, "choice_text": choice_text, "timestamp": datetime.now(UTC).isoformat()})
        await doc.update({"history": history, "current_scene": next_scene, "updated_at": datetime.now(UTC)})

    async def create_lesson_session(self, *, user_id: str, lesson_id: str, prompt: str, duration: int) -> None:
        payload = {
            "user_id": user_id,
            "prompt": prompt,
            "duration": duration,
            "quiz_attempts": [],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        client = self._ensure_client()
        if client is None:
            self.lesson_sessions[lesson_id] = payload
            return

        doc = client.collection("lesson_sessions").document(lesson_id)
        await doc.set(payload)

    async def get_lesson_session(self, *, lesson_id: str) -> dict | None:
        client = self._ensure_client()
        if client is None:
            return self.lesson_sessions.get(lesson_id)

        snap = await client.collection("lesson_sessions").document(lesson_id).get()
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
        client = self._ensure_client()
        if client is None:
            payload = self.lesson_sessions.get(lesson_id)
            if payload is None:
                return
            attempts = payload.get("quiz_attempts", [])
            attempts.append(
                {
                    "question_id": question_id,
                    "answer": answer,
                    "correct": correct,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            payload["quiz_attempts"] = attempts
            payload["updated_at"] = datetime.now(UTC)
            return

        doc = client.collection("lesson_sessions").document(lesson_id)
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
