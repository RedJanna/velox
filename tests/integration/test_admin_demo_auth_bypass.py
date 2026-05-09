"""Integration checks for the local demo admin auth bypass."""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from velox.api.middleware import auth
from velox.api.routes import admin_portal
from velox.config.settings import settings
from velox.utils.admin_security import ACCESS_COOKIE_NAME


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(admin_portal.router, prefix="/api/v1")
    return app


async def _get_admin_me(
    monkeypatch: pytest.MonkeyPatch,
    *,
    app_env: str = "development",
    operation_mode: str = "test",
    public_base_url: str = "http://127.0.0.1:8011",
    base_url: str = "http://127.0.0.1:8011",
) -> httpx.Response:
    monkeypatch.setattr(settings, "app_env", app_env)
    monkeypatch.setattr(settings, "operation_mode", operation_mode)
    monkeypatch.setattr(settings, "public_base_url", public_base_url)
    monkeypatch.setattr(auth, "get_all_profiles", lambda: {21966: object()})

    transport = httpx.ASGITransport(app=_build_app())
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        return await client.get("/api/v1/admin/me")


async def test_local_demo_admin_me_works_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    response = await _get_admin_me(monkeypatch)

    assert response.status_code == 200
    payload = response.json()
    assert payload["hotel_id"] == 21966
    assert payload["username"] == "local_demo_admin"
    assert payload["role"] == "ADMIN"
    assert payload["auth_source"] == auth.LOCAL_DEMO_AUTH_SOURCE
    assert payload["two_factor_required"] is False
    assert "dashboard:read" in payload["permissions"]


async def test_local_demo_admin_me_works_with_live_runtime_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    response = await _get_admin_me(
        monkeypatch,
        app_env="production",
        operation_mode="ai",
        public_base_url="https://velox.nexlumeai.com",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "local_demo_admin"
    assert payload["auth_source"] == auth.LOCAL_DEMO_AUTH_SOURCE


async def test_local_demo_admin_me_ignores_stale_access_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "operation_mode", "ai")
    monkeypatch.setattr(settings, "public_base_url", "https://velox.nexlumeai.com")
    monkeypatch.setattr(auth, "get_all_profiles", lambda: {21966: object()})

    transport = httpx.ASGITransport(app=_build_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8011") as client:
        client.cookies.set(ACCESS_COOKIE_NAME, "stale-token", domain="127.0.0.1")
        response = await client.get("/api/v1/admin/me")

    assert response.status_code == 200
    assert response.json()["auth_source"] == auth.LOCAL_DEMO_AUTH_SOURCE


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:8001",
        "http://localhost:8011",
        "http://192.168.1.20:8011",
        "https://velox.nexlumeai.com",
    ],
)
async def test_demo_admin_bypass_is_blocked_outside_canonical_local_url(
    monkeypatch: pytest.MonkeyPatch,
    base_url: str,
) -> None:
    response = await _get_admin_me(
        monkeypatch,
        app_env="production",
        operation_mode="ai",
        public_base_url="https://velox.nexlumeai.com",
        base_url=base_url,
    )

    assert response.status_code == 401
