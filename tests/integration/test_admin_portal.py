"""Integration tests for admin bootstrap and login flows."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from velox.api.routes import admin, admin_access_control, admin_portal, admin_session
from velox.config.settings import settings
from velox.core.admin_access_control import PERMISSION_CATALOG
from velox.utils.admin_security import ACCESS_COOKIE_NAME, CSRF_COOKIE_NAME, TRUSTED_DEVICE_COOKIE_NAME
from velox.utils.totp import generate_totp_code


class _AcquireContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.hotels = [{"hotel_id": 21966, "name": "Kassandra Oludeniz"}]
        self.admin_users: list[dict[str, object]] = []
        self.trusted_devices: list[dict[str, object]] = []
        self.permission_overrides: dict[int, dict[str, bool]] = {}

    async def fetchval(self, query: str, *args: object) -> object:
        if "SELECT COUNT(*) FROM admin_users" in query:
            return len(self.admin_users)
        if "SELECT 1 FROM hotels WHERE hotel_id = $1" in query:
            return 1 if any(item["hotel_id"] == int(args[0]) for item in self.hotels) else None
        if "SELECT 1 FROM admin_users WHERE username = $1" in query:
            return 1 if any(item["username"] == args[0] for item in self.admin_users) else None
        raise AssertionError(f"Unsupported fetchval query: {query}")

    async def fetch(self, query: str, *args: object) -> list[dict[str, object]]:
        if "FROM hotels ORDER BY hotel_id" in query:
            return self.hotels
        if "FROM admin_users" in query and "WHERE hotel_id = $1" in query:
            hotel_id = int(args[0])
            return [
                item
                for item in self.admin_users
                if int(item["hotel_id"]) == hotel_id
            ]
        if "FROM admin_user_permission_overrides" in query:
            user_ids = [int(item) for item in list(args[0])]
            items: list[dict[str, object]] = []
            for admin_user_id in user_ids:
                for permission_key, is_allowed in self.permission_overrides.get(admin_user_id, {}).items():
                    items.append(
                        {
                            "admin_user_id": admin_user_id,
                            "permission_key": permission_key,
                            "is_allowed": is_allowed,
                        }
                    )
            return items
        raise AssertionError(f"Unsupported fetch query: {query}")

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        if "FROM admin_trusted_devices d" in query:
            selector = str(args[0])
            for item in self.trusted_devices:
                if item["selector"] != selector or item.get("revoked_at") is not None:
                    continue
                for user in self.admin_users:
                    if int(user["id"]) == int(item["admin_user_id"]):
                        return {
                            **item,
                            "username": user["username"],
                            "display_name": user["display_name"],
                            "role": user["role"],
                            "department_code": user["department_code"],
                            "totp_secret": user["totp_secret"],
                            "is_active": user["is_active"],
                        }
            return None
        if "INSERT INTO admin_users" in query and "RETURNING" in query:
            row = {
                "id": len(self.admin_users) + 1,
                "hotel_id": int(args[0]),
                "username": str(args[1]),
                "password_hash": str(args[2]),
                "role": str(args[3]),
                "display_name": args[4],
                "department_code": str(args[5]),
                "totp_secret": str(args[6]),
                "is_active": bool(args[7]),
                "created_at": "now",
                "updated_at": "now",
            }
            self.admin_users.append(row)
            return row
        if "FROM admin_users WHERE username = $1" in query:
            username = str(args[0])
            for item in self.admin_users:
                if item["username"] == username:
                    return item
            return None
        if "FROM admin_users" in query and "WHERE id = $1" in query:
            target_id = int(args[0])
            for item in self.admin_users:
                if int(item["id"]) != target_id:
                    continue
                if len(args) > 1 and int(item["hotel_id"]) != int(args[1]):
                    continue
                return item
            return None
        raise AssertionError(f"Unsupported fetchrow query: {query}")

    async def execute(self, query: str, *args: object) -> str:
        if "INSERT INTO admin_users" in query:
            self.admin_users.append(
                {
                    "id": len(self.admin_users) + 1,
                    "hotel_id": int(args[0]),
                    "username": str(args[1]),
                    "password_hash": str(args[2]),
                    "role": str(args[3]),
                    "display_name": args[4],
                    "department_code": str(args[5]),
                    "totp_secret": str(args[6]),
                    "is_active": True,
                    "created_at": "now",
                    "updated_at": "now",
                }
            )
            return "INSERT 0 1"
        if "DELETE FROM admin_user_permission_overrides" in query:
            target_id = int(args[0])
            self.permission_overrides[target_id] = {}
            return "DELETE 0"
        if "INSERT INTO admin_user_permission_overrides" in query:
            target_id = int(args[0])
            self.permission_overrides.setdefault(target_id, {})[str(args[1])] = bool(args[2])
            return "INSERT 0 1"
        if "UPDATE admin_users SET updated_at = now() WHERE id = $1" in query:
            target_id = int(args[0])
            for item in self.admin_users:
                if int(item["id"]) == target_id:
                    item["updated_at"] = "now"
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_users" in query and "SET role = $1" in query:
            target_id = int(args[5])
            for item in self.admin_users:
                if int(item["id"]) == target_id and int(item["hotel_id"]) == int(args[6]):
                    item["role"] = str(args[0])
                    item["display_name"] = args[1]
                    item["department_code"] = str(args[2])
                    item["is_active"] = bool(args[3])
                    if args[4] is not None:
                        item["password_hash"] = str(args[4])
                    item["updated_at"] = "now"
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_users" in query and "SET totp_secret = $1," in query and "WHERE id = $2 AND hotel_id = $3" in query:
            target_id = int(args[1])
            for item in self.admin_users:
                if int(item["id"]) == target_id and int(item["hotel_id"]) == int(args[2]):
                    item["totp_secret"] = str(args[0])
                    item["updated_at"] = "now"
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_users SET totp_secret = $1, password_hash = $2 WHERE id = $3" in query:
            target_id = int(args[2])
            for item in self.admin_users:
                if int(item["id"]) == target_id:
                    item["totp_secret"] = str(args[0])
                    item["password_hash"] = str(args[1])
                    item["updated_at"] = "now"
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_users SET totp_secret = $1 WHERE id = $2" in query:
            target_id = int(args[1])
            for item in self.admin_users:
                if int(item["id"]) == target_id:
                    item["totp_secret"] = str(args[0])
                    item["updated_at"] = "now"
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_trusted_devices" in query and "SET revoked_at = now()" in query:
            target_id = int(args[0])
            for item in self.trusted_devices:
                if int(item["admin_user_id"]) == target_id and item.get("revoked_at") is None:
                    item["revoked_at"] = "now"
                    item["verification_expires_at"] = "now"
                    item["session_expires_at"] = "now"
                    item["updated_at"] = "now"
            return "UPDATE 1"
        if "INSERT INTO admin_trusted_devices" in query:
            self.trusted_devices.append(
                {
                    "id": f"td-{len(self.trusted_devices) + 1}",
                    "admin_user_id": int(args[0]),
                    "hotel_id": int(args[1]),
                    "selector": str(args[2]),
                    "token_hash": str(args[3]),
                    "device_label": str(args[4]),
                    "verification_preset": str(args[5]),
                    "session_preset": str(args[6]),
                    "last_verified_at": args[7],
                    "verification_expires_at": args[8],
                    "session_expires_at": args[9],
                    "last_seen_at": args[7],
                    "created_at": args[7],
                    "updated_at": args[7],
                    "revoked_at": None,
                }
            )
            return "INSERT 0 1"
        if "UPDATE admin_trusted_devices" in query and "SET selector = $1" in query:
            target_id = args[8]
            for item in self.trusted_devices:
                if item["id"] == target_id:
                    item["selector"] = str(args[0])
                    item["token_hash"] = str(args[1])
                    item["device_label"] = str(args[2])
                    item["verification_preset"] = str(args[3])
                    item["session_preset"] = str(args[4])
                    item["last_verified_at"] = args[5]
                    item["verification_expires_at"] = args[6]
                    item["session_expires_at"] = args[7]
                    item["last_seen_at"] = args[5]
                    item["updated_at"] = args[5]
                    return "UPDATE 1"
            return "UPDATE 0"
        if (
            "UPDATE admin_trusted_devices" in query
            and "SET session_expires_at = $1" in query
            and "last_seen_at = $2" in query
        ):
            target_id = args[2]
            for item in self.trusted_devices:
                if item["id"] == target_id:
                    item["session_expires_at"] = args[0]
                    item["last_seen_at"] = args[1]
                    item["updated_at"] = args[1]
                    return "UPDATE 1"
            return "UPDATE 0"
        if (
            "UPDATE admin_trusted_devices" in query
            and "SET session_expires_at = $1" in query
            and "updated_at = $1" in query
        ):
            target_id = args[1]
            for item in self.trusted_devices:
                if item["id"] == target_id:
                    item["session_expires_at"] = args[0]
                    item["updated_at"] = args[0]
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_trusted_devices" in query and "SET revoked_at = $1" in query:
            target_id = args[1]
            for item in self.trusted_devices:
                if item["id"] == target_id:
                    item["revoked_at"] = args[0]
                    item["session_expires_at"] = args[0]
                    item["verification_expires_at"] = args[0]
                    item["updated_at"] = args[0]
                    return "UPDATE 1"
            return "UPDATE 0"
        raise AssertionError(f"Unsupported execute query: {query}")


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


@pytest.fixture
async def admin_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[httpx.AsyncClient]:
    connection = _FakeConnection()
    app = FastAPI()
    app.state.db_pool = _FakePool(connection)
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(admin_access_control.router, prefix="/api/v1")
    app.include_router(admin_portal.router, prefix="/api/v1")
    app.include_router(admin_session.router, prefix="/api/v1")

    monkeypatch.setattr(settings, "admin_bootstrap_token", "bootstrap-secret")
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")
    monkeypatch.setattr(admin_portal, "hash_password", lambda password: f"hash::{password}")
    monkeypatch.setattr(admin, "verify_password", lambda password, hashed: hashed == f"hash::{password}")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver.local") as client:
        yield client


async def test_bootstrap_then_login_with_totp(admin_client: httpx.AsyncClient) -> None:
    status_response = await admin_client.get("/api/v1/admin/bootstrap/status")

    assert status_response.status_code == 200
    assert status_response.json()["bootstrap_required"] is True

    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_admin",
            "display_name": "Ops Admin",
            "password": "SuperSecure123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )

    assert bootstrap_response.status_code == 201
    bootstrap_payload = bootstrap_response.json()
    assert bootstrap_payload["otpauth_qr_svg_data_uri"].startswith("data:image/svg+xml;base64,")
    otp_code = generate_totp_code(bootstrap_payload["totp_secret"])

    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_admin",
            "password": "SuperSecure123!",
            "otp_code": otp_code,
        },
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    me_response = await admin_client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "ADMIN"
    assert me_response.json()["hotel_id"] == 21966


async def test_bootstrap_rejects_password_longer_than_bcrypt_limit(admin_client: httpx.AsyncClient) -> None:
    response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_admin_long_password",
            "display_name": "Ops Admin",
            "password": "A" * 73,
            "bootstrap_token": "bootstrap-secret",
        },
    )

    assert response.status_code == 422
    assert "72 bytes" in str(response.json())


async def test_recover_totp_and_login_with_new_password(admin_client: httpx.AsyncClient) -> None:
    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_admin_recovery",
            "display_name": "Ops Admin",
            "password": "BootstrapPass123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )
    assert bootstrap_response.status_code == 201

    recovery_response = await admin_client.post(
        "/api/v1/admin/bootstrap/recover-totp",
        json={
            "username": "ops_admin_recovery",
            "bootstrap_token": "bootstrap-secret",
            "new_password": "RecoveredPass123!",
        },
    )
    assert recovery_response.status_code == 200
    recovery_payload = recovery_response.json()
    assert recovery_payload["status"] == "updated"
    assert recovery_payload["otpauth_qr_svg_data_uri"].startswith("data:image/svg+xml;base64,")

    otp_code = generate_totp_code(recovery_payload["totp_secret"])
    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_admin_recovery",
            "password": "RecoveredPass123!",
            "otp_code": otp_code,
        },
    )
    assert login_response.status_code == 200


async def test_login_can_remember_device_and_skip_otp_after_logout(admin_client: httpx.AsyncClient) -> None:
    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_fast_login",
            "display_name": "Ops Fast Login",
            "password": "FastLoginPass123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )
    otp_code = generate_totp_code(bootstrap_response.json()["totp_secret"])

    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_fast_login",
            "password": "FastLoginPass123!",
            "otp_code": otp_code,
            "remember_device": True,
            "verification_preset": "24_hours",
            "session_preset": "8_hours",
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["trusted_device_enabled"] is True
    assert admin_client.cookies.get(TRUSTED_DEVICE_COOKIE_NAME)

    csrf_token = admin_client.cookies.get(CSRF_COOKIE_NAME)
    logout_response = await admin_client.post(
        "/api/v1/admin/logout",
        headers={"X-CSRF-Token": str(csrf_token)},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["trusted_device_retained"] is True

    relogin_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_fast_login",
            "password": "FastLoginPass123!",
        },
    )
    assert relogin_response.status_code == 200
    assert relogin_response.json()["authentication_mode"] == "trusted_device"


async def test_session_refresh_works_with_trusted_device_cookie(admin_client: httpx.AsyncClient) -> None:
    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_refresh",
            "display_name": "Ops Refresh",
            "password": "RefreshPass123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )
    otp_code = generate_totp_code(bootstrap_response.json()["totp_secret"])
    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_refresh",
            "password": "RefreshPass123!",
            "otp_code": otp_code,
            "remember_device": True,
            "verification_preset": "24_hours",
            "session_preset": "8_hours",
        },
    )
    assert login_response.status_code == 200

    admin_client.cookies.delete(ACCESS_COOKIE_NAME)
    admin_client.cookies.delete(CSRF_COOKIE_NAME)

    refresh_response = await admin_client.post("/api/v1/admin/session/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json()["authentication_mode"] == "session_refresh"

    me_response = await admin_client.get("/api/v1/admin/me")
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "ops_refresh"


async def test_access_control_catalog_is_available_for_bootstrapped_admin(admin_client: httpx.AsyncClient) -> None:
    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_catalog_admin",
            "display_name": "Ops Catalog Admin",
            "password": "CatalogPass123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )
    otp_code = generate_totp_code(bootstrap_response.json()["totp_secret"])
    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_catalog_admin",
            "password": "CatalogPass123!",
            "otp_code": otp_code,
        },
    )
    token = login_response.json()["access_token"]

    catalog_response = await admin_client.get(
        "/api/v1/admin/access-control/catalog",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert catalog_response.status_code == 200
    payload = catalog_response.json()
    assert payload["security_policy"]["two_factor_required"] is True
    assert any(item["code"] == "ADMIN" for item in payload["roles"])
    assert any(item["code"] == "FRONT_OFFICE" for item in payload["departments"])


async def test_admin_can_create_and_list_scoped_users(admin_client: httpx.AsyncClient) -> None:
    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "ops_user_admin",
            "display_name": "Ops User Admin",
            "password": "UserAdminPass123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )
    otp_code = generate_totp_code(bootstrap_response.json()["totp_secret"])
    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_user_admin",
            "password": "UserAdminPass123!",
            "otp_code": otp_code,
        },
    )
    token = login_response.json()["access_token"]

    create_response = await admin_client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "front.office.user",
            "display_name": "Front Office User",
            "password": "FrontOfficePass123!",
            "role": "OPS",
            "department_code": "FRONT_OFFICE",
            "permissions": [
                "dashboard:read",
                "holds:read",
                "holds:approve",
            ],
        },
    )

    assert create_response.status_code == 201
    create_payload = create_response.json()
    assert create_payload["user"]["role"] == "OPS"
    assert create_payload["user"]["department_code"] == "FRONT_OFFICE"
    assert create_payload["totp_secret"]

    list_response = await admin_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 2
    created_user = next(item for item in list_payload["items"] if item["username"] == "front.office.user")
    assert created_user["permissions"] == ["dashboard:read", "holds:approve", "holds:read"]


async def test_owner_super_admin_keeps_full_permissions_and_can_save_own_profile(
    admin_client: httpx.AsyncClient,
) -> None:
    bootstrap_response = await admin_client.post(
        "/api/v1/admin/bootstrap",
        json={
            "hotel_id": 21966,
            "username": "H893453klkads",
            "display_name": "Owner Super Admin",
            "password": "OwnerSuperPass123!",
            "bootstrap_token": "bootstrap-secret",
        },
    )
    otp_code = generate_totp_code(bootstrap_response.json()["totp_secret"])
    login_response = await admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "H893453klkads",
            "password": "OwnerSuperPass123!",
            "otp_code": otp_code,
        },
    )
    token = login_response.json()["access_token"]

    me_response = await admin_client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["is_super_admin"] is True
    assert set(me_response.json()["permissions"]) == set(PERMISSION_CATALOG)

    save_response = await admin_client.put(
        "/api/v1/admin/users/1",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Owner Super Admin Updated",
            "role": "ADMIN",
            "department_code": "MANAGEMENT",
            "is_active": True,
        },
    )
    assert save_response.status_code == 200
    assert save_response.json()["user"]["display_name"] == "Owner Super Admin Updated"

    permission_response = await admin_client.put(
        "/api/v1/admin/users/1/permissions",
        headers={"Authorization": f"Bearer {token}"},
        json={"permissions": []},
    )
    assert permission_response.status_code == 200
    assert permission_response.json()["user"]["is_super_admin"] is True
    assert set(permission_response.json()["user"]["permissions"]) == set(PERMISSION_CATALOG)
