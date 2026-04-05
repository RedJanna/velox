"""Health and readiness endpoints for container orchestration."""

import asyncio
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse

from velox.config.settings import settings
from velox.core.hotel_profile_loader import get_all_profiles
from velox.utils.metrics import prometheus_content_type, render_metrics

router = APIRouter(prefix="/health", tags=["health"])
metrics_router = APIRouter(tags=["metrics"])


def _result(ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    """Build a consistent status object for readiness checks."""
    payload: dict[str, Any] = {"ok": ok, "detail": detail}
    payload.update(extra)
    return payload


def _metrics_client_allowed(request: Request) -> bool:
    """Allow metrics access only from loopback/private client networks by default."""
    if settings.metrics_allow_public:
        return True

    client = request.client
    if client is None or not client.host:
        return False

    try:
        client_ip = ip_address(client.host)
    except ValueError:
        return False

    return any(client_ip in network for network in settings.metrics_allowed_networks)


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


async def check_openai_live() -> dict[str, Any]:
    """Send a minimal request to OpenAI to verify the key works end-to-end."""
    from openai import AsyncOpenAI

    if not settings.openai_api_key.strip():
        return _result(False, "openai_api_key_missing")

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        async with asyncio.timeout(15):
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
        content = (response.choices[0].message.content or "").strip() if response.choices else ""
        return _result(True, "openai_live_ok", model=settings.openai_model, response_preview=content[:50])
    except Exception as exc:
        return _result(False, "openai_live_error", error_type=type(exc).__name__, error_detail=str(exc)[:300])
    finally:
        await client.close()


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


def check_migrations(request: Request) -> dict[str, Any]:
    """Validate startup migration runner finished without pending files."""
    migration_status = getattr(request.app.state, "migration_status", None)
    if not isinstance(migration_status, dict):
        return _result(False, "migration_status_unavailable")

    pending = migration_status.get("pending") or []
    if pending:
        return _result(False, "pending_migrations", pending=pending)

    return _result(
        True,
        "migrations_ready",
        detected_existing=migration_status.get("detected_existing", []),
        executed=migration_status.get("executed", []),
    )


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    from velox.config.settings import settings

    return {"status": "ok", "service": "velox", "version": "0.1.0", "operation_mode": settings.operation_mode}


@router.get("/openai")
async def openai_check() -> JSONResponse:
    """Live OpenAI connectivity check — tests actual API call."""
    result = await check_openai_live()
    return JSONResponse(
        content=result,
        status_code=200 if result.get("ok") else 503,
    )


@router.get("/ready")
async def readiness_check(request: Request) -> JSONResponse:
    """Readiness probe with dependency-level checks."""
    checks: dict[str, dict[str, Any]] = {
        "database": await check_db(request),
        "migrations": check_migrations(request),
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


@metrics_router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics(request: Request) -> PlainTextResponse:
    """Expose in-process Prometheus-style counters for runtime observability."""
    if not _metrics_client_allowed(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="metrics_access_denied",
        )
    return PlainTextResponse(
        content=render_metrics(),
        media_type=prometheus_content_type(),
    )
