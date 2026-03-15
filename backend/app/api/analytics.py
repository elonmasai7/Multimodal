from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud_progress import lesson_performance, list_student_progress, my_quiz_performance, quiz_performance
from app.db.session import get_db_session
from app.deps.auth import AuthUser, get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/student-progress")
async def analytics_student_progress(
    user_id: str | None = None,
    limit: int = 100,
    _: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    rows = await list_student_progress(db, user_id=user_id, limit=limit)
    return {
        "status": "ok",
        "data": [
            {
                "user_id": row.user_id,
                "lesson_id": row.lesson_id,
                "score": row.score,
                "completion": row.completion,
                "time_spent_seconds": row.time_spent_seconds,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ],
    }


@router.get("/lesson-performance")
async def analytics_lesson_performance(
    limit: int = 100,
    _: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    rows = await lesson_performance(db, limit=limit)
    return {"status": "ok", "data": rows}


@router.get("/my-quiz-performance")
async def analytics_my_quiz_performance(
    limit: int = 100,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    rows = await my_quiz_performance(db, user_id=user.uid, limit=limit)
    return {"status": "ok", "data": rows}


@router.get("/quiz-performance")
async def analytics_quiz_performance(
    limit: int = 100,
    _: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    rows = await quiz_performance(db, limit=limit)
    return {"status": "ok", "data": rows}
