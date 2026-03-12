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
_http_requests = None
_http_latency = None
_pipeline_registry = None
_system_registry = None


def get_pipeline_registry():
    _ensure_metrics()
    return _pipeline_registry


def get_system_registry():
    _ensure_metrics()
    return _system_registry


def _ensure_metrics():
    global _failure_counter, _success_counter, _stage_duration
    global _prom_failure_counter, _prom_success_counter, _prom_stage_duration
    global _http_requests, _http_latency
    global _pipeline_registry, _system_registry
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
            from prometheus_client import Counter, GCCollector, Histogram, PlatformCollector, ProcessCollector
            from prometheus_client import CollectorRegistry

            _pipeline_registry = CollectorRegistry()
            _system_registry = CollectorRegistry()
            ProcessCollector(registry=_system_registry)
            PlatformCollector(registry=_system_registry)
            GCCollector(registry=_system_registry)

            _prom_failure_counter = Counter(
                "pipeline_failures",
                "Count of pipeline failures by stage and error type",
                ["stage", "error_type"],
                registry=_pipeline_registry,
            )
            _prom_success_counter = Counter(
                "pipeline_success",
                "Count of pipeline successes by stage",
                ["stage"],
                registry=_pipeline_registry,
            )
            _prom_stage_duration = Histogram(
                "pipeline_stage_duration_ms",
                "Duration of pipeline stages in ms",
                ["stage"],
                unit="ms",
                registry=_pipeline_registry,
            )
            _http_requests = Counter(
                "http_requests_total",
                "HTTP requests by method/path/status",
                ["method", "path", "status"],
                registry=_pipeline_registry,
            )
            _http_latency = Histogram(
                "http_request_duration_ms",
                "HTTP request duration in ms",
                ["method", "path", "status"],
                unit="ms",
                registry=_pipeline_registry,
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


def observe_http_request(*, method: str, path: str, status: int, duration_ms: float) -> None:
    _ensure_metrics()
    if _http_requests:
        _http_requests.labels(method=method, path=path, status=str(status)).inc()
    if _http_latency:
        _http_latency.labels(method=method, path=path, status=str(status)).observe(duration_ms)
