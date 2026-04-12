"""Admin portal support endpoints for bootstrap, identity, and overview data."""

from __future__ import annotations

# ruff: noqa: E501
from ipaddress import ip_address
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import ROLE_PERMISSIONS, TokenData, get_current_user
from velox.api.routes.health import (
    check_db,
    check_elektraweb,
    check_elektraweb_generic_sync,
    check_openai_api_key,
    check_profiles_loaded,
    check_redis,
)
from velox.config.constants import Role
from velox.config.settings import settings
from velox.utils.passwords import ensure_password_within_bcrypt_limit, hash_password
from velox.utils.totp import build_otpauth_qr_svg_data_uri, build_otpauth_uri, generate_totp_secret

router = APIRouter(prefix="/admin", tags=["admin"])

LOCAL_BOOTSTRAP_HOSTS = {"127.0.0.1", "::1", "localhost"}


class BootstrapStatusResponse(BaseModel):
    """Public bootstrap status for the admin panel login screen."""

    bootstrap_required: bool
    has_admin_users: bool
    local_bootstrap_allowed: bool
    token_bootstrap_enabled: bool
    panel_url: str
    public_host: str
    hotel_options: list[dict[str, Any]] = Field(default_factory=list)


class BootstrapAdminRequest(BaseModel):
    """One-time admin bootstrap payload."""

    hotel_id: int
    username: str = Field(min_length=3, max_length=100)
    display_name: str | None = Field(default=None, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    bootstrap_token: str | None = Field(default=None, max_length=256)
    totp_secret: str | None = Field(default=None, min_length=16, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_byte_length(cls, value: str) -> str:
        """Enforce bcrypt byte-length limit to avoid runtime hashing errors."""
        return ensure_password_within_bcrypt_limit(value)


class BootstrapAdminResponse(BaseModel):
    """Bootstrap response containing one-time TOTP enrollment details."""

    status: str
    hotel_id: int
    username: str
    panel_url: str
    totp_secret: str
    otpauth_uri: str
    otpauth_qr_svg_data_uri: str


class RecoverTotpRequest(BaseModel):
    """Recovery payload for regenerating an admin TOTP enrollment secret."""

    username: str = Field(min_length=3, max_length=100)
    bootstrap_token: str | None = Field(default=None, max_length=256)
    new_password: str | None = Field(default=None, min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_byte_length(cls, value: str | None) -> str | None:
        """Enforce bcrypt byte-length limit for optional recovery password reset."""
        if value is None:
            return None
        return ensure_password_within_bcrypt_limit(value)


class RecoverTotpResponse(BaseModel):
    """Recovery response containing refreshed TOTP enrollment details."""

    status: str
    username: str
    otpauth_uri: str
    totp_secret: str
    otpauth_qr_svg_data_uri: str


@router.get("/bootstrap/status", response_model=BootstrapStatusResponse)
async def bootstrap_status(request: Request) -> BootstrapStatusResponse:
    """Expose whether the panel needs one-time admin bootstrap."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        admin_count = int(await conn.fetchval("SELECT COUNT(*) FROM admin_users") or 0)
        hotel_rows = await conn.fetch(
            "SELECT hotel_id, COALESCE(name_en, name_tr, 'Hotel') AS name FROM hotels ORDER BY hotel_id"
        )

    local_allowed = _is_local_bootstrap_request(request)
    return BootstrapStatusResponse(
        bootstrap_required=admin_count == 0,
        has_admin_users=admin_count > 0,
        local_bootstrap_allowed=local_allowed,
        token_bootstrap_enabled=bool(settings.admin_bootstrap_token.strip()),
        panel_url=settings.admin_panel_url,
        public_host=settings.public_host,
        hotel_options=[dict(row) for row in hotel_rows],
    )


@router.post("/bootstrap", response_model=BootstrapAdminResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_admin_account(body: BootstrapAdminRequest, request: Request) -> BootstrapAdminResponse:
    """Create the first admin account with TOTP enrollment details."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        admin_count = int(await conn.fetchval("SELECT COUNT(*) FROM admin_users") or 0)
        if admin_count > 0:
            raise HTTPException(status_code=409, detail="Bootstrap already completed")
        if not _bootstrap_permitted(request, body.bootstrap_token):
            raise HTTPException(status_code=403, detail="Bootstrap requires localhost access or a valid bootstrap token")

        hotel_exists = await conn.fetchval("SELECT 1 FROM hotels WHERE hotel_id = $1", body.hotel_id)
        if hotel_exists != 1:
            raise HTTPException(status_code=404, detail="Hotel not found")

        existing_user = await conn.fetchval("SELECT 1 FROM admin_users WHERE username = $1", body.username)
        if existing_user == 1:
            raise HTTPException(status_code=409, detail="Username already exists")

        totp_secret = body.totp_secret.strip() if body.totp_secret else generate_totp_secret()
        password_hash = hash_password(body.password)
        await conn.execute(
            """
            INSERT INTO admin_users (hotel_id, username, password_hash, role, display_name, totp_secret, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, true)
            """,
            body.hotel_id,
            body.username,
            password_hash,
            Role.ADMIN.value,
            body.display_name,
            totp_secret,
        )

    otpauth_uri = build_otpauth_uri(
        secret=totp_secret,
        account_name=body.username,
        issuer=settings.admin_totp_issuer,
    )

    return BootstrapAdminResponse(
        status="created",
        hotel_id=body.hotel_id,
        username=body.username,
        panel_url=settings.admin_panel_url,
        totp_secret=totp_secret,
        otpauth_uri=otpauth_uri,
        otpauth_qr_svg_data_uri=build_otpauth_qr_svg_data_uri(otpauth_uri),
    )


@router.post("/bootstrap/recover-totp", response_model=RecoverTotpResponse)
async def recover_admin_totp(body: RecoverTotpRequest, request: Request) -> RecoverTotpResponse:
    """Regenerate TOTP secret for an existing admin account via bootstrap recovery token."""
    if not _bootstrap_permitted(request, body.bootstrap_token):
        raise HTTPException(status_code=403, detail="Recovery requires localhost access or a valid bootstrap token")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT id, username FROM admin_users WHERE username = $1 AND is_active = true", body.username)
        if row is None:
            raise HTTPException(status_code=404, detail="Admin user not found")

        refreshed_secret = generate_totp_secret()
        if body.new_password:
            password_hash = hash_password(body.new_password)
            await conn.execute(
                "UPDATE admin_users SET totp_secret = $1, password_hash = $2 WHERE id = $3",
                refreshed_secret,
                password_hash,
                row["id"],
            )
        else:
            await conn.execute(
                "UPDATE admin_users SET totp_secret = $1 WHERE id = $2",
                refreshed_secret,
                row["id"],
            )

    otpauth_uri = build_otpauth_uri(
        secret=refreshed_secret,
        account_name=str(row["username"]),
        issuer=settings.admin_totp_issuer,
    )
    return RecoverTotpResponse(
        status="updated",
        username=str(row["username"]),
        otpauth_uri=otpauth_uri,
        totp_secret=refreshed_secret,
        otpauth_qr_svg_data_uri=build_otpauth_qr_svg_data_uri(otpauth_uri),
    )


@router.get("/me")
async def admin_me(
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return current admin identity, permissions, and panel metadata."""
    return {
        "user_id": user.user_id,
        "hotel_id": user.hotel_id,
        "username": user.username,
        "role": user.role.value,
        "display_name": user.display_name,
        "permissions": sorted(ROLE_PERMISSIONS.get(user.role, set())),
        "panel_url": settings.admin_panel_url,
        "public_host": settings.public_host,
    }


@router.get("/dashboard/overview")
async def admin_dashboard_overview(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
) -> dict[str, Any]:
    """Return cross-module operational summary cards and recent work queues."""
    effective_hotel_id = hotel_id if user.role == Role.ADMIN else user.hotel_id
    db = request.app.state.db_pool

    async with db.acquire() as conn:
        counts_row = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM hotels WHERE ($1::int IS NULL OR hotel_id = $1)) AS hotels_total,
                (SELECT COUNT(*) FROM conversations WHERE ($1::int IS NULL OR hotel_id = $1)) AS conversations_total,
                (SELECT COUNT(*) FROM conversations WHERE ($1::int IS NULL OR hotel_id = $1) AND is_active = true) AS conversations_active,
                (
                    SELECT COUNT(*) FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id
                    WHERE ($1::int IS NULL OR c.hotel_id = $1)
                      AND m.created_at >= now() - interval '24 hours'
                ) AS messages_last_24h,
                (
                    (SELECT COUNT(*) FROM stay_holds WHERE ($1::int IS NULL OR hotel_id = $1) AND status = 'PENDING_APPROVAL' AND archived_at IS NULL) +
                    (SELECT COUNT(*) FROM restaurant_holds WHERE ($1::int IS NULL OR hotel_id = $1) AND status = 'PENDING_APPROVAL' AND archived_at IS NULL) +
                    (SELECT COUNT(*) FROM transfer_holds WHERE ($1::int IS NULL OR hotel_id = $1) AND status = 'PENDING_APPROVAL' AND archived_at IS NULL)
                ) AS pending_holds,
                (
                    SELECT COUNT(*) FROM tickets
                    WHERE ($1::int IS NULL OR hotel_id = $1)
                      AND status IN ('OPEN', 'IN_PROGRESS')
                ) AS open_tickets,
                (
                    SELECT COUNT(*) FROM tickets
                    WHERE ($1::int IS NULL OR hotel_id = $1)
                      AND priority = 'high'
                      AND status IN ('OPEN', 'IN_PROGRESS')
                ) AS high_priority_tickets
            """,
            effective_hotel_id,
        )
        recent_conversations = await conn.fetch(
            """
            SELECT
                c.id,
                c.hotel_id,
                c.phone_display,
                COALESCE(NULLIF(c.current_state, ''), assistant_meta.last_state, 'GREETING') AS current_state,
                COALESCE(NULLIF(c.current_intent, ''), assistant_meta.last_intent) AS current_intent,
                c.risk_flags,
                c.last_message_at
            FROM conversations c
            LEFT JOIN LATERAL (
                SELECT
                    m.internal_json->>'intent' AS last_intent,
                    m.internal_json->>'state' AS last_state
                FROM messages m
                WHERE m.conversation_id = c.id
                  AND m.role = 'assistant'
                ORDER BY m.created_at DESC
                LIMIT 1
            ) assistant_meta ON true
            WHERE ($1::int IS NULL OR hotel_id = $1)
            ORDER BY c.last_message_at DESC
            LIMIT 5
            """,
            effective_hotel_id,
        )
        recent_tickets = await conn.fetch(
            """
            SELECT ticket_id, hotel_id, reason, priority, status, assigned_to_role, created_at
            FROM tickets
            WHERE ($1::int IS NULL OR hotel_id = $1)
              AND status IN ('OPEN', 'IN_PROGRESS')
            ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, created_at DESC
            LIMIT 5
            """,
            effective_hotel_id,
        )
        recent_holds = await conn.fetch(
            """
            SELECT * FROM (
                SELECT hold_id, hotel_id, status, created_at, 'stay' AS hold_type FROM stay_holds
                WHERE ($1::int IS NULL OR hotel_id = $1) AND status = 'PENDING_APPROVAL' AND archived_at IS NULL
                UNION ALL
                SELECT hold_id, hotel_id, status, created_at, 'restaurant' AS hold_type FROM restaurant_holds
                WHERE ($1::int IS NULL OR hotel_id = $1) AND status = 'PENDING_APPROVAL' AND archived_at IS NULL
                UNION ALL
                SELECT hold_id, hotel_id, status, created_at, 'transfer' AS hold_type FROM transfer_holds
                WHERE ($1::int IS NULL OR hotel_id = $1) AND status = 'PENDING_APPROVAL' AND archived_at IS NULL
            ) pending
            ORDER BY created_at DESC
            LIMIT 5
            """,
            effective_hotel_id,
        )

    counts = dict(counts_row or {})
    return {
        "scope_hotel_id": effective_hotel_id,
        "cards": counts,
        "recent_conversations": [dict(row) for row in recent_conversations],
        "recent_tickets": [dict(row) for row in recent_tickets],
        "recent_holds": [dict(row) for row in recent_holds],
        "panel_url": settings.admin_panel_url,
        "public_host": settings.public_host,
    }


@router.get("/system/overview")
async def admin_system_overview(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return system readiness, dependency status, and panel host metadata."""
    _ = user
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        admin_users = int(await conn.fetchval("SELECT COUNT(*) FROM admin_users") or 0)

    checks = {
        "database": await check_db(request),
        "redis": await check_redis(request),
        "openai": await check_openai_api_key(),
        "elektraweb": await check_elektraweb(),
        "elektraweb_generic_sync": await check_elektraweb_generic_sync(),
        "hotel_profiles_loaded": check_profiles_loaded(),
    }
    return {
        "status": "ready" if all(item["ok"] for item in checks.values()) else "not_ready",
        "checks": checks,
        "public_base_url": settings.public_base_url,
        "panel_url": settings.admin_panel_url,
        "trusted_hosts": settings.trusted_hosts,
        "bootstrap_required": admin_users == 0,
        "admin_user_count": admin_users,
    }


def _is_local_bootstrap_request(request: Request) -> bool:
    """Return whether the caller is local and allowed to bootstrap without a token."""
    cf_connecting_ip = request.headers.get("cf-connecting-ip", "").strip()
    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_hosts = [host.strip() for host in forwarded_for.split(",") if host.strip()]
    real_ip = request.headers.get("x-real-ip", "").strip()
    client_host = request.client.host if request.client else ""
    candidates = [cf_connecting_ip, *forwarded_hosts, real_ip, client_host]
    if any(_is_loopback_host(host) for host in candidates):
        return True

    host_header = request.headers.get("host", "")
    hostname = host_header.split(":", maxsplit=1)[0].strip().strip("[]")
    return hostname in LOCAL_BOOTSTRAP_HOSTS and _is_private_host(client_host)


def _bootstrap_permitted(request: Request, provided_token: str | None) -> bool:
    """Allow bootstrap from localhost or with the configured one-time token."""
    configured_token = settings.admin_bootstrap_token.strip()
    if _is_local_bootstrap_request(request):
        return True
    return bool(configured_token and provided_token and provided_token == configured_token)


def _is_loopback_host(host: str) -> bool:
    """Return whether the given host value is a loopback address."""
    normalized = host.strip().strip("[]")
    if normalized in LOCAL_BOOTSTRAP_HOSTS:
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _is_private_host(host: str) -> bool:
    """Return whether the given host value belongs to a private network."""
    normalized = host.strip().strip("[]")
    try:
        parsed = ip_address(normalized)
    except ValueError:
        return False
    return parsed.is_private or parsed.is_loopback
