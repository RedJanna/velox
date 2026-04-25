"""Unit tests for optional browser screenshots in the admin debug runner."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI

from velox.config.settings import settings
from velox.core import admin_debug_runner
from velox.core.admin_debug_runner import _maybe_capture_browser_screenshot
from velox.core.admin_debug_scan_registry import ScanTarget
from velox.models.admin_debug import DebugRunMode, DebugRunResponse, DebugRunScope, DebugRunStatus, DebugRunSummary


def _build_run() -> DebugRunResponse:
    return DebugRunResponse(
        id=str(uuid4()),
        hotel_id=21966,
        triggered_by_user_id=7,
        mode=DebugRunMode.AGGRESSIVE_REPORT_ONLY,
        status=DebugRunStatus.RUNNING,
        scope=DebugRunScope(),
        summary=DebugRunSummary(),
        queued_at="2026-04-24T10:00:00+00:00",
        artifact_count=0,
        worker_meta={},
    )


def _build_target() -> ScanTarget:
    return ScanTarget(
        key="admin_shell",
        view_key="dashboard",
        screen="Admin Panel",
        path="/admin",
        response_type="html",
        performance_budget_ms=3000,
        expected_markers=("NexlumeAI Yönetim Paneli",),
    )


class _FakeRepository:
    def __init__(self) -> None:
        self.artifacts: list[dict[str, object]] = []

    async def append_artifact(self, **payload):
        self.artifacts.append(payload)
        return payload


class _ProcessRunRepository:
    def __init__(self) -> None:
        self.findings: list[dict[str, object]] = []
        self.summary: dict[str, int] | None = None

    async def append_finding(self, **payload):
        self.findings.append(payload)
        return payload

    async def mark_completed(self, *, run_id, hotel_id, summary_json):
        _ = (run_id, hotel_id)
        self.summary = summary_json


@pytest.mark.asyncio
async def test_browser_screenshot_skips_when_playwright_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    repository = _FakeRepository()
    session_value = "signed-token"

    def _raise_import_error(_name: str):
        raise ModuleNotFoundError("playwright not installed")

    monkeypatch.setattr(admin_debug_runner, "DEBUG_ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(admin_debug_runner.importlib, "import_module", _raise_import_error)

    await _maybe_capture_browser_screenshot(
        repository=repository,
        run=_build_run(),
        target=_build_target(),
        debug_session_token=session_value,
    )

    assert repository.artifacts == []


@pytest.mark.asyncio
async def test_browser_screenshot_writes_artifact_when_playwright_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    repository = _FakeRepository()
    run = _build_run()
    session_value = "signed-token"

    class _FakePage:
        async def goto(self, *_args, **_kwargs) -> None:
            return None

        async def wait_for_load_state(self, *_args, **_kwargs) -> None:
            return None

        async def wait_for_timeout(self, *_args, **_kwargs) -> None:
            return None

        async def screenshot(self, **_kwargs) -> bytes:
            return b"png-bytes"

    class _FakeContext:
        async def new_page(self) -> _FakePage:
            return _FakePage()

        async def close(self) -> None:
            return None

    class _FakeBrowser:
        async def new_context(self, **_kwargs) -> _FakeContext:
            return _FakeContext()

        async def close(self) -> None:
            return None

    class _FakeChromium:
        async def launch(self, **_kwargs) -> _FakeBrowser:
            return _FakeBrowser()

    class _FakePlaywrightManager:
        async def __aenter__(self):
            return SimpleNamespace(chromium=_FakeChromium())

        async def __aexit__(self, exc_type, exc, tb) -> None:
            _ = (exc_type, exc, tb)

    monkeypatch.setattr(admin_debug_runner, "DEBUG_ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(
        admin_debug_runner.importlib,
        "import_module",
        lambda _name: SimpleNamespace(async_playwright=lambda: _FakePlaywrightManager()),
    )

    await _maybe_capture_browser_screenshot(
        repository=repository,
        run=run,
        target=_build_target(),
        debug_session_token=session_value,
    )

    assert len(repository.artifacts) == 1
    artifact = repository.artifacts[0]
    assert artifact["mime_type"] == "image/png"
    assert artifact["artifact_type"].value == "screenshot"
    storage_path = str(artifact["storage_path"])
    assert (tmp_path / storage_path).read_bytes() == b"png-bytes"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "public_base_url", "app_port", "expected_base_url"),
    (
        ("public", "https://velox.nexlumeai.com/", 8001, "https://velox.nexlumeai.com"),
        ("internal", "https://velox.nexlumeai.com/", 9009, "http://127.0.0.1:9009"),
    ),
)
async def test_process_run_uses_configured_scan_base_url(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    public_base_url: str,
    app_port: int,
    expected_base_url: str,
) -> None:
    run = _build_run()
    repository = _ProcessRunRepository()
    captured: dict[str, str] = {}

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            _ = args
            captured["base_url"] = str(kwargs["base_url"])

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            _ = (exc_type, exc, tb)

    def _build_scan_targets(*_args, **_kwargs):
        return []

    monkeypatch.setattr(settings, "admin_debug_browser_target_mode", mode)
    monkeypatch.setattr(settings, "public_base_url", public_base_url)
    monkeypatch.setattr(settings, "app_port", app_port)
    monkeypatch.setattr(admin_debug_runner, "build_scan_targets", _build_scan_targets)
    monkeypatch.setattr(admin_debug_runner, "create_debug_session_token", lambda **_kwargs: "signed-token")
    monkeypatch.setattr(admin_debug_runner.httpx, "AsyncClient", _FakeAsyncClient)

    await admin_debug_runner._process_run(FastAPI(), repository, run)

    assert captured["base_url"] == expected_base_url
    assert repository.summary is not None
