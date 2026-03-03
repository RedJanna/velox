"""Shared pytest fixtures for Velox tests."""

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from velox.models.escalation import EscalationMatrixEntry
from velox.models.hotel_profile import HotelProfile


class _AcquireContext:
    """Async context manager that yields a mocked DB connection."""

    def __init__(self, connection: AsyncMock) -> None:
        self._connection = connection

    async def __aenter__(self) -> AsyncMock:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database pool with acquire() async context manager."""
    connection = AsyncMock()
    pool = MagicMock()
    pool.acquire.return_value = _AcquireContext(connection)
    return pool


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client."""
    client = AsyncMock()
    client.ping.return_value = True
    return client


@pytest.fixture
def mock_elektraweb() -> AsyncMock:
    """Mock Elektraweb adapter with predefined async methods."""
    client = AsyncMock()
    client.get.return_value = {}
    client.post.return_value = {}
    client.put.return_value = {}
    return client


@pytest.fixture
def mock_whatsapp() -> AsyncMock:
    """Mock WhatsApp client."""
    client = AsyncMock()
    client.send_text_message.return_value = {"messages": [{"id": "wamid.1"}]}
    client.mark_as_read.return_value = None
    return client


@pytest.fixture
def mock_openai() -> AsyncMock:
    """Mock OpenAI client with chat.completions.create stub."""
    completions = SimpleNamespace(create=AsyncMock())
    chat = SimpleNamespace(completions=completions)
    client = AsyncMock()
    client.chat = chat
    return client


@pytest.fixture
def hotel_profile() -> HotelProfile:
    """Load Kassandra Oludeniz profile from YAML."""
    path = Path("data/hotel_profiles/kassandra_oludeniz.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return HotelProfile.model_validate(raw)


@pytest.fixture
def escalation_matrix() -> list[EscalationMatrixEntry]:
    """Load escalation matrix entries from YAML."""
    path = Path("data/escalation_matrix.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    return [EscalationMatrixEntry.model_validate(item) for item in raw]


@pytest.fixture
def reset_whatsapp_webhook_state() -> Iterator[None]:
    """Reset in-memory webhook dedupe/rate-limit state between tests."""
    from velox.api.routes import whatsapp_webhook

    whatsapp_webhook.deduplicator._entries.clear()
    whatsapp_webhook.phone_minute_limiter._events.clear()
    whatsapp_webhook.phone_hour_limiter._events.clear()
    whatsapp_webhook.ip_limiter._events.clear()
    yield
    whatsapp_webhook.deduplicator._entries.clear()
    whatsapp_webhook.phone_minute_limiter._events.clear()
    whatsapp_webhook.phone_hour_limiter._events.clear()
    whatsapp_webhook.ip_limiter._events.clear()
