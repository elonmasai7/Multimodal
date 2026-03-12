from __future__ import annotations

import logging
import asyncio
import traceback
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import AppError, ExternalServiceError, TimeoutError
from app.core.logging import get_request_id
from app.core.metrics import emit_failure_metric

logger = logging.getLogger("api.error")


def _http_exception_to_app_error(exc: HTTPException) -> AppError:
    status_code = exc.status_code or 500
    if 400 <= status_code < 500:
        return AppError(
            message=str(exc.detail),
            stage="validation",
            status_code=status_code,
            error_type="ValidationError",
            safe_message=str(exc.detail),
            retryable=False,
        )
    return ExternalServiceError(str(exc.detail), stage="response")


def _validation_error_to_app_error(exc: RequestValidationError) -> AppError:
    return AppError(
        message="Validation failed",
        stage="validation",
        status_code=422,
        error_type="ValidationError",
        safe_message="Validation failed",
        details={"errors": exc.errors()},
        retryable=False,
    )


def normalize_exception(exc: Exception) -> AppError:
    if isinstance(exc, AppError):
        return exc
    if isinstance(exc, RequestValidationError):
        return _validation_error_to_app_error(exc)
    if isinstance(exc, HTTPException):
        return _http_exception_to_app_error(exc)
    if isinstance(exc, asyncio.TimeoutError):
        return TimeoutError("Request timed out", stage="response")
    if isinstance(exc, TimeoutError):
        return exc
    return ExternalServiceError(str(exc), stage="response", retryable=False)


def error_response_payload(error: AppError, request_id: str | None) -> dict[str, Any]:
    payload = error.to_payload(request_id=request_id)
    if error.details:
        payload["error"]["details"] = error.details
    return payload


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = get_request_id()
            app_error = normalize_exception(exc)

            log_method = logger.error
            if app_error.status_code < 500:
                log_method = logger.warning
            elif app_error.status_code >= 500 and not app_error.retryable:
                log_method = logger.critical
            log_method(
                "request_failed",
                extra={
                    "stage": app_error.stage,
                    "error_type": app_error.type,
                    "status_code": app_error.status_code,
                    "request_id": request_id,
                    "trace": "".join(traceback.format_exception(exc)),
                },
            )
            emit_failure_metric(stage=app_error.stage, error_type=app_error.type)
            response = JSONResponse(status_code=app_error.status_code, content=error_response_payload(app_error, request_id))
            if request_id:
                response.headers["X-Request-ID"] = request_id
            return response
