from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger("observability")
_tracer = None
_meter = None
_sqlalchemy_attrs_registered = False


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


def _redact_sql_params(parameters):
    if parameters is None:
        return None
    if isinstance(parameters, (list, tuple)):
        return ["***" for _ in parameters]
    if isinstance(parameters, dict):
        return {key: "***" for key in parameters}
    return "***"


def _should_record_sql(statement: str) -> bool:
    normalized = statement.strip().lower()
    return normalized.startswith("select") or normalized.startswith("with")


def _register_sqlalchemy_span_attributes(engine) -> None:
    global _sqlalchemy_attrs_registered
    if _sqlalchemy_attrs_registered:
        return
    try:
        from opentelemetry import trace
        from sqlalchemy import event
    except Exception:
        return

    @event.listens_for(engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        span = trace.get_current_span()
        if not span or not span.is_recording():
            return
        if _should_record_sql(statement):
            span.set_attribute("db.statement", statement)
        else:
            span.set_attribute("db.statement", "<redacted>")
        redacted = _redact_sql_params(parameters)
        if redacted is not None:
            try:
                span.set_attribute("db.statement.parameters", json.dumps(redacted, ensure_ascii=True))
            except Exception:
                pass

    _sqlalchemy_attrs_registered = True


def instrument_app(app) -> None:
    if not settings.otel_endpoint:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        AsyncPGInstrumentor().instrument()
        RedisInstrumentor().instrument()
        try:
            from app.db.session import engine

            SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
            _register_sqlalchemy_span_attributes(engine.sync_engine)
        except Exception as exc:
            logger.warning("otel_sqlalchemy_instrumentation_failed", extra={"error": str(exc)})
        logger.info("otel_instrumentation_enabled")
    except Exception as exc:
        logger.warning("otel_instrumentation_failed", extra={"error": str(exc)})
