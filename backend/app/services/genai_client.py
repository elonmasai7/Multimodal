import logging
import os
from functools import lru_cache

from google import genai

from app.core.config import settings
from app.core.errors import AIIntegrationError


logger = logging.getLogger("ai.genai")


def _should_use_vertexai() -> bool:
    if settings.genai_use_vertexai is False:
        return False
    if settings.gcp_project_id:
        return True
    return False


def _api_key() -> str | None:
    return settings.gemini_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


@lru_cache(maxsize=1)
def get_genai_client() -> genai.Client:
    if _should_use_vertexai():
        if not settings.gcp_project_id:
            raise AIIntegrationError("GCP_PROJECT_ID is required for Vertex AI GenAI client")
        return genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )

    api_key = _api_key()
    if api_key:
        return genai.Client(api_key=api_key)

    raise AIIntegrationError(
        "GenAI client unavailable. Set GENAI_USE_VERTEXAI=true with GCP_PROJECT_ID, "
        "or provide GEMINI_API_KEY/GOOGLE_API_KEY."
    )
