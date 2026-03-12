from __future__ import annotations

import logging

from app.core.config import settings
from app.core.observability import get_meter

logger = logging.getLogger("metrics")
_failure_counter = None
_success_counter = None
_stage_duration = None
_prom_failure_counter = None
_prom_success_counter = None
_prom_stage_duration = None


def _ensure_metrics():
    global _failure_counter, _success_counter, _stage_duration
    global _prom_failure_counter, _prom_success_counter, _prom_stage_duration
    if _failure_counter or _success_counter or _stage_duration:
        return
    meter = get_meter()
    if meter is not None:
        _failure_counter = meter.create_counter(
            "pipeline_failures",
            description="Count of pipeline failures by stage and error type",
        )
        _success_counter = meter.create_counter(
            "pipeline_success",
            description="Count of pipeline successes by stage",
        )
        _stage_duration = meter.create_histogram(
            "pipeline_stage_duration_ms",
            description="Duration of pipeline stages in ms",
            unit="ms",
        )

    if settings.prometheus_enabled:
        try:
            from prometheus_client import Counter, Histogram

            _prom_failure_counter = Counter(
                "pipeline_failures",
                "Count of pipeline failures by stage and error type",
                ["stage", "error_type"],
            )
            _prom_success_counter = Counter(
                "pipeline_success",
                "Count of pipeline successes by stage",
                ["stage"],
            )
            _prom_stage_duration = Histogram(
                "pipeline_stage_duration_ms",
                "Duration of pipeline stages in ms",
                ["stage"],
                unit="ms",
            )
        except Exception as exc:
            logger.warning("prometheus_metrics_init_failed", extra={"error": str(exc)})


def emit_failure_metric(*, stage: str, error_type: str) -> None:
    _ensure_metrics()
    if _failure_counter:
        _failure_counter.add(1, {"stage": stage, "error_type": error_type})
    if _prom_failure_counter:
        _prom_failure_counter.labels(stage=stage, error_type=error_type).inc()
    logger.info("pipeline_failure", extra={"stage": stage, "error_type": error_type})


def emit_success_metric(*, stage: str, duration_ms: int | None = None) -> None:
    _ensure_metrics()
    if _success_counter:
        _success_counter.add(1, {"stage": stage})
    if _stage_duration and duration_ms is not None:
        _stage_duration.record(duration_ms, {"stage": stage})
    if _prom_success_counter:
        _prom_success_counter.labels(stage=stage).inc()
    if _prom_stage_duration and duration_ms is not None:
        _prom_stage_duration.labels(stage=stage).observe(duration_ms)
    logger.info("pipeline_success", extra={"stage": stage, "duration_ms": duration_ms})
