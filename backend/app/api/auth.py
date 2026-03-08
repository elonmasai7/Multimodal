import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.deps.auth import AuthUser, get_current_user
from app.models.schemas import AuthLoginRequest, AuthSignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _identity_toolkit_url(path: str) -> str:
    if not settings.firebase_web_api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="FIREBASE_WEB_API_KEY not configured")
    return f"https://identitytoolkit.googleapis.com/v1/{path}?key={settings.firebase_web_api_key}"


@router.post("/signup")
async def signup(req: AuthSignupRequest) -> dict:
    payload = {
        "email": req.email,
        "password": req.password,
        "returnSecureToken": True,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(_identity_toolkit_url("accounts:signUp"), json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signup failed")

    data = response.json()
    if req.display_name:
        update_payload = {
            "idToken": data.get("idToken"),
            "displayName": req.display_name,
            "returnSecureToken": True,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            update_response = await client.post(_identity_toolkit_url("accounts:update"), json=update_payload)
        if update_response.status_code < 400:
            data = update_response.json()

    return {
        "status": "ok",
        "data": {
            "id_token": data.get("idToken"),
            "refresh_token": data.get("refreshToken"),
            "expires_in": data.get("expiresIn"),
            "user_id": data.get("localId"),
            "email": data.get("email"),
            "display_name": data.get("displayName"),
        },
    }


@router.post("/login")
async def login(req: AuthLoginRequest) -> dict:
    payload = {
        "email": req.email,
        "password": req.password,
        "returnSecureToken": True,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(_identity_toolkit_url("accounts:signInWithPassword"), json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login failed")

    data = response.json()
    return {
        "status": "ok",
        "data": {
            "id_token": data.get("idToken"),
            "refresh_token": data.get("refreshToken"),
            "expires_in": data.get("expiresIn"),
            "user_id": data.get("localId"),
            "email": data.get("email"),
            "display_name": data.get("displayName"),
        },
    }


@router.get("/session")
async def session(user: AuthUser = Depends(get_current_user)) -> dict:
    return {
        "status": "ok",
        "data": {
            "user_id": user.uid,
            "email": user.email,
            "name": user.name,
            "claims": user.claims,
        },
    }
