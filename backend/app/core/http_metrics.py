import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import observe_http_request


class HttpMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        route = request.scope.get("route")
        path = getattr(route, "name", None) or request.url.path
        observe_http_request(
            method=request.method,
            path=path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response
