from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multimodal AI Learning Platform"
    env: str = "dev"
    api_prefix: str = "/api/v1"

    redis_url: str = "redis://redis:6379/0"
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/modal"

    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    gcs_media_bucket: str = ""
    gcs_signed_url_ttl_seconds: int = 3600
    vertex_model_text: str = "gemini-2.5-pro"
    vertex_model_image: str = "imagen-3.0-generate-002"

    videofx_endpoint: str | None = None
    videofx_api_key: str | None = None

    firebase_project_id: str = ""
    firebase_credentials_path: str | None = None
    firebase_web_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("firebase_credentials_path", "videofx_endpoint", "videofx_api_key")
    @classmethod
    def normalize_blank_path(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value


settings = Settings()
