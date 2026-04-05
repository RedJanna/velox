"""Unit tests for database startup retry behavior."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from velox.config.constants import ConversationState
from velox.db import database
from velox.db.repositories.conversation import ConversationRepository


@pytest.mark.asyncio
async def test_init_db_pool_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    pool = MagicMock()
    sleep_mock = AsyncMock()
    attempts = {"count": 0}

    async def fake_create_pool(**_: object) -> MagicMock:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise OSError("temporary db outage")
        return pool

    monkeypatch.setattr(database, "_pool", None)
    monkeypatch.setattr(database.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(database.asyncio, "sleep", sleep_mock)

    result = await database.init_db_pool()

    assert result is pool
    assert database._pool is pool
    assert attempts["count"] == 3
    assert sleep_mock.await_args_list == [call(1), call(3)]

    monkeypatch.setattr(database, "_pool", None)


@pytest.mark.asyncio
async def test_init_db_pool_raises_after_retry_budget_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_mock = AsyncMock()

    async def fake_create_pool(**_: object) -> MagicMock:
        raise ConnectionError("db unavailable")

    monkeypatch.setattr(database, "_pool", None)
    monkeypatch.setattr(database.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(database.asyncio, "sleep", sleep_mock)

    with pytest.raises(RuntimeError, match="Database dependency unavailable during startup."):
        await database.init_db_pool()

    assert sleep_mock.await_args_list == [call(1), call(3)]
    assert database._pool is None


def test_normalize_conversation_state_maps_legacy_values() -> None:
    """Legacy conversation state values should not break replay or admin reads."""
    assert (
        ConversationRepository._normalize_conversation_state("awaiting_request")
        == ConversationState.NEEDS_VERIFICATION.value
    )
    assert ConversationRepository._normalize_conversation_state("") == ConversationState.GREETING.value
    assert ConversationRepository._normalize_conversation_state("HANDOFF") == "HANDOFF"
