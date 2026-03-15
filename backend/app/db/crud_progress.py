from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LessonQuizAttempt, StudentProgress


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


async def create_quiz_attempt(
    db: AsyncSession,
    *,
    user_id: str,
    lesson_id: str,
    question_id: str,
    answer: str,
    correct: bool,
    time_spent_seconds: int,
) -> LessonQuizAttempt:
    row = LessonQuizAttempt(
        user_id=user_id,
        lesson_id=lesson_id,
        question_id=question_id,
        answer=answer,
        correct=correct,
        time_spent_seconds=time_spent_seconds,
    )
    db.add(row)
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


async def list_student_progress(db: AsyncSession, *, user_id: str | None = None, limit: int = 100) -> list[StudentProgress]:
    stmt = select(StudentProgress).order_by(desc(StudentProgress.updated_at)).limit(limit)
    if user_id:
        stmt = stmt.where(StudentProgress.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_watch_time(
    db: AsyncSession,
    *,
    user_id: str,
    lesson_id: str,
    watched_seconds: int,
    duration_seconds: int,
) -> StudentProgress:
    result = await db.execute(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.lesson_id == lesson_id,
        )
    )
    row = result.scalar_one_or_none()
    watch_completion = min(1.0, watched_seconds / duration_seconds) if duration_seconds > 0 else 0.0
    if row is None:
        row = StudentProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            score=0,
            completion=watch_completion,
            time_spent_seconds=watched_seconds,
        )
        db.add(row)
    else:
        # Keep the higher completion value (quiz-based vs watch-based)
        row.completion = max(float(row.completion or 0), watch_completion)
        row.time_spent_seconds = max(int(row.time_spent_seconds or 0), watched_seconds)

    await db.commit()
    await db.refresh(row)
    return row


async def my_quiz_performance(db: AsyncSession, *, user_id: str, limit: int = 100) -> list[dict]:
    stmt = (
        select(
            LessonQuizAttempt.lesson_id,
            func.count(LessonQuizAttempt.id).label("total"),
            func.sum(case((LessonQuizAttempt.correct == True, 1), else_=0)).label("correct_count"),
        )
        .where(LessonQuizAttempt.user_id == user_id)
        .group_by(LessonQuizAttempt.lesson_id)
        .order_by(desc(func.count(LessonQuizAttempt.id)))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = []
    for row in result:
        total = int(row.total or 0)
        correct = int(row.correct_count or 0)
        rows.append({
            "lesson_id": row.lesson_id,
            "total_attempts": total,
            "correct_count": correct,
            "correct_rate": round(correct / total, 3) if total > 0 else 0.0,
        })
    return rows


async def quiz_performance(db: AsyncSession, *, limit: int = 100) -> list[dict]:
    stmt = (
        select(
            LessonQuizAttempt.lesson_id,
            func.count(LessonQuizAttempt.id).label("total"),
            func.sum(case((LessonQuizAttempt.correct == True, 1), else_=0)).label("correct_count"),
        )
        .group_by(LessonQuizAttempt.lesson_id)
        .order_by(desc(func.count(LessonQuizAttempt.id)))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = []
    for row in result:
        total = int(row.total or 0)
        correct = int(row.correct_count or 0)
        rows.append({
            "lesson_id": row.lesson_id,
            "total_attempts": total,
            "correct_count": correct,
            "correct_rate": round(correct / total, 3) if total > 0 else 0.0,
        })
    return rows


async def lesson_performance(db: AsyncSession, *, limit: int = 100) -> list[dict]:
    stmt = (
        select(
            StudentProgress.lesson_id,
            func.avg(StudentProgress.score).label("average_score"),
            func.avg(StudentProgress.completion).label("completion_rate"),
            func.count(StudentProgress.id).label("attempts"),
        )
        .group_by(StudentProgress.lesson_id)
        .order_by(desc(func.count(StudentProgress.id)))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = []
    for row in result:
        rows.append(
            {
                "lesson_id": row.lesson_id,
                "average_score": float(row.average_score or 0),
                "completion_rate": float(row.completion_rate or 0),
                "attempts": int(row.attempts or 0),
            }
        )
    return rows
