from __future__ import annotations

import re

from app.core.config import settings
from app.core.errors import ValidationError

RESOLUTION_PATTERN = re.compile(r"^\d+x\d+$")
SUPPORTED_RESOLUTIONS = [
    "3840x2160",
    "2560x1440",
    "1920x1080",
    "1280x720",
    "854x480",
    "640x360",
]


def validate_prompt(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt is required")
    trimmed = prompt.strip()
    if len(trimmed) < 3:
        raise ValidationError("Prompt must be at least 3 characters")
    if len(trimmed) > settings.prompt_max_chars:
        raise ValidationError(f"Prompt exceeds {settings.prompt_max_chars} characters")
    return trimmed


def validate_resolution(resolution: str) -> str:
    if not RESOLUTION_PATTERN.match(resolution):
        raise ValidationError("Resolution must be in WIDTHxHEIGHT format")
    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValidationError(f"Resolution must be one of: {', '.join(SUPPORTED_RESOLUTIONS)}")
    return resolution


def fallback_resolutions(current: str) -> list[str]:
    if current not in SUPPORTED_RESOLUTIONS:
        return ["1280x720", "854x480"]
    index = SUPPORTED_RESOLUTIONS.index(current)
    return SUPPORTED_RESOLUTIONS[index + 1 :]
