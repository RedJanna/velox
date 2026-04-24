"""Helpers for signed admin debug sessions used by report-only scans."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from velox.config.constants import Role
from velox.config.settings import settings

DEBUG_SESSION_HEADER = "X-Velox-Debug-Session"
DEBUG_SESSION_USERNAME = "debug_runner"
DEBUG_SESSION_DISPLAY_NAME = "Debug Worker"
DEBUG_SESSION_TTL_MINUTES = 15


class AdminDebugSession(BaseModel):
    """Decoded report-only debug session payload."""

    run_id: UUID
    hotel_id: int
    triggered_by_user_id: int
    username: str = DEBUG_SESSION_USERNAME
    role: Role = Role.ADMIN
    display_name: str | None = DEBUG_SESSION_DISPLAY_NAME
    report_only: bool = True


def create_debug_session_token(
    *,
    run_id: UUID,
    hotel_id: int,
    triggered_by_user_id: int,
    expires_in_minutes: int = DEBUG_SESSION_TTL_MINUTES,
) -> str:
    """Create a short-lived signed token for one internal debug worker session."""
    issued_at = datetime.now(UTC)
    payload = {
        "sub": f"debug:{run_id}",
        "run_id": str(run_id),
        "hotel_id": hotel_id,
        "triggered_by_user_id": triggered_by_user_id,
        "username": DEBUG_SESSION_USERNAME,
        "role": Role.ADMIN.value,
        "display_name": DEBUG_SESSION_DISPLAY_NAME,
        "report_only": True,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=expires_in_minutes),
    }
    return str(jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm))


def decode_debug_session_token(token: str) -> AdminDebugSession:
    """Validate and decode one signed debug session token."""
    try:
        payload = jwt.decode(
            token,
            settings.admin_jwt_secret,
            algorithms=[settings.admin_jwt_algorithm],
        )
        return AdminDebugSession(
            run_id=UUID(str(payload["run_id"])),
            hotel_id=int(payload["hotel_id"]),
            triggered_by_user_id=int(payload["triggered_by_user_id"]),
            username=str(payload.get("username") or DEBUG_SESSION_USERNAME),
            role=Role(str(payload.get("role") or Role.ADMIN.value)),
            display_name=str(payload.get("display_name") or DEBUG_SESSION_DISPLAY_NAME),
            report_only=bool(payload.get("report_only", True)),
        )
    except (JWTError, KeyError, ValueError, TypeError) as exc:
        raise ValueError("Invalid debug session token.") from exc
