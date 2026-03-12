from __future__ import annotations

import asyncio
import time
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.logging import set_stage

logger = logging.getLogger("retry")

T = TypeVar("T")


def _backoff_delay(attempt: int, base: float, maximum: float) -> float:
    delay = min(maximum, base * (2**attempt))
    jitter = random.uniform(0.5, 1.5)
    return delay * jitter


def retry_sync(
    func: Callable[[], T],
    *,
    attempts: int,
    base_delay: float,
    max_delay: float,
    stage: str,
    retry_on: tuple[type[Exception], ...],
) -> T:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            set_stage(stage)
            return func()
        except retry_on as exc:
            last_exc = exc
            if attempt >= attempts - 1:
                raise
            delay = _backoff_delay(attempt, base_delay, max_delay)
            logger.warning(
                "retrying_sync",
                extra={"stage": stage, "attempt": attempt + 1, "delay_seconds": round(delay, 2)},
            )
            time.sleep(delay)
    raise last_exc or RuntimeError("retry_sync failed without exception")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    base_delay: float,
    max_delay: float,
    stage: str,
    retry_on: tuple[type[Exception], ...],
) -> T:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            set_stage(stage)
            return await func()
        except retry_on as exc:
            last_exc = exc
            if attempt >= attempts - 1:
                raise
            delay = _backoff_delay(attempt, base_delay, max_delay)
            logger.warning(
                "retrying_async",
                extra={"stage": stage, "attempt": attempt + 1, "delay_seconds": round(delay, 2)},
            )
            await asyncio.sleep(delay)
    raise last_exc or RuntimeError("retry_async failed without exception")
