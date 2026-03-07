from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup() -> dict:
    return {"status": "ok", "message": "Use Firebase Auth on frontend for production."}


@router.post("/login")
async def login() -> dict:
    return {"status": "ok", "message": "Use Firebase Auth token exchange for production."}
