"""Unit tests for application startup dependency handling."""

from unittest.mock import AsyncMock, call

import pytest

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


def _redis_factory(client: _FakeRedis):
    """Build a redis.from_url replacement for tests."""

    def factory(*_args: object, **_kwargs: object) -> _FakeRedis:
        return client

    return factory


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
