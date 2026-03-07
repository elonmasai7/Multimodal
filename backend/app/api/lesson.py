from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud_progress import get_progress, upsert_progress
from app.db.session import get_db_session
from app.deps.auth import AuthUser, get_current_user
from app.models.schemas import CreateSessionRequest, QuizSubmitRequest
from app.services.ai_orchestrator import new_session_id, stream_multimodal_events
from app.services.firestore_repo import FirestoreRepository
from app.services.redis_state import RedisStateManager

router = APIRouter(prefix="/lesson", tags=["lesson"])
firestore_repo = FirestoreRepository()
redis_state = RedisStateManager()


@router.post("/create")
async def create_lesson(
    req: CreateSessionRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    if req.session_type != "lesson":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_type must be lesson")

    lesson_id = new_session_id()
    await firestore_repo.create_lesson_session(
        user_id=user.uid,
        lesson_id=lesson_id,
        prompt=req.prompt,
        duration=req.duration,
    )
    await upsert_progress(
        db,
        user_id=user.uid,
        lesson_id=lesson_id,
        score=0,
        completion=0,
        time_spent_seconds=0,
    )

    return {
        "status": "ok",
        "data": {
            "lesson_id": lesson_id,
            "session_type": req.session_type,
            "prompt": req.prompt,
            "duration": req.duration,
        },
    }


@router.get("/stream/{lesson_id}")
async def lesson_stream(
    lesson_id: str,
    prompt: str | None = None,
    user: AuthUser = Depends(get_current_user),
) -> StreamingResponse:
    lesson = await firestore_repo.get_lesson_session(lesson_id=lesson_id)
    if lesson is None or lesson.get("user_id") != user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson session not found")

    stream_prompt = prompt or lesson.get("prompt", "Lesson session")

    async def event_generator():
        async for chunk in stream_multimodal_events(prompt=stream_prompt, session_type="lesson"):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{lesson_id}")
async def get_lesson(lesson_id: str, user: AuthUser = Depends(get_current_user)) -> dict:
    lesson = await firestore_repo.get_lesson_session(lesson_id=lesson_id)
    if lesson is None or lesson.get("user_id") != user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson session not found")

    return {
        "status": "ok",
        "data": {
            "lesson_id": lesson_id,
            "title": "Generated lesson",
            "prompt": lesson.get("prompt"),
            "sections": ["Intro", "Diagram", "Animation", "Quiz"],
        },
    }


@router.post("/quiz")
async def submit_quiz(
    req: QuizSubmitRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    lesson = await firestore_repo.get_lesson_session(lesson_id=req.lesson_id)
    if lesson is None or lesson.get("user_id") != user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson session not found")

    correct = req.answer.strip().upper() == "B"
    await firestore_repo.append_quiz_attempt(
        lesson_id=req.lesson_id,
        question_id=req.question_id,
        answer=req.answer,
        correct=correct,
    )
    await redis_state.upsert_lesson_quiz_state(
        lesson_id=req.lesson_id,
        question_id=req.question_id,
        answer=req.answer,
        correct=correct,
    )

    attempts = await redis_state.quiz_attempt_count(lesson_id=req.lesson_id)
    score = 100.0 if correct else max(0.0, 100.0 - attempts * 10.0)
    completion = min(1.0, attempts / 5.0)
    row = await upsert_progress(
        db,
        user_id=user.uid,
        lesson_id=req.lesson_id,
        score=score,
        completion=completion,
        time_spent_seconds=req.time_spent_seconds,
    )

    return {
        "status": "ok",
        "data": {
            "lesson_id": req.lesson_id,
            "question_id": req.question_id,
            "correct": correct,
            "score": row.score,
            "completion": row.completion,
        },
    }


@router.get("/progress/{lesson_id}")
async def get_lesson_progress(
    lesson_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    row = await get_progress(db, user_id=user.uid, lesson_id=lesson_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found")

    return {
        "status": "ok",
        "data": {
            "lesson_id": lesson_id,
            "score": row.score,
            "completion": row.completion,
            "time_spent_seconds": row.time_spent_seconds,
        },
    }
