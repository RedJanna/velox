"""JWT authentication and role-based access control for admin routes."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from velox.config.constants import Role
from velox.config.settings import settings


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
    token_type: str = "bearer"
    expires_in: int
    role: str
    hotel_id: int


def create_access_token(data: TokenData) -> str:
    """Create JWT access token with configured expiration."""
    issued_at = datetime.now(timezone.utc)
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


security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    """Validate bearer token and return current user context."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
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
    },
    Role.SALES: {
        "hotels:read",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
    },
    Role.OPS: {
        "hotels:read",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "tickets:write",
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
