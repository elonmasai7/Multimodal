import json

from redis.asyncio import Redis

from app.core.config import settings


class RedisStateManager:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        await self.redis.close()

    async def init_story_state(self, *, session_id: str) -> None:
        key = f"story:{session_id}"
        await self.redis.hset(key, mapping={"current_scene": "scene_01", "history": "[]"})
        await self.redis.expire(key, 86400)

    async def get_story_state(self, *, session_id: str) -> dict | None:
        key = f"story:{session_id}"
        data = await self.redis.hgetall(key)
        if not data:
            return None
        return {
            "current_scene": data.get("current_scene", "scene_01"),
            "history": json.loads(data.get("history", "[]")),
        }

    async def append_story_choice(self, *, session_id: str, scene_id: str, choice_text: str, next_scene: str) -> None:
        key = f"story:{session_id}"
        current = await self.get_story_state(session_id=session_id)
        history = (current or {}).get("history", [])
        history.append({"scene_id": scene_id, "choice_text": choice_text})
        await self.redis.hset(key, mapping={"current_scene": next_scene, "history": json.dumps(history)})
        await self.redis.expire(key, 86400)

    async def upsert_lesson_quiz_state(self, *, lesson_id: str, question_id: str, answer: str, correct: bool) -> None:
        key = f"lesson:{lesson_id}:quiz"
        entry = {"question_id": question_id, "answer": answer, "correct": correct}
        await self.redis.rpush(key, json.dumps(entry))
        await self.redis.expire(key, 86400)

    async def quiz_attempt_count(self, *, lesson_id: str) -> int:
        key = f"lesson:{lesson_id}:quiz"
        return int(await self.redis.llen(key))

    async def set_quiz_key(self, *, lesson_id: str, question_id: str, correct: str) -> None:
        key = f"lesson:{lesson_id}:quiz-keys"
        await self.redis.hset(key, mapping={question_id: correct})
        await self.redis.expire(key, 86400)

    async def get_quiz_key(self, *, lesson_id: str, question_id: str) -> str | None:
        key = f"lesson:{lesson_id}:quiz-keys"
        value = await self.redis.hget(key, question_id)
        return str(value) if value is not None else None

    async def get_ai_cache(self, *, key: str) -> dict | None:
        data = await self.redis.get(f"ai-cache:{key}")
        return json.loads(data) if data else None

    async def set_ai_cache(self, *, key: str, payload: dict, ttl_seconds: int = 3600) -> None:
        await self.redis.set(f"ai-cache:{key}", json.dumps(payload), ex=ttl_seconds)
