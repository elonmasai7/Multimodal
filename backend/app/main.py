import json

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, lesson, story
from app.core.config import settings
from app.db.models import Base
from app.db.session import engine

app = FastAPI(title=settings.app_name)

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


@app.on_event("startup")
async def startup() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        # Allow API startup without DB during local scaffolding.
        return


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
