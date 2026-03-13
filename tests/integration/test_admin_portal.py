"""Integration tests for admin bootstrap and login flows."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from velox.api.routes import admin, admin_portal, admin_session
from velox.config.settings import settings
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

    async def fetchval(self, query: str, *args: object) -> object:
        if "SELECT COUNT(*) FROM admin_users" in query:
            return len(self.admin_users)
        if "SELECT 1 FROM hotels WHERE hotel_id = $1" in query:
            return 1 if any(item["hotel_id"] == int(args[0]) for item in self.hotels) else None
        if "SELECT 1 FROM admin_users WHERE username = $1" in query:
            return 1 if any(item["username"] == args[0] for item in self.admin_users) else None
        raise AssertionError(f"Unsupported fetchval query: {query}")

    async def fetch(self, query: str, *args: object) -> list[dict[str, object]]:
        _ = args
        if "FROM hotels ORDER BY hotel_id" in query:
            return self.hotels
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
                            "totp_secret": user["totp_secret"],
                            "is_active": user["is_active"],
                        }
            return None
        if "FROM admin_users WHERE username = $1" in query:
            username = str(args[0])
            for item in self.admin_users:
                if item["username"] == username:
                    return item
            return None
        if "FROM admin_users" in query and "WHERE id = $1" in query:
            target_id = int(args[0])
            for item in self.admin_users:
                if int(item["id"]) == target_id:
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
                    "totp_secret": str(args[5]),
                    "is_active": True,
                }
            )
            return "INSERT 0 1"
        if "UPDATE admin_users SET totp_secret = $1, password_hash = $2 WHERE id = $3" in query:
            target_id = int(args[2])
            for item in self.admin_users:
                if int(item["id"]) == target_id:
                    item["totp_secret"] = str(args[0])
                    item["password_hash"] = str(args[1])
                    return "UPDATE 1"
            return "UPDATE 0"
        if "UPDATE admin_users SET totp_secret = $1 WHERE id = $2" in query:
            target_id = int(args[1])
            for item in self.admin_users:
                if int(item["id"]) == target_id:
                    item["totp_secret"] = str(args[0])
                    return "UPDATE 1"
            return "UPDATE 0"
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
    app.include_router(admin_portal.router, prefix="/api/v1")
    app.include_router(admin_session.router, prefix="/api/v1")

    monkeypatch.setattr(settings, "admin_bootstrap_token", "bootstrap-secret")
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")
    monkeypatch.setattr(admin_portal.bcrypt, "hash", lambda password: f"hash::{password}")
    monkeypatch.setattr(admin.bcrypt, "verify", lambda password, hashed: hashed == f"hash::{password}")
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
