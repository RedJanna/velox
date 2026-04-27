"""Admin access-control repository helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from velox.config.constants import Role
from velox.core.admin_access_control import (
    build_effective_permissions,
    get_department_label,
    get_role_label,
    normalize_department_code,
    validate_permission_keys,
)


@dataclass(slots=True)
class AdminAccessContext:
    """Current admin identity and effective access context."""

    user_id: int
    hotel_id: int
    username: str
    role: Role
    display_name: str | None
    department_code: str
    is_active: bool
    permissions: set[str]
    permission_overrides: dict[str, bool]


def _build_department_code(raw_value: object, role: Role) -> str:
    """Normalize nullable DB values into one supported department code."""
    value = str(raw_value).strip() if raw_value is not None else ""
    return normalize_department_code(value or None, role=role)


async def _fetch_permission_overrides_for_users(
    conn: Any,
    admin_user_ids: Sequence[int],
) -> dict[int, dict[str, bool]]:
    """Load explicit allow/deny overrides keyed by admin_user_id."""
    if not admin_user_ids:
        return {}
    rows = await conn.fetch(
        """
        SELECT admin_user_id, permission_key, is_allowed
        FROM admin_user_permission_overrides
        WHERE admin_user_id = ANY($1::int[])
        ORDER BY admin_user_id, permission_key
        """,
        list(admin_user_ids),
    )
    overrides: dict[int, dict[str, bool]] = {}
    for row in rows:
        admin_user_id = int(row["admin_user_id"])
        overrides.setdefault(admin_user_id, {})[str(row["permission_key"])] = bool(row["is_allowed"])
    return overrides


async def fetch_admin_access_context(conn: Any, user_id: int) -> AdminAccessContext | None:
    """Load one admin user plus effective permissions."""
    row = await conn.fetchrow(
        """
        SELECT id, hotel_id, username, role, display_name, department_code, is_active
        FROM admin_users
        WHERE id = $1
        """,
        user_id,
    )
    if row is None:
        return None
    role = Role(str(row["role"]))
    overrides = (await _fetch_permission_overrides_for_users(conn, [user_id])).get(user_id, {})
    return AdminAccessContext(
        user_id=int(row["id"]),
        hotel_id=int(row["hotel_id"]),
        username=str(row["username"]),
        role=role,
        display_name=str(row["display_name"]) if row["display_name"] is not None else None,
        department_code=_build_department_code(row["department_code"], role),
        is_active=bool(row["is_active"]),
        permissions=build_effective_permissions(role, overrides),
        permission_overrides=overrides,
    )


async def fetch_admin_user_for_hotel(conn: Any, admin_user_id: int, hotel_id: int) -> dict[str, Any] | None:
    """Load one admin user inside the caller's hotel boundary."""
    row = await conn.fetchrow(
        """
        SELECT id, hotel_id, username, password_hash, role, display_name, department_code, totp_secret, is_active, created_at, updated_at
        FROM admin_users
        WHERE id = $1 AND hotel_id = $2
        """,
        admin_user_id,
        hotel_id,
    )
    return dict(row) if row is not None else None


async def list_admin_user_access(conn: Any, hotel_id: int) -> list[dict[str, Any]]:
    """List admin users for one hotel with effective permissions."""
    rows = await conn.fetch(
        """
        SELECT id, hotel_id, username, role, display_name, department_code, totp_secret, is_active, created_at, updated_at
        FROM admin_users
        WHERE hotel_id = $1
        ORDER BY
            CASE role
                WHEN 'ADMIN' THEN 0
                WHEN 'OPS' THEN 1
                WHEN 'SALES' THEN 2
                WHEN 'CHEF' THEN 3
                ELSE 9
            END,
            username ASC
        """,
        hotel_id,
    )
    admin_user_ids = [int(row["id"]) for row in rows]
    overrides_map = await _fetch_permission_overrides_for_users(conn, admin_user_ids)
    items: list[dict[str, Any]] = []
    for row in rows:
        role = Role(str(row["role"]))
        admin_user_id = int(row["id"])
        overrides = overrides_map.get(admin_user_id, {})
        department_code = _build_department_code(row["department_code"], role)
        items.append(
            {
                "user_id": admin_user_id,
                "hotel_id": int(row["hotel_id"]),
                "username": str(row["username"]),
                "display_name": str(row["display_name"]) if row["display_name"] is not None else None,
                "role": role.value,
                "role_label": get_role_label(role),
                "department_code": department_code,
                "department_label": get_department_label(department_code),
                "is_active": bool(row["is_active"]),
                "two_factor_required": True,
                "totp_enrolled": bool(str(row["totp_secret"] or "").strip()),
                "permissions": sorted(build_effective_permissions(role, overrides)),
                "permission_overrides": overrides,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
    return items


async def replace_admin_user_permission_overrides(
    conn: Any,
    *,
    admin_user_id: int,
    role: Role,
    permissions: set[str] | list[str],
) -> dict[str, bool]:
    """Persist only the permission differences from the role defaults."""
    desired_permissions = validate_permission_keys(permissions)
    default_permissions = build_effective_permissions(role)
    override_rows: list[tuple[str, bool]] = []
    for permission_key in sorted(desired_permissions | default_permissions):
        desired_allowed = permission_key in desired_permissions
        default_allowed = permission_key in default_permissions
        if desired_allowed != default_allowed:
            override_rows.append((permission_key, desired_allowed))

    await conn.execute("DELETE FROM admin_user_permission_overrides WHERE admin_user_id = $1", admin_user_id)
    persisted: dict[str, bool] = {}
    for permission_key, is_allowed in override_rows:
        await conn.execute(
            """
            INSERT INTO admin_user_permission_overrides (admin_user_id, permission_key, is_allowed, created_at, updated_at)
            VALUES ($1, $2, $3, now(), now())
            """,
            admin_user_id,
            permission_key,
            is_allowed,
        )
        persisted[permission_key] = is_allowed
    await conn.execute("UPDATE admin_users SET updated_at = now() WHERE id = $1", admin_user_id)
    return persisted


async def clear_admin_user_permission_overrides(conn: Any, admin_user_id: int) -> None:
    """Reset one user's permissions back to the role defaults."""
    await conn.execute("DELETE FROM admin_user_permission_overrides WHERE admin_user_id = $1", admin_user_id)
    await conn.execute("UPDATE admin_users SET updated_at = now() WHERE id = $1", admin_user_id)


def build_admin_user_response(
    *,
    row: dict[str, Any],
    permission_overrides: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Build one stable admin-user payload from a DB row."""
    role = Role(str(row["role"]))
    overrides = permission_overrides or {}
    department_code = _build_department_code(row.get("department_code"), role)
    return {
        "user_id": int(row["id"]),
        "hotel_id": int(row["hotel_id"]),
        "username": str(row["username"]),
        "display_name": str(row["display_name"]) if row.get("display_name") is not None else None,
        "role": role.value,
        "role_label": get_role_label(role),
        "department_code": department_code,
        "department_label": get_department_label(department_code),
        "is_active": bool(row["is_active"]),
        "two_factor_required": True,
        "totp_enrolled": bool(str(row.get("totp_secret") or "").strip()),
        "permissions": sorted(build_effective_permissions(role, overrides)),
        "permission_overrides": overrides,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }
