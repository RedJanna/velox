"""Regression checks for Chat Lab live feed query options."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from velox.api.routes import test_chat


class _CapturePool:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.params: list[tuple[object, ...]] = []

    async def fetch(self, query: str, *params: object):
        self.queries.append(query)
        self.params.append(params)
        return []


def _request_with_pool(pool: _CapturePool) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=pool)))


@pytest.mark.asyncio
async def test_live_feed_filters_to_active_conversations_by_default() -> None:
    pool = _CapturePool()

    response = await test_chat.live_feed(request=_request_with_pool(pool), limit=15)

    assert response["conversations"] == []
    assert response["total"] == 0
    assert pool.params == [(15,)]
    assert "AND c.is_active = true" in pool.queries[0]


@pytest.mark.asyncio
async def test_live_feed_can_include_inactive_conversations() -> None:
    pool = _CapturePool()

    response = await test_chat.live_feed(
        request=_request_with_pool(pool),
        limit=15,
        include_inactive=True,
    )

    assert response["conversations"] == []
    assert response["total"] == 0
    assert pool.params == [(15,)]
    assert "AND c.is_active = true" not in pool.queries[0]
