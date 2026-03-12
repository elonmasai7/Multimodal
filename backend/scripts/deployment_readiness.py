#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import timedelta
from urllib.parse import urlparse

import asyncpg
import httpx
from redis.asyncio import Redis

from app.core.config import settings


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    details: dict


def _ok(name: str, message: str, **details) -> CheckResult:
    return CheckResult(name=name, status="ok", message=message, details=details)


def _warn(name: str, message: str, **details) -> CheckResult:
    return CheckResult(name=name, status="warn", message=message, details=details)


def _fail(name: str, message: str, **details) -> CheckResult:
    return CheckResult(name=name, status="fail", message=message, details=details)


def check_required_env() -> CheckResult:
    required = [
        "POSTGRES_URL",
        "REDIS_URL",
        "GCS_MEDIA_BUCKET",
        "VERTEX_MODEL_TEXT",
        "VERTEX_MODEL_IMAGE",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_WEB_API_KEY",
    ]
    if settings.genai_use_vertexai:
        required.extend(["GCP_PROJECT_ID", "GCP_REGION"])
    else:
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            required.append("GEMINI_API_KEY")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        return _fail("env", "Missing required environment variables", missing=missing)
    if not os.getenv("VIDEOFX_ENDPOINT"):
        return _warn("env", "VIDEOFX_ENDPOINT not set; video generation will use GenAI fallback only")
    return _ok("env", "Required environment variables present")


async def check_redis() -> CheckResult:
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        pong = await client.ping()
        await client.close()
        if pong is True:
            return _ok("redis", "Redis reachable")
        return _fail("redis", "Redis ping returned unexpected response", pong=str(pong))
    except Exception as exc:
        return _fail("redis", "Redis connectivity failed", error=str(exc))


async def check_postgres() -> CheckResult:
    try:
        postgres_url = settings.postgres_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(postgres_url)
        value = await conn.fetchval("SELECT 1")
        await conn.close()
        return _ok("postgres", "Cloud SQL/Postgres reachable", probe=value)
    except Exception as exc:
        return _fail("postgres", "Postgres connectivity failed", error=str(exc))


def check_gcp_auth() -> CheckResult:
    try:
        import google.auth
        from google.auth.transport.requests import Request

        credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(Request())
        return _ok(
            "gcp-auth",
            "Google application default credentials valid",
            project=project,
            service_account=getattr(credentials, "service_account_email", None),
        )
    except Exception as exc:
        return _fail("gcp-auth", "Google credentials invalid/unavailable", error=str(exc))


async def check_firestore() -> CheckResult:
    try:
        from google.cloud.firestore_v1 import AsyncClient

        client = AsyncClient(project=settings.gcp_project_id)
        probe = await client.collection("__readiness").document("probe").get()
        return _ok("firestore", "Firestore reachable", probe_exists=probe.exists)
    except Exception as exc:
        return _fail("firestore", "Firestore connectivity failed", error=str(exc))


def check_gcs_and_iam() -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        from google.cloud import storage

        client = storage.Client(project=settings.gcp_project_id)
        bucket = client.bucket(settings.gcs_media_bucket)

        if not bucket.exists():
            return [_fail("gcs", "Configured GCS bucket does not exist", bucket=settings.gcs_media_bucket)]

        results.append(_ok("gcs", "GCS bucket reachable", bucket=settings.gcs_media_bucket))

        required_perms = ["storage.objects.create", "storage.objects.get", "storage.objects.delete"]
        granted = bucket.test_iam_permissions(required_perms)
        missing = [perm for perm in required_perms if perm not in granted]
        if missing:
            results.append(_fail("gcs-iam", "Missing required bucket IAM permissions", missing=missing))
        else:
            results.append(_ok("gcs-iam", "Bucket IAM permissions OK", permissions=granted))

        try:
            blob = bucket.blob("readiness/signature-check.txt")
            signed = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=5),
                method="GET",
            )
            parsed = urlparse(signed)
            results.append(_ok("gcs-signing", "Signed URL generation works", host=parsed.netloc))
        except Exception as exc:
            results.append(
                _fail(
                    "gcs-signing",
                    "Signed URL generation failed (likely missing roles/iam.serviceAccountTokenCreator)",
                    error=str(exc),
                )
            )

        return results
    except Exception as exc:
        return [_fail("gcs", "GCS connectivity failed", error=str(exc))]


def check_vertex() -> CheckResult:
    try:
        from app.services.genai_client import get_genai_client

        client = get_genai_client()
        token_info = client.models.count_tokens(model=settings.vertex_model_text, contents="readiness-check")
        return _ok("genai", "GenAI text model reachable", total_tokens=int(getattr(token_info, "total_tokens", 0)))
    except Exception as exc:
        return _fail("genai", "GenAI text model check failed", error=str(exc))


def check_imagen() -> CheckResult:
    try:
        from google.genai import types as genai_types

        from app.services.genai_client import get_genai_client

        client = get_genai_client()
        response = client.models.generate_content(
            model=settings.vertex_model_image,
            contents="A minimal line drawing of a rocket.",
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=genai_types.ImageConfig(aspect_ratio="16:9"),
            ),
        )
        parts = getattr(response, "parts", None)
        if not parts:
            candidates = getattr(response, "candidates", None)
            if candidates:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None) if content else None
        if not parts:
            return _fail("imagen", "Imagen response missing inline data")
        return _ok("imagen", "Imagen model accessible", model=settings.vertex_model_image)
    except Exception as exc:
        return _fail("imagen", "Imagen model check failed", error=str(exc))


async def check_videofx() -> CheckResult:
    endpoint = settings.videofx_endpoint
    if not endpoint:
        return _fail("videofx", "VIDEOFX_ENDPOINT not configured")

    headers = {"Content-Type": "application/json"}
    if settings.videofx_api_key:
        headers["Authorization"] = f"Bearer {settings.videofx_api_key}"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(str(endpoint), headers=headers, json={"prompt": "health check", "duration_seconds": 1})

        if response.status_code < 500:
            return _ok("videofx", "VideoFX endpoint reachable", status_code=response.status_code)
        return _fail("videofx", "VideoFX endpoint returned server error", status_code=response.status_code)
    except Exception as exc:
        return _fail("videofx", "VideoFX connectivity failed", error=str(exc))


async def check_firebase_admin() -> CheckResult:
    try:
        import firebase_admin
        from firebase_admin import auth, credentials

        if not firebase_admin._apps:
            if settings.firebase_credentials_path:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
            else:
                firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

        auth.list_users(max_results=1)
        return _ok("firebase-admin", "Firebase Admin SDK reachable")
    except Exception as exc:
        return _fail("firebase-admin", "Firebase Admin check failed", error=str(exc))


async def check_firebase_web_api() -> CheckResult:
    if not settings.firebase_web_api_key:
        return _fail("firebase-web-api", "FIREBASE_WEB_API_KEY not configured")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.firebase_web_api_key}"
    payload = {"email": "readiness-check@example.com", "password": "invalid-password", "returnSecureToken": True}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)

        if response.status_code in (200, 400):
            return _ok("firebase-web-api", "Firebase Web API reachable", status_code=response.status_code)
        return _fail("firebase-web-api", "Firebase Web API returned unexpected status", status_code=response.status_code)
    except Exception as exc:
        return _fail("firebase-web-api", "Firebase Web API connectivity failed", error=str(exc))


async def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = [check_required_env()]
    if results[-1].status == "fail":
        return results

    results.extend(await asyncio.gather(check_redis(), check_postgres(), check_firestore(), check_videofx(), check_firebase_admin(), check_firebase_web_api()))
    results.extend(check_gcs_and_iam())
    results.append(check_vertex())
    results.append(check_imagen())
    return results


def print_human(results: list[CheckResult]) -> None:
    for result in results:
        icon = "[OK]" if result.status == "ok" else "[WARN]" if result.status == "warn" else "[FAIL]"
        print(f"{icon} {result.name}: {result.message}")
        if result.details:
            print(f"       details={json.dumps(result.details, default=str)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deployment readiness checks")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any check is not OK")
    args = parser.parse_args()

    results = asyncio.run(run_checks())

    if args.json:
        print(json.dumps([asdict(item) for item in results], default=str))
    else:
        print_human(results)

    has_fail = any(item.status == "fail" for item in results)
    has_warn = any(item.status == "warn" for item in results)

    if args.strict and (has_fail or has_warn):
        return 1
    if has_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
