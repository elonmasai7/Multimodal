from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_stage_var: ContextVar[str | None] = ContextVar("pipeline_stage", default=None)
_route_var: ContextVar[str | None] = ContextVar("route_name", default=None)


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_request_id(value: str | None) -> None:
    _request_id_var.set(value)


def set_stage(value: str | None) -> None:
    _stage_var.set(value)


def set_route_name(value: str | None) -> None:
    _route_var.set(value)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id:
            payload["request_id"] = request_id

        stage = getattr(record, "stage", None) or _stage_var.get()
        if stage:
            payload["stage"] = stage

        route_name = getattr(record, "route_name", None) or _route_var.get()
        if route_name:
            payload["route_name"] = route_name

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }
        }
        for key, value in extra_fields.items():
            if key not in payload and value is not None:
                payload[key] = value

        if record.exc_info and "trace" not in payload:
            payload["trace"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root.handlers = [handler]


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        request.state.request_id = request_id
        set_route_name(getattr(getattr(request, "scope", {}).get("route", None), "name", None))
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            logging.getLogger("api.request").info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            set_request_id(None)
            set_route_name(None)
