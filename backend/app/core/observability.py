from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("observability")
_tracer = None
_meter = None


def get_tracer():
    return _tracer


def get_meter():
    return _meter


def configure_observability() -> None:
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.env,
                traces_sample_rate=settings.sentry_traces_sample_rate,
                send_default_pii=False,
            )
            logger.info("sentry_initialized")
        except Exception as exc:
            logger.warning("sentry_init_failed", extra={"error": str(exc)})

    if settings.otel_endpoint:
        try:
            from opentelemetry import metrics, trace
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

            resource = Resource.create({"service.name": settings.otel_service_name})
            tracer_provider = TracerProvider(
                resource=resource,
                sampler=TraceIdRatioBased(settings.otel_traces_sample_rate),
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_endpoint)))
            trace.set_tracer_provider(tracer_provider)

            metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=settings.otel_endpoint))
            metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

            global _tracer, _meter
            _tracer = trace.get_tracer(settings.otel_service_name)
            _meter = metrics.get_meter(settings.otel_service_name)
            logger.info("otel_initialized", extra={"endpoint": settings.otel_endpoint})
        except Exception as exc:
            logger.warning("otel_init_failed", extra={"error": str(exc)})


def instrument_app(app) -> None:
    if not settings.otel_endpoint:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        AsyncPGInstrumentor().instrument()
        RedisInstrumentor().instrument()
        logger.info("otel_instrumentation_enabled")
    except Exception as exc:
        logger.warning("otel_instrumentation_failed", extra={"error": str(exc)})
