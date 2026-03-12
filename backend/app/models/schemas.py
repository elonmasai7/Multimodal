from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


SessionType = Literal["story", "lesson"]
VideoFormat = Literal["mp4", "webm"]


class VideoOptions(BaseModel):
    duration_seconds: int = Field(default=8, ge=1, le=30)
    resolution: str = Field(default="1280x720")
    fps: int = Field(default=24, ge=1, le=60)
    format: VideoFormat = "mp4"

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, value: str) -> str:
        allowed = {"3840x2160", "2560x1440", "1920x1080", "1280x720", "854x480", "640x360"}
        if value not in allowed:
            raise ValueError(f"Resolution must be one of: {', '.join(sorted(allowed))}")
        return value


class CreateSessionRequest(BaseModel):
    prompt: str = Field(min_length=3)
    session_type: SessionType
    duration: int = Field(default=10, ge=1, le=60)
    video: VideoOptions | None = None


class ChoiceRequest(BaseModel):
    session_id: str
    scene_id: str
    choice_text: str


class QuizSubmitRequest(BaseModel):
    lesson_id: str
    question_id: str
    answer: str
    time_spent_seconds: int = Field(default=0, ge=0)


class AuthSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    status: str = "ok"
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: dict[str, Any] | None = None


class GenericResponse(BaseModel):
    status: str = "ok"
    data: dict[str, Any]


class StudentProgressItem(BaseModel):
    user_id: str
    lesson_id: str
    score: float
    completion: float
    time_spent_seconds: int
    updated_at: datetime | None = None


class LessonPerformanceItem(BaseModel):
    lesson_id: str
    average_score: float
    completion_rate: float
    attempts: int
