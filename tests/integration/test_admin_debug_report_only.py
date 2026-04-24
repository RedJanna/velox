"""Integration tests for report-only admin debug auth and middleware."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import uuid4

import httpx
import pytest
from fastapi import Depends, FastAPI

from velox.api.middleware.auth import TokenData, require_role
from velox.api.middleware.debug_report_only import REPORT_ONLY_BLOCK_MESSAGE, ReportOnlyDebugMiddleware
from velox.config.constants import Role
from velox.config.settings import settings
from velox.utils.admin_debug_security import DEBUG_SESSION_HEADER, create_debug_session_token


@pytest.fixture
async def debug_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")

    app = FastAPI()
    app.add_middleware(ReportOnlyDebugMiddleware)

    @app.get("/protected")
    async def protected(
        user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    ) -> dict[str, object]:
        return {
            "hotel_id": user.hotel_id,
            "user_id": user.user_id,
            "debug_report_only": user.debug_report_only,
            "debug_run_id": user.debug_run_id,
            "auth_source": user.auth_source,
        }

    @app.post("/mutate")
    async def mutate(
        user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    ) -> dict[str, object]:
        return {"status": "ok", "user_id": user.user_id}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver.local") as client:
        yield client


def _debug_header() -> dict[str, str]:
    token = create_debug_session_token(
        run_id=uuid4(),
        hotel_id=21966,
        triggered_by_user_id=7,
    )
    return {DEBUG_SESSION_HEADER: token}


async def test_debug_session_allows_safe_get(debug_client: httpx.AsyncClient) -> None:
    response = await debug_client.get("/protected", headers=_debug_header())

    assert response.status_code == 200
    payload = response.json()
    assert payload["hotel_id"] == 21966
    assert payload["user_id"] == 7
    assert payload["debug_report_only"] is True
    assert payload["auth_source"] == "debug_session"
    assert payload["debug_run_id"]


async def test_debug_session_blocks_unsafe_mutation(debug_client: httpx.AsyncClient) -> None:
    response = await debug_client.post("/mutate", headers=_debug_header())

    assert response.status_code == 409
    assert response.json()["detail"] == REPORT_ONLY_BLOCK_MESSAGE


async def test_debug_session_rejects_invalid_token(debug_client: httpx.AsyncClient) -> None:
    response = await debug_client.get("/protected", headers={DEBUG_SESSION_HEADER: "invalid-token"})

    assert response.status_code == 401
    assert "Invalid debug session token" in response.json()["detail"]
