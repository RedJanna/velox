"""Health and readiness endpoints for container orchestration."""

import asyncio
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from velox.config.settings import settings
from velox.core.hotel_profile_loader import get_all_profiles

router = APIRouter(prefix="/health", tags=["health"])


def _result(ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    """Build a consistent status object for readiness checks."""
    payload: dict[str, Any] = {"ok": ok, "detail": detail}
    payload.update(extra)
    return payload


async def check_db(request: Request) -> dict[str, Any]:
    """Validate database reachability via current app pool."""
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        return _result(False, "db_pool_not_initialized")

    try:
        async with asyncio.timeout(5):
            probe = await db_pool.fetchval("SELECT 1")
    except TimeoutError:
        return _result(False, "db_timeout")
    except Exception as exc:
        return _result(False, "db_error", error_type=type(exc).__name__)

    return _result(bool(probe == 1), "db_connected")


async def check_redis(request: Request) -> dict[str, Any]:
    """Validate redis reachability via app redis client."""
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        return _result(False, "redis_not_initialized")

    try:
        async with asyncio.timeout(5):
            pong = await redis_client.ping()
    except TimeoutError:
        return _result(False, "redis_timeout")
    except Exception as exc:
        return _result(False, "redis_error", error_type=type(exc).__name__)

    return _result(bool(pong), "redis_connected")


async def check_openai_api_key() -> dict[str, Any]:
    """Validate OpenAI client configuration is present."""
    configured = bool(settings.openai_api_key.strip())
    if not configured:
        return _result(False, "openai_api_key_missing")
    return _result(True, "openai_api_key_configured")


async def check_elektraweb() -> dict[str, Any]:
    """Validate Elektraweb configuration format."""
    base_url = settings.elektra_api_base_url.strip()
    api_key = settings.elektra_api_key.strip()
    if not base_url or not api_key:
        return _result(False, "elektraweb_credentials_missing")

    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return _result(False, "elektraweb_base_url_invalid")

    return _result(True, "elektraweb_configured")


def check_profiles_loaded() -> dict[str, Any]:
    """Validate at least one hotel profile is loaded in memory."""
    profiles_count = len(get_all_profiles())
    detail = "profiles_loaded" if profiles_count > 0 else "profiles_missing"
    return _result(profiles_count > 0, detail, count=profiles_count)


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "service": "velox", "version": "0.1.0"}


@router.get("/ready")
async def readiness_check(request: Request) -> JSONResponse:
    """Readiness probe with dependency-level checks."""
    checks: dict[str, dict[str, Any]] = {
        "database": await check_db(request),
        "redis": await check_redis(request),
        "openai": await check_openai_api_key(),
        "elektraweb": await check_elektraweb(),
        "hotel_profiles_loaded": check_profiles_loaded(),
    }
    all_ok = all(check.get("ok", False) for check in checks.values())
    return JSONResponse(
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
        status_code=200 if all_ok else 503,
    )
