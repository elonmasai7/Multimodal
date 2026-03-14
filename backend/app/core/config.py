from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multimodal AI Learning Platform"
    env: str = "dev"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    redis_url: str = "redis://redis:6379/0"
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/modal"

    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    genai_use_vertexai: bool = True
    gemini_api_key: str | None = None
    gcs_media_bucket: str = ""
    gcs_signed_url_ttl_seconds: int = 3600
    vertex_model_text: str = "gemini-2.5-pro"
    vertex_model_interleaved: str = "gemini-2.0-flash-preview-image-generation"
    vertex_model_image: str = "imagen-3.0-generate-002"
    vertex_model_video: str = "veo-3.1-generate-001"
    vertex_model_text_backup: str | None = None
    vertex_model_image_backup: str | None = None

    videofx_endpoint: str | None = None
    videofx_api_key: str | None = None
    videofx_fallback_endpoint: str | None = None
    videofx_timeout_seconds: int = 120
    videofx_fallback_duration_seconds: int = 6
    videofx_fallback_resolution: str = "1280x720"

    prompt_max_chars: int = 2000
    model_inference_timeout_seconds: int = 60
    media_generation_timeout_seconds: int = 90
    retry_max_attempts: int = 3
    retry_base_delay_seconds: float = 0.5
    retry_max_delay_seconds: float = 8.0

    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0
    otel_endpoint: str | None = None
    otel_service_name: str = "modal-backend"
    otel_traces_sample_rate: float = 0.0
    prometheus_enabled: bool = False
    prometheus_pipeline_path: str = "/metrics/pipeline"
    prometheus_system_path: str = "/metrics/system"

    firebase_project_id: str = ""
    firebase_credentials_path: str | None = None
    firebase_web_api_key: str = ""
    demo_auth_enabled: bool = True
    demo_auth_email: str = "demo@modal.local"
    demo_auth_password: str = "demo12345"
    demo_auth_user_id: str = "demo-user"
    demo_auth_token: str = "modal-demo-token"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator(
        "firebase_credentials_path",
        "gemini_api_key",
        "videofx_endpoint",
        "videofx_api_key",
        "videofx_fallback_endpoint",
        "sentry_dsn",
        "otel_endpoint",
        "vertex_model_text_backup",
        "vertex_model_image_backup",
    )
    @classmethod
    def normalize_blank_path(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value


settings = Settings()
