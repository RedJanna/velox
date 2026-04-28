"""Admin user, role, department, and permission management routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import TokenData, check_permission, ensure_hotel_access, get_current_user
from velox.config.constants import Role
from velox.config.settings import settings
from velox.core.admin_access_control import (
    get_department_catalog,
    get_permission_catalog,
    get_role_catalog,
    is_super_admin_username,
    normalize_department_code,
    validate_permission_keys,
)
from velox.db.repositories.admin_access import (
    build_admin_user_response,
    clear_admin_user_permission_overrides,
    fetch_admin_user_for_hotel,
    list_admin_user_access,
    replace_admin_user_permission_overrides,
)
from velox.utils.passwords import ensure_password_within_bcrypt_limit, hash_password
from velox.utils.totp import build_otpauth_qr_svg_data_uri, build_otpauth_uri, generate_totp_secret

router = APIRouter(prefix="/admin", tags=["admin-access-control"])


class AdminUserCreateRequest(BaseModel):
    """Payload for creating one admin-panel user inside the current hotel."""

    username: str = Field(min_length=3, max_length=100)
    display_name: str | None = Field(default=None, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    role: Role
    department_code: str | None = Field(default=None, max_length=50)
    permissions: list[str] | None = None
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Trim usernames before persistence."""
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Username must contain at least 3 visible characters")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_byte_length(cls, value: str) -> str:
        """Enforce bcrypt byte-length limit to avoid runtime hashing errors."""
        return ensure_password_within_bcrypt_limit(value)

    @field_validator("role")
    @classmethod
    def reject_none_role(cls, value: Role) -> Role:
        """Keep the placeholder NONE role out of persisted admin users."""
        if value == Role.NONE:
            raise ValueError("Role.NONE cannot be assigned to an admin user")
        return value


class AdminUserUpdateRequest(BaseModel):
    """Mutable admin-user properties updated from the access-control UI."""

    display_name: str | None = Field(default=None, max_length=100)
    role: Role | None = None
    department_code: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_byte_length(cls, value: str | None) -> str | None:
        """Enforce bcrypt byte-length limit for optional password resets."""
        if value is None:
            return None
        return ensure_password_within_bcrypt_limit(value)

    @field_validator("role")
    @classmethod
    def reject_none_role(cls, value: Role | None) -> Role | None:
        """Keep the placeholder NONE role out of persisted admin users."""
        if value == Role.NONE:
            raise ValueError("Role.NONE cannot be assigned to an admin user")
        return value


class AdminUserPermissionRequest(BaseModel):
    """Final effective permission set selected in the toggle UI."""

    permissions: list[str] = Field(default_factory=list)


@router.get("/access-control/catalog")
async def get_access_control_catalog(
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return role, department, and permission metadata for the admin UI."""
    check_permission(user, "access_control:read")
    return {
        "roles": get_role_catalog(),
        "departments": get_department_catalog(),
        "permission_groups": get_permission_catalog(),
        "security_policy": {
            "two_factor_required": True,
            "trusted_device_enabled": True,
        },
    }


@router.get("/users")
async def list_admin_users(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """List admin users inside the caller's hotel boundary."""
    check_permission(user, "access_control:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        items = await list_admin_user_access(conn, user.hotel_id)
    return {
        "items": items,
        "total": len(items),
        "current_user_id": user.user_id,
        "hotel_id": user.hotel_id,
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    body: AdminUserCreateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create one hotel-scoped admin user and issue TOTP enrollment details."""
    check_permission(user, "access_control:write")
    department_code = normalize_department_code(body.department_code, role=body.role)
    desired_permissions = validate_permission_keys(body.permissions or [])
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        existing_user = await conn.fetchval("SELECT 1 FROM admin_users WHERE username = $1", body.username)
        if existing_user == 1:
            raise HTTPException(status_code=409, detail="Username already exists")

        totp_secret = generate_totp_secret()
        password_hash = hash_password(body.password)
        row = await conn.fetchrow(
            """
            INSERT INTO admin_users (
                hotel_id,
                username,
                password_hash,
                role,
                display_name,
                department_code,
                totp_secret,
                is_active,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now(), now())
            RETURNING id, hotel_id, username, password_hash, role, display_name, department_code, totp_secret, is_active, created_at, updated_at
            """,
            user.hotel_id,
            body.username,
            password_hash,
            body.role.value,
            body.display_name.strip() if body.display_name else None,
            department_code,
            totp_secret,
            body.is_active,
        )
        if row is None:
            raise HTTPException(status_code=500, detail="Admin user could not be created")

        permission_overrides = None
        if body.permissions is not None:
            permission_overrides = await replace_admin_user_permission_overrides(
                conn,
                admin_user_id=int(row["id"]),
                role=body.role,
                permissions=desired_permissions,
            )

    otpauth_uri = build_otpauth_uri(
        secret=totp_secret,
        account_name=body.username,
        issuer=settings.admin_totp_issuer,
    )
    return {
        "status": "created",
        "user": build_admin_user_response(row=dict(row), permission_overrides=permission_overrides),
        "totp_secret": totp_secret,
        "otpauth_uri": otpauth_uri,
        "otpauth_qr_svg_data_uri": build_otpauth_qr_svg_data_uri(otpauth_uri),
    }


@router.put("/users/{admin_user_id}")
async def update_admin_user(
    admin_user_id: int,
    body: AdminUserUpdateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update one admin user's role, department, password, or activation state."""
    check_permission(user, "access_control:write")
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        current_row = await fetch_admin_user_for_hotel(conn, admin_user_id, user.hotel_id)
        if current_row is None:
            raise HTTPException(status_code=404, detail="Admin user not found")

        next_role = body.role or Role(str(current_row["role"]))
        target_is_super_admin = is_super_admin_username(str(current_row["username"]))
        self_role_change = admin_user_id == user.user_id and next_role.value != str(current_row["role"])
        self_deactivate = admin_user_id == user.user_id and body.is_active is False
        super_admin_demote = target_is_super_admin and next_role != Role.ADMIN
        super_admin_deactivate = target_is_super_admin and body.is_active is False
        if self_role_change or self_deactivate:
            raise HTTPException(status_code=400, detail="Your own role or activation state cannot be changed from this flow")
        if super_admin_demote or super_admin_deactivate:
            raise HTTPException(status_code=400, detail="Protected super admin access cannot be reduced from this flow")

        next_department = normalize_department_code(
            body.department_code if "department_code" in payload else str(current_row.get("department_code") or ""),
            role=next_role,
        )
        if "display_name" in payload:
            next_display_name = body.display_name.strip() or None if body.display_name is not None else None
        else:
            next_display_name = current_row["display_name"]
        next_is_active = body.is_active if body.is_active is not None else bool(current_row["is_active"])
        next_password_hash = hash_password(body.new_password) if body.new_password else None

        await conn.execute(
            """
            UPDATE admin_users
            SET role = $1,
                display_name = $2,
                department_code = $3,
                is_active = $4,
                password_hash = COALESCE($5, password_hash),
                updated_at = now()
            WHERE id = $6 AND hotel_id = $7
            """,
            next_role.value,
            next_display_name,
            next_department,
            next_is_active,
            next_password_hash,
            admin_user_id,
            user.hotel_id,
        )

        if body.role is not None and body.role.value != str(current_row["role"]):
            await clear_admin_user_permission_overrides(conn, admin_user_id)

        updated_row = await fetch_admin_user_for_hotel(conn, admin_user_id, user.hotel_id)
        if updated_row is None:
            raise HTTPException(status_code=404, detail="Admin user not found")

    return {
        "status": "updated",
        "permissions_reset_to_role_defaults": body.role is not None and body.role.value != str(current_row["role"]),
        "user": build_admin_user_response(row=updated_row),
    }


@router.put("/users/{admin_user_id}/permissions")
async def update_admin_user_permissions(
    admin_user_id: int,
    body: AdminUserPermissionRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Replace one user's permission overrides from the toggle selection UI."""
    check_permission(user, "access_control:write")
    desired_permissions = validate_permission_keys(body.permissions)
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        current_row = await fetch_admin_user_for_hotel(conn, admin_user_id, user.hotel_id)
        if current_row is None:
            raise HTTPException(status_code=404, detail="Admin user not found")
        role = Role(str(current_row["role"]))
        if is_super_admin_username(str(current_row["username"])):
            await clear_admin_user_permission_overrides(conn, admin_user_id)
            return {
                "status": "updated",
                "user": build_admin_user_response(
                    row=current_row,
                    permission_overrides={},
                ),
            }
        if admin_user_id == user.user_id:
            raise HTTPException(status_code=400, detail="Your own permission set cannot be changed from this flow")
        permission_overrides = await replace_admin_user_permission_overrides(
            conn,
            admin_user_id=admin_user_id,
            role=role,
            permissions=desired_permissions,
        )
    return {
        "status": "updated",
        "user": build_admin_user_response(row=current_row, permission_overrides=permission_overrides),
    }


@router.post("/users/{admin_user_id}/rotate-totp")
async def rotate_admin_user_totp(
    admin_user_id: int,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Rotate one user's TOTP enrollment and revoke remembered-device sessions."""
    check_permission(user, "access_control:write")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        current_row = await fetch_admin_user_for_hotel(conn, admin_user_id, user.hotel_id)
        if current_row is None:
            raise HTTPException(status_code=404, detail="Admin user not found")
        ensure_hotel_access(user, current_row["hotel_id"])

        refreshed_secret = generate_totp_secret()
        await conn.execute(
            """
            UPDATE admin_users
            SET totp_secret = $1,
                updated_at = now()
            WHERE id = $2 AND hotel_id = $3
            """,
            refreshed_secret,
            admin_user_id,
            user.hotel_id,
        )
        await conn.execute(
            """
            UPDATE admin_trusted_devices
            SET revoked_at = now(),
                verification_expires_at = now(),
                session_expires_at = now(),
                updated_at = now()
            WHERE admin_user_id = $1
              AND revoked_at IS NULL
            """,
            admin_user_id,
        )
        updated_row = await fetch_admin_user_for_hotel(conn, admin_user_id, user.hotel_id)
        if updated_row is None:
            raise HTTPException(status_code=404, detail="Admin user not found")

    otpauth_uri = build_otpauth_uri(
        secret=refreshed_secret,
        account_name=str(updated_row["username"]),
        issuer=settings.admin_totp_issuer,
    )
    return {
        "status": "rotated",
        "user": build_admin_user_response(row=updated_row),
        "totp_secret": refreshed_secret,
        "otpauth_uri": otpauth_uri,
        "otpauth_qr_svg_data_uri": build_otpauth_qr_svg_data_uri(otpauth_uri),
    }
