from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class AppError(Exception):
    message: str
    stage: str = "unknown"
    status_code: int = 500
    error_type: str | None = None
    safe_message: str | None = None
    details: dict[str, Any] | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        super().__init__(self.message)

    @property
    def type(self) -> str:
        return self.error_type or self.__class__.__name__

    def public_message(self) -> str:
        return self.safe_message or self.message

    def to_payload(self, request_id: str | None = None) -> dict[str, Any]:
        return {
            "error": {
                "type": self.type,
                "message": self.public_message(),
                "stage": self.stage,
                "timestamp": _utc_now(),
                "request_id": request_id,
            }
        }


class ValidationError(AppError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            stage="validation",
            status_code=400,
            safe_message=message,
            details=details,
            retryable=False,
        )


class ModelInferenceError(AppError):
    def __init__(
        self,
        message: str,
        *,
        stage: str = "inference",
        retryable: bool = True,
        safe_message: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            stage=stage,
            status_code=502,
            safe_message=safe_message or "Model inference failed",
            retryable=retryable,
        )


class EncodingError(AppError):
    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(
            message=message,
            stage="encoding",
            status_code=502,
            safe_message="Video encoding failed",
            retryable=retryable,
        )


class StorageError(AppError):
    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(
            message=message,
            stage="storage",
            status_code=503,
            safe_message="Storage operation failed",
            retryable=retryable,
        )


class ExternalServiceError(AppError):
    def __init__(self, message: str, *, stage: str = "external", retryable: bool = True) -> None:
        super().__init__(
            message=message,
            stage=stage,
            status_code=503,
            safe_message="External service unavailable",
            retryable=retryable,
        )


class TimeoutError(AppError):
    def __init__(self, message: str, *, stage: str = "inference") -> None:
        super().__init__(
            message=message,
            stage=stage,
            status_code=504,
            safe_message="Request timed out",
            retryable=True,
        )


class AIIntegrationError(ModelInferenceError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, stage="inference", retryable=True, safe_message="AI integration failed")


class MediaGenerationError(AppError):
    def __init__(self, message: str, *, stage: str = "rendering") -> None:
        super().__init__(
            message=message,
            stage=stage,
            status_code=502,
            safe_message="Media generation failed",
            retryable=True,
        )
