from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StudentProgress


async def upsert_progress(
    db: AsyncSession,
    *,
    user_id: str,
    lesson_id: str,
    score: float,
    completion: float,
    time_spent_seconds: int,
) -> StudentProgress:
    result = await db.execute(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.lesson_id == lesson_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = StudentProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            score=score,
            completion=completion,
            time_spent_seconds=time_spent_seconds,
        )
        db.add(row)
    else:
        row.score = score
        row.completion = completion
        row.time_spent_seconds = time_spent_seconds

    await db.commit()
    await db.refresh(row)
    return row


async def get_progress(db: AsyncSession, *, user_id: str, lesson_id: str) -> StudentProgress | None:
    result = await db.execute(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.lesson_id == lesson_id,
        )
    )
    return result.scalar_one_or_none()
