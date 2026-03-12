import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.demo_auth import build_demo_auth_response, is_demo_credentials, is_demo_auth_enabled
from app.deps.auth import AuthUser, get_current_user
from app.models.schemas import AuthLoginRequest, AuthRefreshRequest, AuthSignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _identity_toolkit_url(path: str) -> str:
    if not settings.firebase_web_api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="FIREBASE_WEB_API_KEY not configured")
    return f"https://identitytoolkit.googleapis.com/v1/{path}?key={settings.firebase_web_api_key}"


def _map_firebase_error(response: httpx.Response, default_status: int, default_message: str) -> None:
    try:
        body = response.json().get("error", {})
    except ValueError:
        body = {}
    firebase_message = str(body.get("message", "")).strip()
    detail_map = {
        "EMAIL_EXISTS": (status.HTTP_409_CONFLICT, "An account with that email already exists"),
        "EMAIL_NOT_FOUND": (status.HTTP_401_UNAUTHORIZED, "No account found for that email"),
        "INVALID_PASSWORD": (status.HTTP_401_UNAUTHORIZED, "Incorrect password"),
        "INVALID_LOGIN_CREDENTIALS": (status.HTTP_401_UNAUTHORIZED, "Incorrect email or password"),
        "USER_DISABLED": (status.HTTP_403_FORBIDDEN, "This account has been disabled"),
        "TOO_MANY_ATTEMPTS_TRY_LATER": (status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Try again later"),
    }
    if firebase_message.startswith("WEAK_PASSWORD"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters long")
    mapped_status, mapped_message = detail_map.get(firebase_message, (default_status, default_message))
    raise HTTPException(status_code=mapped_status, detail=mapped_message)


@router.post("/signup")
async def signup(req: AuthSignupRequest) -> dict:
    payload = {
        "email": req.email,
        "password": req.password,
        "returnSecureToken": True,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(_identity_toolkit_url("accounts:signUp"), json=payload)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Authentication service timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable") from exc
    if response.status_code >= 400:
        _map_firebase_error(response, status.HTTP_400_BAD_REQUEST, "Signup failed")

    data = response.json()
    if req.display_name:
        update_payload = {
            "idToken": data.get("idToken"),
            "displayName": req.display_name,
            "returnSecureToken": True,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                update_response = await client.post(_identity_toolkit_url("accounts:update"), json=update_payload)
        except httpx.HTTPError:
            update_response = None
        if update_response is not None and update_response.status_code < 400:
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
    if is_demo_credentials(req.email, req.password):
        return build_demo_auth_response()

    if is_demo_auth_enabled() and not settings.firebase_web_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Firebase auth is not configured. Use the demo login: {settings.demo_auth_email} / {settings.demo_auth_password}",
        )

    payload = {
        "email": req.email,
        "password": req.password,
        "returnSecureToken": True,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(_identity_toolkit_url("accounts:signInWithPassword"), json=payload)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Authentication service timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable") from exc
    if response.status_code >= 400:
        _map_firebase_error(response, status.HTTP_401_UNAUTHORIZED, "Login failed")

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


@router.post("/refresh")
async def refresh(req: AuthRefreshRequest) -> dict:
    if not settings.firebase_web_api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="FIREBASE_WEB_API_KEY not configured")
    url = f"https://securetoken.googleapis.com/v1/token?key={settings.firebase_web_api_key}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data={"grant_type": "refresh_token", "refresh_token": req.refresh_token})
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Authentication service timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable") from exc
    if response.status_code >= 400:
        _map_firebase_error(response, status.HTTP_401_UNAUTHORIZED, "Token refresh failed")
    data = response.json()
    return {
        "status": "ok",
        "data": {
            "id_token": data.get("id_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
        },
    }


@router.post("/demo")
async def demo_login() -> dict:
    if not is_demo_auth_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo login disabled")
    return build_demo_auth_response()


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
