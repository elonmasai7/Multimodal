import json
import logging

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, lesson, story
from app.api.metrics import get_metrics_router
from app.core.http_metrics import HttpMetricsMiddleware
from app.core.error_handling import ErrorHandlingMiddleware
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.core.observability import configure_observability, instrument_app
from app.core.config import settings
from app.db.models import Base
from app.db.session import engine

configure_logging()
logger = logging.getLogger("api.main")

app = FastAPI(title=settings.app_name)
configure_observability()
instrument_app(app)

app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(HttpMetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(story.router, prefix=settings.api_prefix)
app.include_router(lesson.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
metrics_router = get_metrics_router()
if metrics_router:
    app.include_router(metrics_router)


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("startup_complete")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.websocket("/ws/stream")
async def websocket_stream(ws: WebSocket) -> None:
    await ws.accept()
    await ws.send_text(json.dumps({"event": "connected", "status": "ok"}))
    while True:
        incoming = await ws.receive_text()
        await ws.send_text(json.dumps({"event": "echo", "data": incoming}))
