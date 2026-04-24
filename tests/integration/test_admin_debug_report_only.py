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
from velox.api.routes import admin_debug
from velox.config.constants import Role
from velox.config.settings import settings
from velox.models.admin_debug import DebugRunListItem, DebugRunMode, DebugRunScope, DebugRunStatus, DebugRunSummary
from velox.models.admin_debug import DebugArtifactResponse, DebugArtifactType, DebugRunResponse
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


@pytest.fixture
async def debug_status_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")

    class _FakeRepository:
        async def list_runs(self, *, hotel_id: int, status=None, limit: int = 20, offset: int = 0):
            _ = (hotel_id, status, limit, offset)
            return [
                DebugRunListItem(
                    id="run-1",
                    hotel_id=21966,
                    triggered_by_user_id=7,
                    mode=DebugRunMode.AGGRESSIVE_REPORT_ONLY,
                    status=DebugRunStatus.RUNNING,
                    scope=DebugRunScope(),
                    summary=DebugRunSummary(),
                    queued_at="2026-04-24T10:00:00+00:00",
                )
            ]

    class _FakeTask:
        def done(self) -> bool:
            return False

    app = FastAPI()
    app.state.debug_runner_task = _FakeTask()
    app.dependency_overrides[admin_debug._repository] = lambda: _FakeRepository()
    app.include_router(admin_debug.router, prefix="/api/v1")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver.local") as client:
        yield client


def _admin_auth_header() -> dict[str, str]:
    from velox.api.middleware.auth import create_access_token

    token = create_access_token(
        TokenData(
            user_id=1,
            hotel_id=21966,
            username="tester",
            role=Role.ADMIN,
            display_name="Tester",
        )
    )
    return {"Authorization": f"Bearer {token}"}


async def test_debug_status_reports_worker_ready(debug_status_client: httpx.AsyncClient) -> None:
    response = await debug_status_client.get("/api/v1/admin/debug/status", headers=_admin_auth_header())

    assert response.status_code == 200
    payload = response.json()
    assert payload["worker_ready"] is True
    assert payload["active_run_id"] == "run-1"
    assert payload["active_run_status"] == "running"


def _make_run_response(run_id: str = "run-1") -> DebugRunResponse:
    return DebugRunResponse(
        id=run_id,
        hotel_id=21966,
        triggered_by_user_id=7,
        mode=DebugRunMode.AGGRESSIVE_REPORT_ONLY,
        status=DebugRunStatus.COMPLETED,
        scope=DebugRunScope(),
        summary=DebugRunSummary(),
        queued_at="2026-04-24T10:00:00+00:00",
        artifact_count=1,
        worker_meta={},
    )


@pytest.fixture
async def debug_artifact_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")
    monkeypatch.setattr(admin_debug, "_ARTIFACT_ROOT", tmp_path)

    artifact = DebugArtifactResponse(
        id="11111111-1111-1111-1111-111111111111",
        run_id="run-1",
        artifact_type=DebugArtifactType.SCREENSHOT,
        storage_path="run-1/screenshots/admin_shell.png",
        mime_type="image/png",
        created_at="2026-04-24T10:01:00+00:00",
        metadata={"screen": "Admin Panel"},
    )
    artifact_path = tmp_path / artifact.storage_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(b"fake-image-bytes")

    class _FakeRepository:
        async def get_run(self, *, run_id, hotel_id):
            _ = (run_id, hotel_id)
            return _make_run_response()

        async def list_artifacts_for_finding(self, *, run_id, hotel_id, finding_id):
            _ = (run_id, hotel_id, finding_id)
            return [artifact]

    app = FastAPI()
    app.dependency_overrides[admin_debug._repository] = lambda: _FakeRepository()
    app.include_router(admin_debug.router, prefix="/api/v1")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver.local") as client:
        yield client


async def test_debug_artifact_list_hydrates_content_url(debug_artifact_client: httpx.AsyncClient) -> None:
    response = await debug_artifact_client.get(
        "/api/v1/admin/debug/runs/11111111-1111-1111-1111-111111111111/artifacts",
        headers=_admin_auth_header(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["content_url"].endswith("/artifacts/11111111-1111-1111-1111-111111111111/content")


async def test_debug_artifact_content_serves_file(debug_artifact_client: httpx.AsyncClient) -> None:
    response = await debug_artifact_client.get(
        "/api/v1/admin/debug/runs/11111111-1111-1111-1111-111111111111/artifacts/11111111-1111-1111-1111-111111111111/content",
        headers=_admin_auth_header(),
    )

    assert response.status_code == 200
    assert response.content == b"fake-image-bytes"
    assert response.headers["content-type"].startswith("image/png")
