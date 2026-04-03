"""Unit tests for application startup dependency handling."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from velox import main


class _FakeRedis:
    """Minimal Redis client stub for startup tests."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = iter(responses)
        self.aclose = AsyncMock()

    async def ping(self) -> bool:
        response = next(self._responses)
        if isinstance(response, Exception):
            raise response
        return bool(response)

    async def get(self, _key: str) -> str | None:
        return "ai"


def _redis_factory(client: _FakeRedis):
    """Build a redis.from_url replacement for tests."""

    def factory(*_args: object, **_kwargs: object) -> _FakeRedis:
        return client

    return factory


def _build_request(*, accept: str) -> Request:
    """Create a minimal ASGI request for root route tests."""
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"accept", accept.encode("utf-8"))],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
    )


@pytest.mark.asyncio
async def test_connect_redis_with_retry_recovers_from_transient_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeRedis([ConnectionError("temporary"), True])
    sleep_mock = AsyncMock()

    monkeypatch.setattr(main.redis, "from_url", _redis_factory(client))
    monkeypatch.setattr(main.asyncio, "sleep", sleep_mock)

    result = await main._connect_redis_with_retry()

    assert result is client
    assert sleep_mock.await_args_list == [call(1)]
    client.aclose.assert_not_awaited()


@pytest.mark.asyncio
async def test_connect_redis_with_retry_degrades_after_exhausting_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeRedis(
        [
            ConnectionError("attempt-1"),
            ConnectionError("attempt-2"),
            ConnectionError("attempt-3"),
        ]
    )
    sleep_mock = AsyncMock()

    monkeypatch.setattr(main.redis, "from_url", _redis_factory(client))
    monkeypatch.setattr(main.asyncio, "sleep", sleep_mock)

    result = await main._connect_redis_with_retry()

    assert result is None
    assert sleep_mock.await_args_list == [call(1), call(3)]
    client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_root_redirects_html_clients_to_admin_panel() -> None:
    response = await main.root(_build_request(accept="text/html"))

    assert isinstance(response, RedirectResponse)
    assert response.headers["location"] == main.settings.admin_panel_path
    assert response.status_code == 307


@pytest.mark.asyncio
async def test_root_returns_json_for_api_clients() -> None:
    response = await main.root(_build_request(accept="application/json"))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert response.body == b'{"service":"velox","status":"running"}'


@pytest.mark.asyncio
async def test_lifespan_restores_operation_mode_from_redis_on_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = _FakeRedis([True])
    close_db_pool = AsyncMock()
    close_client = AsyncMock()

    class _FakeEscalationEngine:
        def load_matrix(self) -> None:
            return None

    class _FakeDispatcher:
        def registered_names(self) -> list[str]:
            return []

    async def _dummy_noshow_loop(_hotel_ids: list[int]) -> None:
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            raise

    monkeypatch.setattr(main, "init_db_pool", AsyncMock(return_value=object()))
    monkeypatch.setattr(main, "apply_pending_migrations", AsyncMock(return_value={"executed": []}))
    monkeypatch.setattr(main, "_connect_redis_with_retry", AsyncMock(return_value=redis_client))
    monkeypatch.setattr(main, "load_all_profiles", lambda: {})
    monkeypatch.setattr(main, "load_escalation_matrix", lambda: {})
    monkeypatch.setattr(main, "EscalationEngine", _FakeEscalationEngine)
    monkeypatch.setattr(main, "load_templates", lambda: [])
    monkeypatch.setattr(main, "initialize_tool_dispatcher", lambda: _FakeDispatcher())
    monkeypatch.setattr(main, "EventProcessor", lambda **_kwargs: object())
    monkeypatch.setattr(main, "_noshow_background_loop", _dummy_noshow_loop)
    monkeypatch.setattr(main.settings, "whatsapp_phone_number_id", "")
    monkeypatch.setattr(main.settings, "operation_mode", "test")
    monkeypatch.setattr(main, "close_db_pool", close_db_pool)
    monkeypatch.setattr(main, "close_elektraweb_client", close_client)
    monkeypatch.setattr(main, "close_whatsapp_client", close_client)
    monkeypatch.setattr(main, "close_llm_client", close_client)
    monkeypatch.setattr(main, "close_transcription_client", close_client)
    monkeypatch.setattr(main, "close_vision_client", close_client)

    async with main.lifespan(main.app):
        assert main.settings.operation_mode == "ai"

    redis_client.aclose.assert_awaited_once()
