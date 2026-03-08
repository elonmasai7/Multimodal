from typing import Any

import firebase_admin
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from pydantic import BaseModel, Field

from app.core.config import settings

security = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    uid: str
    email: str | None = None
    name: str | None = None
    claims: dict[str, Any] = Field(default_factory=dict)


def _init_firebase() -> None:
    if firebase_admin._apps:
        return

    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id or None})
    else:
        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id or None})


def verify_token(id_token: str) -> AuthUser:
    try:
        _init_firebase()
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded.get("uid")
        if not uid:
            raise ValueError("Token payload missing uid")
        return AuthUser(
            uid=uid,
            email=decoded.get("email"),
            name=decoded.get("name"),
            claims=decoded,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token") from exc


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> AuthUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return verify_token(credentials.credentials)


def get_token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    token = request.query_params.get("token")
    return token.strip() if token else None
