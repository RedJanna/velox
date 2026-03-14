"""Integration tests for admin notification phone endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from velox.api.middleware.auth import TokenData, create_access_token
from velox.api.routes import admin
from velox.config.constants import Role
from velox.config.settings import settings


@pytest.fixture
async def admin_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[httpx.AsyncClient]:
    app = FastAPI()
    app.include_router(admin.router, prefix="/api/v1")

    async def _list_active(_hotel_id: int) -> list[dict[str, object]]:
        return [{"phone": "+905300000001", "label": "Ops", "is_default": False, "active": True}]

    async def _add(_hotel_id: int, phone: str, label: str) -> dict[str, object]:
        return {"phone": phone, "label": label, "is_default": False, "active": True}

    async def _remove(_hotel_id: int, phone: str) -> bool:
        return phone == "+905300000001"

    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")
    monkeypatch.setattr(admin._notification_phone_repo, "list_active", _list_active)
    monkeypatch.setattr(admin._notification_phone_repo, "add", _add)
    monkeypatch.setattr(admin._notification_phone_repo, "remove", _remove)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver.local") as client:
        yield client


def _auth_header(*, role: Role) -> dict[str, str]:
    token = create_access_token(
        TokenData(
            user_id=1,
            hotel_id=21966,
            username="tester",
            role=role,
            display_name="Tester",
        )
    )
    return {"Authorization": f"Bearer {token}"}


async def test_notification_phones_list_allows_sales(admin_client: httpx.AsyncClient) -> None:
    response = await admin_client.get(
        "/api/v1/admin/notification-phones",
        headers=_auth_header(role=Role.SALES),
    )

    assert response.status_code == 200
    assert response.json()[0]["phone"] == "+905300000001"


async def test_notification_phones_add_forbidden_for_sales(admin_client: httpx.AsyncClient) -> None:
    response = await admin_client.post(
        "/api/v1/admin/notification-phones",
        json={"phone": "+905300000001", "label": "Ops"},
        headers=_auth_header(role=Role.SALES),
    )

    assert response.status_code == 403
    assert "notification_phones:write" in response.json()["detail"]


async def test_notification_phones_add_allows_ops(admin_client: httpx.AsyncClient) -> None:
    response = await admin_client.post(
        "/api/v1/admin/notification-phones",
        json={"phone": "+905300000001", "label": "Ops"},
        headers=_auth_header(role=Role.OPS),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["phone"] == "+905300000001"
    assert payload["active"] is True


async def test_notification_phones_returns_503_when_table_missing(
    admin_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _raise_undefined(_hotel_id: int) -> list[dict[str, object]]:
        raise admin.asyncpg.UndefinedTableError("notification_phones missing")

    monkeypatch.setattr(admin._notification_phone_repo, "list_active", _raise_undefined)

    response = await admin_client.get(
        "/api/v1/admin/notification-phones",
        headers=_auth_header(role=Role.ADMIN),
    )

    assert response.status_code == 503
    assert "Migration 004" in response.json()["detail"]
