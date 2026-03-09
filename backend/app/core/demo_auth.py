from app.core.config import settings


def is_demo_auth_enabled() -> bool:
    return settings.demo_auth_enabled


def is_demo_credentials(email: str, password: str) -> bool:
    return is_demo_auth_enabled() and email == settings.demo_auth_email and password == settings.demo_auth_password


def is_demo_token(token: str) -> bool:
    return is_demo_auth_enabled() and token == settings.demo_auth_token


def build_demo_user_payload() -> dict:
    return {
        "uid": settings.demo_auth_user_id,
        "email": settings.demo_auth_email,
        "name": "Demo User",
        "claims": {"role": "demo", "auth_provider": "local-demo"},
    }


def build_demo_auth_response() -> dict:
    return {
        "status": "ok",
        "data": {
            "id_token": settings.demo_auth_token,
            "refresh_token": None,
            "expires_in": None,
            "user_id": settings.demo_auth_user_id,
            "email": settings.demo_auth_email,
            "display_name": "Demo User",
        },
    }
