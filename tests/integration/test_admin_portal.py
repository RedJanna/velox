"""Integration tests for admin bootstrap and login flows."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from velox.api.routes import admin, admin_portal
from velox.config.settings import settings
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
        if "FROM admin_users WHERE username = $1" in query:
            username = str(args[0])
            for item in self.admin_users:
                if item["username"] == username:
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
        raise AssertionError(f"Unsupported execute query: {query}")


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


@pytest.fixture
def admin_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    connection = _FakeConnection()
    app = FastAPI()
    app.state.db_pool = _FakePool(connection)
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(admin_portal.router, prefix="/api/v1")

    monkeypatch.setattr(settings, "admin_bootstrap_token", "bootstrap-secret")
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")
    monkeypatch.setattr(admin_portal.bcrypt, "hash", lambda password: f"hash::{password}")
    monkeypatch.setattr(admin.bcrypt, "verify", lambda password, hashed: hashed == f"hash::{password}")
    with TestClient(app) as client:
        yield client


def test_bootstrap_then_login_with_totp(admin_client: TestClient) -> None:
    status_response = admin_client.get("/api/v1/admin/bootstrap/status")

    assert status_response.status_code == 200
    assert status_response.json()["bootstrap_required"] is True

    bootstrap_response = admin_client.post(
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
    otp_code = generate_totp_code(bootstrap_payload["totp_secret"])

    login_response = admin_client.post(
        "/api/v1/admin/login",
        json={
            "username": "ops_admin",
            "password": "SuperSecure123!",
            "otp_code": otp_code,
        },
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    me_response = admin_client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "ADMIN"
    assert me_response.json()["hotel_id"] == 21966


def test_bootstrap_rejects_password_longer_than_bcrypt_limit(admin_client: TestClient) -> None:
    response = admin_client.post(
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
