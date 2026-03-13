from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.deps.auth import AuthUser, get_current_user, get_token_from_request, verify_token
from app.models.schemas import ChoiceRequest, CreateSessionRequest, VideoOptions
from app.services.ai_orchestrator import new_session_id, stream_multimodal_events
from app.services.firestore_repo import FirestoreRepository
from app.services.redis_state import RedisStateManager

router = APIRouter(prefix="/story", tags=["story"])
firestore_repo = FirestoreRepository()
redis_state = RedisStateManager()


@router.post("/create")
async def create_story(req: CreateSessionRequest, user: AuthUser = Depends(get_current_user)) -> dict:
    if req.session_type != "story":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_type must be story")

    session_id = new_session_id()
    await firestore_repo.create_story_session(
        user_id=user.uid,
        session_id=session_id,
        prompt=req.prompt,
        duration=req.duration,
    )
    await redis_state.init_story_state(session_id=session_id)

    return {
        "status": "ok",
        "data": {
            "session_id": session_id,
            "session_type": req.session_type,
            "prompt": req.prompt,
            "duration": req.duration,
        },
    }


@router.get("/stream/{session_id}")
async def story_stream(
    request: Request,
    session_id: str,
    prompt: str | None = None,
    token: str | None = None,
    duration_seconds: int | None = None,
    resolution: str | None = None,
    fps: int | None = None,
    format: str | None = None,
) -> StreamingResponse:
    resolved_token = token or get_token_from_request(request)
    if not resolved_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    user = verify_token(resolved_token)

    session = await firestore_repo.get_story_session(session_id=session_id)
    if session is None or session.get("user_id") != user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story session not found")

    stream_prompt = prompt or session.get("prompt", "Storybook session")
    base_duration = duration_seconds or int(session.get("duration") or 0) or None
    video_data: dict[str, object] = {}
    if base_duration is not None:
        video_data["duration_seconds"] = base_duration
    if resolution is not None:
        video_data["resolution"] = resolution
    if fps is not None:
        video_data["fps"] = fps
    if format is not None:
        video_data["format"] = format
    video_options = VideoOptions.model_validate(video_data)

    async def event_generator():
        async for chunk in stream_multimodal_events(
            prompt=stream_prompt,
            session_type="story",
            video_options=video_options,
            request_id=getattr(request.state, "request_id", None),
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions")
async def list_story_sessions(user: AuthUser = Depends(get_current_user)) -> dict:
    sessions = await firestore_repo.list_story_sessions(user_id=user.uid)
    serialized = []
    for s in sessions:
        created = s.get("created_at")
        serialized.append({
            "session_id": s.get("session_id"),
            "prompt": s.get("prompt", ""),
            "choices_made": len(s.get("history", [])),
            "current_scene": s.get("current_scene", "scene_01"),
            "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
        })
    return {"status": "ok", "data": serialized}


@router.post("/choice")
async def submit_choice(req: ChoiceRequest, user: AuthUser = Depends(get_current_user)) -> dict:
    session = await firestore_repo.get_story_session(session_id=req.session_id)
    if session is None or session.get("user_id") != user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story session not found")

    state = await redis_state.get_story_state(session_id=req.session_id)
    history_len = len((state or {}).get("history", []))
    next_scene = f"scene_{history_len + 2:02d}"
    await redis_state.append_story_choice(
        session_id=req.session_id,
        scene_id=req.scene_id,
        choice_text=req.choice_text,
        next_scene=next_scene,
    )
    await firestore_repo.append_story_choice(
        session_id=req.session_id,
        scene_id=req.scene_id,
        choice_text=req.choice_text,
        next_scene=next_scene,
    )

    return {
        "status": "ok",
        "data": {
            "session_id": req.session_id,
            "scene_id": req.scene_id,
            "choice": req.choice_text,
            "next_scene": next_scene,
        },
    }


@router.get("/resume/{session_id}")
async def resume_story(session_id: str, user: AuthUser = Depends(get_current_user)) -> dict:
    session = await firestore_repo.get_story_session(session_id=session_id)
    if session is None or session.get("user_id") != user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story session not found")

    state = await redis_state.get_story_state(session_id=session_id)
    if state is None:
        state = {
            "current_scene": session.get("current_scene", "scene_01"),
            "history": session.get("history", []),
        }

    return {
        "status": "ok",
        "data": {
            "session_id": session_id,
            "current_scene": state["current_scene"],
            "history": state["history"],
        },
    }
