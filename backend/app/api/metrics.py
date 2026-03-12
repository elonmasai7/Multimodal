from fastapi import APIRouter, Response

from app.core.config import settings
from app.core.metrics import get_pipeline_registry, get_system_registry


def get_metrics_router() -> APIRouter | None:
    if not settings.prometheus_enabled:
        return None
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    except Exception:
        return None

    router = APIRouter(tags=["metrics"])

    @router.get(settings.prometheus_pipeline_path)
    async def metrics_pipeline() -> Response:
        registry = get_pipeline_registry()
        if registry is None:
            return Response("", media_type=CONTENT_TYPE_LATEST)
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    @router.get(settings.prometheus_system_path)
    async def metrics_system() -> Response:
        registry = get_system_registry()
        if registry is None:
            return Response("", media_type=CONTENT_TYPE_LATEST)
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    return router
