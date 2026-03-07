from typing import Any, Literal
from pydantic import BaseModel, Field


SessionType = Literal["story", "lesson"]


class CreateSessionRequest(BaseModel):
    prompt: str = Field(min_length=3)
    session_type: SessionType
    duration: int = Field(default=10, ge=1, le=60)


class ChoiceRequest(BaseModel):
    session_id: str
    scene_id: str
    choice_text: str


class QuizSubmitRequest(BaseModel):
    lesson_id: str
    question_id: str
    answer: str
    time_spent_seconds: int = Field(default=0, ge=0)


class GenericResponse(BaseModel):
    status: str = "ok"
    data: dict[str, Any]
