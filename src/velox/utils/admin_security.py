"""Shared admin auth helpers for cookie-backed sessions and trusted devices."""

from __future__ import annotations

import hashlib
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from fastapi import Request, Response

from velox.config.settings import settings

ACCESS_COOKIE_NAME: Final[str] = "velox_admin_access"
TRUSTED_DEVICE_COOKIE_NAME: Final[str] = "velox_admin_device"
CSRF_COOKIE_NAME: Final[str] = "velox_admin_csrf"
CSRF_HEADER_NAME: Final[str] = "x-csrf-token"
SAFE_HTTP_METHODS: Final[frozenset[str]] = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True)
class DurationOption:
    """Frontend-selectable duration preset."""

    value: str
    label: str
    seconds: int


@dataclass(frozen=True)
class TrustedDeviceToken:
    """Generated selector/token pair for a remembered device."""

    selector: str
    raw_token: str
    verification_expires_at: datetime
    session_expires_at: datetime

    @property
    def cookie_value(self) -> str:
        """Return the serialized cookie payload."""
        return f"{self.selector}.{self.raw_token}"


VERIFICATION_DURATION_OPTIONS: Final[tuple[DurationOption, ...]] = (
    DurationOption(value="every_login", label="Her giriste", seconds=0),
    DurationOption(value="8_hours", label="8 saat", seconds=8 * 60 * 60),
    DurationOption(value="24_hours", label="24 saat", seconds=24 * 60 * 60),
    DurationOption(value="3_days", label="3 gun", seconds=3 * 24 * 60 * 60),
    DurationOption(value="7_days", label="7 gun", seconds=7 * 24 * 60 * 60),
)
SESSION_DURATION_OPTIONS: Final[tuple[DurationOption, ...]] = (
    DurationOption(value="1_hour", label="1 saat", seconds=1 * 60 * 60),
    DurationOption(value="8_hours", label="8 saat", seconds=8 * 60 * 60),
    DurationOption(value="24_hours", label="24 saat", seconds=24 * 60 * 60),
    DurationOption(value="7_days", label="7 gun", seconds=7 * 24 * 60 * 60),
)
DEFAULT_VERIFICATION_PRESET: Final[str] = "24_hours"
DEFAULT_SESSION_PRESET: Final[str] = "8_hours"


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def _require_int(value: object, field_name: str) -> int:
    """Convert object payload values to int with explicit error context."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return int(normalized)
    raise ValueError(f"Expected integer-like value for {field_name}")


def serialize_duration_options(options: tuple[DurationOption, ...]) -> list[dict[str, int | str]]:
    """Return duration options in a JSON-friendly format."""
    return [{"value": item.value, "label": item.label, "seconds": item.seconds} for item in options]


def resolve_verification_seconds(preset: str) -> int:
    """Resolve the selected verification preset to seconds."""
    for option in VERIFICATION_DURATION_OPTIONS:
        if option.value == preset:
            return option.seconds
    raise ValueError(f"Unsupported verification preset: {preset}")


def resolve_session_seconds(preset: str) -> int:
    """Resolve the selected session preset to seconds."""
    for option in SESSION_DURATION_OPTIONS:
        if option.value == preset:
            return option.seconds
    raise ValueError(f"Unsupported session preset: {preset}")


def generate_trusted_device_token(
    *,
    verification_preset: str,
    session_preset: str,
) -> TrustedDeviceToken:
    """Generate a fresh selector/token pair and expiry timestamps."""
    now = utc_now()
    verification_seconds = resolve_verification_seconds(verification_preset)
    session_seconds = resolve_session_seconds(session_preset)
    return TrustedDeviceToken(
        selector=secrets.token_urlsafe(12),
        raw_token=secrets.token_urlsafe(24),
        verification_expires_at=now + timedelta(seconds=verification_seconds),
        session_expires_at=now + timedelta(seconds=session_seconds),
    )


def hash_trusted_device_token(raw_token: str) -> str:
    """Hash a trusted-device token before persisting it."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def parse_trusted_device_cookie(cookie_value: str | None) -> tuple[str, str] | None:
    """Parse the trusted-device cookie into selector and raw token parts."""
    if not cookie_value or "." not in cookie_value:
        return None
    selector, raw_token = cookie_value.split(".", maxsplit=1)
    if not selector or not raw_token:
        return None
    return selector, raw_token


def generate_csrf_token() -> str:
    """Generate a CSRF token for cookie-backed admin requests."""
    return secrets.token_urlsafe(24)


def build_device_label(request: Request) -> str:
    """Generate a short, low-sensitivity label for the current browser device."""
    platform = request.headers.get("sec-ch-ua-platform", "").strip('" ').strip()
    user_agent = request.headers.get("user-agent", "").strip()
    browser_match = re.search(r"(Chrome|Firefox|Safari|Edg|Opera)[/ ]", user_agent)
    browser = browser_match.group(1) if browser_match else ""
    label_parts = [part for part in (platform, browser) if part]
    if label_parts:
        return " / ".join(label_parts)[:120]
    return "Tarayici cihazi"


def trusted_device_is_active(expires_at: datetime | None, *, now: datetime | None = None) -> bool:
    """Return whether a remembered-device window is still active."""
    if expires_at is None:
        return False
    current = now or utc_now()
    return expires_at > current


async def fetch_trusted_device_record(
    conn: Any,
    cookie_value: str | None,
) -> dict[str, Any] | None:
    """Load the active trusted-device record addressed by the cookie."""
    parsed = parse_trusted_device_cookie(cookie_value)
    if parsed is None:
        return None
    selector, raw_token = parsed
    row = await conn.fetchrow(
        """
        SELECT
            d.id,
            d.admin_user_id,
            d.hotel_id,
            d.selector,
            d.token_hash,
            d.device_label,
            d.verification_preset,
            d.session_preset,
            d.last_verified_at,
            d.verification_expires_at,
            d.session_expires_at,
            d.last_seen_at,
            d.created_at,
            d.updated_at,
            u.username,
            u.display_name,
            u.role,
            u.department_code,
            u.totp_secret,
            u.is_active
        FROM admin_trusted_devices d
        JOIN admin_users u ON u.id = d.admin_user_id
        WHERE d.selector = $1
          AND d.revoked_at IS NULL
        """,
        selector,
    )
    if row is None:
        return None
    record = dict(row)
    if hash_trusted_device_token(raw_token) != str(record["token_hash"]):
        return None
    return record


async def upsert_trusted_device_record(
    conn: Any,
    *,
    admin_user: Mapping[str, object],
    request: Request,
    verification_preset: str,
    session_preset: str,
    existing_device_id: object | None = None,
) -> TrustedDeviceToken:
    """Create or rotate the remembered-device record for the current browser."""
    token = generate_trusted_device_token(
        verification_preset=verification_preset,
        session_preset=session_preset,
    )
    device_label = build_device_label(request)
    token_hash = hash_trusted_device_token(token.raw_token)
    now = utc_now()
    if existing_device_id is not None:
        await conn.execute(
            """
            UPDATE admin_trusted_devices
            SET selector = $1,
                token_hash = $2,
                device_label = $3,
                verification_preset = $4,
                session_preset = $5,
                last_verified_at = $6,
                verification_expires_at = $7,
                session_expires_at = $8,
                last_seen_at = $6,
                updated_at = $6
            WHERE id = $9
            """,
            token.selector,
            token_hash,
            device_label,
            verification_preset,
            session_preset,
            now,
            token.verification_expires_at,
            token.session_expires_at,
            existing_device_id,
        )
        return token

    await conn.execute(
        """
        INSERT INTO admin_trusted_devices (
            admin_user_id,
            hotel_id,
            selector,
            token_hash,
            device_label,
            verification_preset,
            session_preset,
            last_verified_at,
            verification_expires_at,
            session_expires_at,
            last_seen_at,
            created_at,
            updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $8, $8, $8)
        """,
        _require_int(admin_user["id"], "admin_user.id"),
        _require_int(admin_user["hotel_id"], "admin_user.hotel_id"),
        token.selector,
        token_hash,
        device_label,
        verification_preset,
        session_preset,
        now,
        token.verification_expires_at,
        token.session_expires_at,
    )
    return token


async def refresh_trusted_device_session(conn: Any, device_id: object, session_preset: str) -> datetime:
    """Slide the current remembered session window forward."""
    now = utc_now()
    session_expires_at = now + timedelta(seconds=resolve_session_seconds(session_preset))
    await conn.execute(
        """
        UPDATE admin_trusted_devices
        SET session_expires_at = $1,
            last_seen_at = $2,
            updated_at = $2
        WHERE id = $3
        """,
        session_expires_at,
        now,
        device_id,
    )
    return session_expires_at


async def expire_trusted_device_session(conn: Any, device_id: object) -> None:
    """End only the remembered session while keeping the device verified."""
    now = utc_now()
    await conn.execute(
        """
        UPDATE admin_trusted_devices
        SET session_expires_at = $1,
            updated_at = $1
        WHERE id = $2
        """,
        now,
        device_id,
    )


async def revoke_trusted_device_record(conn: Any, device_id: object) -> None:
    """Revoke the remembered-device record entirely."""
    now = utc_now()
    await conn.execute(
        """
        UPDATE admin_trusted_devices
        SET revoked_at = $1,
            session_expires_at = $1,
            verification_expires_at = $1,
            updated_at = $1
        WHERE id = $2
        """,
        now,
        device_id,
    )


def set_access_cookie(response: Response, access_token: str, *, max_age_seconds: int) -> None:
    """Persist the short-lived access token in an httpOnly cookie."""
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def set_csrf_cookie(response: Response, csrf_token: str, *, max_age_seconds: int) -> None:
    """Persist the CSRF token in a JS-readable cookie."""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age_seconds,
        httponly=False,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def clear_access_cookies(response: Response) -> None:
    """Clear access and CSRF cookies from the browser."""
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def set_trusted_device_cookie(response: Response, cookie_value: str, *, max_age_seconds: int) -> None:
    """Persist the remembered-device cookie."""
    response.set_cookie(
        key=TRUSTED_DEVICE_COOKIE_NAME,
        value=cookie_value,
        max_age=max_age_seconds,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def clear_trusted_device_cookie(response: Response) -> None:
    """Clear the remembered-device cookie."""
    response.delete_cookie(
        key=TRUSTED_DEVICE_COOKIE_NAME,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def _cookie_secure() -> bool:
    """Return whether auth cookies should be marked secure."""
    return settings.public_base_url.lower().startswith("https://")
