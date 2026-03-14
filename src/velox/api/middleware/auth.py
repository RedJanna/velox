"""JWT authentication and role-based access control for admin routes."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from velox.config.constants import Role
from velox.config.settings import settings
from velox.utils.admin_security import ACCESS_COOKIE_NAME, CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SAFE_HTTP_METHODS


class TokenData(BaseModel):
    """Decoded JWT token payload."""

    user_id: int
    hotel_id: int
    username: str
    role: Role
    display_name: str | None = None


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
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)


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
        return TokenData(
            user_id=user_id,
            hotel_id=int(payload["hotel_id"]),
            username=str(payload["username"]),
            role=Role(payload["role"]),
            display_name=payload.get("display_name"),
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


def require_role(*allowed_roles: Role):
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


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "hotels:read",
        "hotels:write",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "tickets:write",
        "notification_phones:read",
        "notification_phones:write",
    },
    Role.SALES: {
        "hotels:read",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "notification_phones:read",
    },
    Role.OPS: {
        "hotels:read",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "tickets:write",
        "notification_phones:read",
        "notification_phones:write",
    },
    Role.CHEF: {
        "hotels:read",
        "holds:read",
        "holds:approve",
    },
}


def check_permission(user: TokenData, permission: str) -> None:
    """Raise 403 when role lacks requested permission."""
    if permission not in ROLE_PERMISSIONS.get(user.role, set()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' not granted to role '{user.role.value}'",
        )
