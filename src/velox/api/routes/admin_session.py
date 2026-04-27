"""Admin session routes for trusted-device preferences and cookie refresh."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import TokenData, TokenResponse, create_access_token, get_current_user
from velox.config.constants import Role
from velox.config.settings import settings
from velox.core.admin_access_control import normalize_department_code
from velox.utils.admin_security import (
    ACCESS_COOKIE_NAME,
    DEFAULT_SESSION_PRESET,
    DEFAULT_VERIFICATION_PRESET,
    SESSION_DURATION_OPTIONS,
    TRUSTED_DEVICE_COOKIE_NAME,
    VERIFICATION_DURATION_OPTIONS,
    build_device_label,
    clear_access_cookies,
    clear_trusted_device_cookie,
    expire_trusted_device_session,
    fetch_trusted_device_record,
    generate_csrf_token,
    refresh_trusted_device_session,
    resolve_session_seconds,
    resolve_verification_seconds,
    revoke_trusted_device_record,
    serialize_duration_options,
    set_access_cookie,
    set_csrf_cookie,
    set_trusted_device_cookie,
    trusted_device_is_active,
    upsert_trusted_device_record,
    utc_now,
)
from velox.utils.totp import verify_totp_code

router = APIRouter(prefix="/admin", tags=["admin-session"])

_VERIFICATION_PRESET_VALUES = {item.value for item in VERIFICATION_DURATION_OPTIONS}
_SESSION_PRESET_VALUES = {item.value for item in SESSION_DURATION_OPTIONS}


class SessionStatusResponse(BaseModel):
    """Session and remembered-device state for the admin UI."""

    has_access_cookie: bool
    has_trusted_device: bool
    verification_active: bool
    session_active: bool
    verification_preset: str = DEFAULT_VERIFICATION_PRESET
    session_preset: str = DEFAULT_SESSION_PRESET
    verification_expires_at: datetime | None = None
    session_expires_at: datetime | None = None
    last_verified_at: datetime | None = None
    last_seen_at: datetime | None = None
    device_label: str | None = None
    user_label: str | None = None
    verification_options: list[dict[str, int | str]]
    session_options: list[dict[str, int | str]]


class SessionPreferenceUpdateRequest(BaseModel):
    """Trusted-device preference changes from the admin panel."""

    remember_device: bool = False
    verification_preset: str = DEFAULT_VERIFICATION_PRESET
    session_preset: str = DEFAULT_SESSION_PRESET
    otp_code: str | None = Field(default=None, min_length=6, max_length=8)

    @field_validator("verification_preset")
    @classmethod
    def validate_verification_preset(cls, value: str) -> str:
        """Reject unsupported verification presets."""
        if value not in _VERIFICATION_PRESET_VALUES:
            raise ValueError("Unsupported verification preset")
        return value

    @field_validator("session_preset")
    @classmethod
    def validate_session_preset(cls, value: str) -> str:
        """Reject unsupported session presets."""
        if value not in _SESSION_PRESET_VALUES:
            raise ValueError("Unsupported session preset")
        return value


class LogoutResponse(BaseModel):
    """Logout response for the admin panel."""

    status: str
    trusted_device_retained: bool


@router.get("/session/status", response_model=SessionStatusResponse)
async def admin_session_status(request: Request) -> SessionStatusResponse:
    """Expose remembered-device status for the login screen and bootstrap flow."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        record = await fetch_trusted_device_record(conn, request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME))
    return _build_session_status_response(
        has_access_cookie=bool(request.cookies.get(ACCESS_COOKIE_NAME)),
        record=record,
    )


@router.post("/session/refresh", response_model=TokenResponse)
async def refresh_admin_session(request: Request, response: Response) -> TokenResponse:
    """Re-issue the short-lived access token from an active remembered session."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        record = await fetch_trusted_device_record(conn, request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME))
        if record is None or not bool(record["is_active"]):
            clear_access_cookies(response)
            raise HTTPException(status_code=401, detail="Remembered device not available")
        if not trusted_device_is_active(record.get("session_expires_at")):
            clear_access_cookies(response)
            raise HTTPException(status_code=401, detail="Remembered session expired")

        session_expires_at = await refresh_trusted_device_session(
            conn,
            record["id"],
            str(record["session_preset"]),
        )

    token_data = _token_data_from_record(record)
    access_token = create_access_token(token_data)
    access_max_age = settings.admin_jwt_expire_minutes * 60
    csrf_token = generate_csrf_token()
    set_access_cookie(response, access_token, max_age_seconds=access_max_age)
    set_csrf_cookie(response, csrf_token, max_age_seconds=access_max_age)
    return TokenResponse(
        access_token=access_token,
        expires_in=access_max_age,
        role=token_data.role.value,
        hotel_id=token_data.hotel_id,
        authentication_mode="session_refresh",
        trusted_device_enabled=True,
        verification_expires_at=record.get("verification_expires_at"),
        session_expires_at=session_expires_at,
    )


@router.get("/session/preferences", response_model=SessionStatusResponse)
async def admin_session_preferences(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> SessionStatusResponse:
    """Return the current user's remembered-device preferences for this browser."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        record = await fetch_trusted_device_record(conn, request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME))
    if record is not None and int(record["admin_user_id"]) != user.user_id:
        record = None
    return _build_session_status_response(has_access_cookie=True, record=record)


@router.put("/session/preferences", response_model=SessionStatusResponse)
async def update_admin_session_preferences(
    body: SessionPreferenceUpdateRequest,
    request: Request,
    response: Response,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> SessionStatusResponse:
    """Create, rotate, or revoke remembered-device preferences for this browser."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        current_record = await fetch_trusted_device_record(conn, request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME))
        current_record = (
            current_record if current_record and int(current_record["admin_user_id"]) == user.user_id else None
        )

        if not body.remember_device:
            if current_record is not None:
                await revoke_trusted_device_record(conn, current_record["id"])
            clear_trusted_device_cookie(response)
            return _build_session_status_response(has_access_cookie=True, record=None)

        admin_row = await conn.fetchrow(
            """
            SELECT id, hotel_id, username, display_name, role, department_code, totp_secret, is_active
            FROM admin_users
            WHERE id = $1
            """,
            user.user_id,
        )
        if admin_row is None or not bool(admin_row["is_active"]):
            raise HTTPException(status_code=403, detail="Account disabled")

        totp_secret = str(admin_row["totp_secret"] or "").strip()
        if not totp_secret:
            raise HTTPException(status_code=403, detail="Two-factor authentication is not configured for this account")
        if not body.otp_code or not verify_totp_code(totp_secret, body.otp_code):
            raise HTTPException(status_code=401, detail="Google Authenticator kodu gecersiz")

        token = await upsert_trusted_device_record(
            conn,
            admin_user=dict(admin_row),
            request=request,
            verification_preset=body.verification_preset,
            session_preset=body.session_preset,
            existing_device_id=current_record["id"] if current_record is not None else None,
        )
        remember_seconds = max(
            resolve_verification_seconds(body.verification_preset),
            resolve_session_seconds(body.session_preset),
        )
        set_trusted_device_cookie(
            response,
            token.cookie_value,
            max_age_seconds=max(remember_seconds, 60),
        )

    now = utc_now()
    updated_record = {
        "admin_user_id": user.user_id,
        "hotel_id": user.hotel_id,
        "username": user.username,
        "display_name": user.display_name,
        "device_label": build_device_label(request),
        "verification_preset": body.verification_preset,
        "session_preset": body.session_preset,
        "verification_expires_at": token.verification_expires_at,
        "session_expires_at": token.session_expires_at,
        "last_verified_at": now,
        "last_seen_at": now,
    }
    return _build_session_status_response(has_access_cookie=True, record=updated_record)


@router.post("/session/forget-device", response_model=SessionStatusResponse)
async def forget_admin_trusted_device(
    request: Request,
    response: Response,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> SessionStatusResponse:
    """Forget the current browser entirely so OTP is required again."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        record = await fetch_trusted_device_record(conn, request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME))
        if record is not None and int(record["admin_user_id"]) == user.user_id:
            await revoke_trusted_device_record(conn, record["id"])
    clear_trusted_device_cookie(response)
    return _build_session_status_response(has_access_cookie=True, record=None)


@router.post("/logout", response_model=LogoutResponse)
async def admin_logout(
    request: Request,
    response: Response,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> LogoutResponse:
    """End the active access session while keeping remembered-device verification intact."""
    db = request.app.state.db_pool
    retained = False
    async with db.acquire() as conn:
        record = await fetch_trusted_device_record(conn, request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME))
        if record is not None and int(record["admin_user_id"]) == user.user_id:
            await expire_trusted_device_session(conn, record["id"])
            retained = True

    clear_access_cookies(response)
    return LogoutResponse(status="logged_out", trusted_device_retained=retained)


def _build_session_status_response(
    *,
    has_access_cookie: bool,
    record: dict[str, Any] | None,
) -> SessionStatusResponse:
    """Build a stable session payload for the admin UI."""
    verification_options = serialize_duration_options(VERIFICATION_DURATION_OPTIONS)
    session_options = serialize_duration_options(SESSION_DURATION_OPTIONS)
    if record is None:
        return SessionStatusResponse(
            has_access_cookie=has_access_cookie,
            has_trusted_device=False,
            verification_active=False,
            session_active=False,
            verification_options=verification_options,
            session_options=session_options,
        )

    verification_expires_at = _coerce_datetime(record.get("verification_expires_at"))
    session_expires_at = _coerce_datetime(record.get("session_expires_at"))
    user_label = str(record.get("display_name") or record.get("username") or "").strip() or None
    return SessionStatusResponse(
        has_access_cookie=has_access_cookie,
        has_trusted_device=True,
        verification_active=trusted_device_is_active(verification_expires_at),
        session_active=trusted_device_is_active(session_expires_at),
        verification_preset=str(record.get("verification_preset") or DEFAULT_VERIFICATION_PRESET),
        session_preset=str(record.get("session_preset") or DEFAULT_SESSION_PRESET),
        verification_expires_at=verification_expires_at,
        session_expires_at=session_expires_at,
        last_verified_at=_coerce_datetime(record.get("last_verified_at")),
        last_seen_at=_coerce_datetime(record.get("last_seen_at")),
        device_label=str(record.get("device_label") or "").strip() or None,
        user_label=user_label,
        verification_options=verification_options,
        session_options=session_options,
    )


def _coerce_datetime(value: object) -> datetime | None:
    """Normalize optional timestamp values."""
    return value if isinstance(value, datetime) else None


def _token_data_from_record(record: dict[str, Any]) -> TokenData:
    """Build token data from a trusted-device record."""
    return TokenData(
        user_id=int(record["admin_user_id"]),
        hotel_id=int(record["hotel_id"]),
        username=str(record["username"]),
        role=Role(str(record["role"])),
        display_name=str(record["display_name"]) if record.get("display_name") else None,
        department_code=normalize_department_code(
            str(record.get("department_code") or "") or None,
            role=Role(str(record["role"])),
        ),
    )
