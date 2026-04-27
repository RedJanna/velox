"""JWT authentication and role-based access control for admin routes."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from velox.api.middleware.debug_report_only import get_debug_session
from velox.config.constants import Role
from velox.config.settings import settings
from velox.core.admin_access_control import ROLE_PERMISSIONS, build_effective_permissions, default_department_for_role
from velox.db.repositories.admin_access import fetch_admin_access_context
from velox.utils.admin_security import ACCESS_COOKIE_NAME, CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SAFE_HTTP_METHODS


class TokenData(BaseModel):
    """Decoded JWT token payload."""

    user_id: int
    hotel_id: int
    username: str
    role: Role
    display_name: str | None = None
    department_code: str | None = None
    permissions: set[str] = Field(default_factory=set)
    debug_report_only: bool = False
    debug_run_id: str | None = None
    auth_source: str = "access_token"


class TokenResponse(BaseModel):
    """JWT token response for login endpoint."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    role: str
    hotel_id: int
    authentication_mode: str = "otp"
    trusted_device_enabled: bool = False
    verification_expires_at: datetime | None = None
    session_expires_at: datetime | None = None


def create_access_token(data: TokenData) -> str:
    """Create JWT access token with configured expiration."""
    issued_at = datetime.now(UTC)
    expire = issued_at + timedelta(minutes=settings.admin_jwt_expire_minutes)
    payload = {
        "sub": str(data.user_id),
        "hotel_id": data.hotel_id,
        "username": data.username,
        "role": data.role.value,
        "display_name": data.display_name,
        "exp": expire,
        "iat": issued_at,
    }
    return cast(str, jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm))


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenData:
    """Validate bearer token and return current user context."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    debug_session = get_debug_session(request)
    if debug_session is not None:
        return TokenData(
            user_id=debug_session.triggered_by_user_id,
            hotel_id=debug_session.hotel_id,
            username=debug_session.username,
            role=debug_session.role,
            display_name=debug_session.display_name,
            department_code=default_department_for_role(debug_session.role),
            permissions=build_effective_permissions(debug_session.role),
            debug_report_only=debug_session.report_only,
            debug_run_id=str(debug_session.run_id),
            auth_source="debug_session",
        )
    token = _extract_token(request, credentials)
    if token is None:
        raise credentials_exception
    if credentials is None and request.method.upper() not in SAFE_HTTP_METHODS:
        _validate_csrf(request)
    try:
        payload = jwt.decode(
            token,
            settings.admin_jwt_secret,
            algorithms=[settings.admin_jwt_algorithm],
        )
        user_id = int(payload.get("sub", 0))
        if user_id == 0:
            raise credentials_exception
        db = request.app.state.db_pool
        async with db.acquire() as conn:
            context = await fetch_admin_access_context(conn, user_id)
        if context is None:
            raise credentials_exception
        if not context.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        return TokenData(
            user_id=context.user_id,
            hotel_id=context.hotel_id,
            username=context.username,
            role=context.role,
            display_name=context.display_name,
            department_code=context.department_code,
            permissions=context.permissions,
            auth_source="bearer" if credentials is not None else "cookie",
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise credentials_exception from exc


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Prefer bearer auth headers, but fall back to the access cookie for the panel UI."""
    if credentials is not None:
        return credentials.credentials
    cookie_token = request.cookies.get(ACCESS_COOKIE_NAME, "").strip()
    return cookie_token or None


def _validate_csrf(request: Request) -> None:
    """Require a matching CSRF header for cookie-backed unsafe requests."""
    header_token = request.headers.get(CSRF_HEADER_NAME, "").strip()
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "").strip()
    if not header_token or not cookie_token or header_token != cookie_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def require_role(
    *allowed_roles: Role,
) -> Callable[..., Awaitable[TokenData]]:
    """Return dependency enforcing allowed roles."""

    async def role_checker(
        current_user: Annotated[TokenData, Depends(get_current_user)],
    ) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role.value}' not authorized. "
                    f"Required: {[role.value for role in allowed_roles]}"
                ),
            )
        return current_user

    return role_checker


def check_permission(user: TokenData, permission: str) -> None:
    """Raise 403 when role lacks requested permission."""
    effective_permissions = user.permissions or ROLE_PERMISSIONS.get(user.role, set())
    if permission not in effective_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' not granted to role '{user.role.value}'",
        )


def ensure_hotel_access(user: TokenData, hotel_id: int | object) -> int:
    """Enforce the hotel boundary for one admin request."""
    try:
        requested_hotel_id = int(hotel_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied") from exc
    if requested_hotel_id != user.hotel_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return requested_hotel_id


def resolve_hotel_scope(user: TokenData, requested_hotel_id: int | None) -> int:
    """Resolve optional hotel filters inside the user's hotel boundary."""
    if requested_hotel_id is None:
        return user.hotel_id
    return ensure_hotel_access(user, requested_hotel_id)
