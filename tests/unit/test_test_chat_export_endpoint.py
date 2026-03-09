"""Unit tests for test chat export endpoint function."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from velox.api.routes import test_chat
from velox.models.conversation import Conversation, Message


class _FakeRepository:
    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        _ = (hotel_id, phone_hash)
        return Conversation(
            id=uuid4(),
            hotel_id=21966,
            phone_hash="hash",
            phone_display="test_user_123",
            language="tr",
        )

    async def get_messages(self, conversation_id, limit: int = 500, offset: int = 0) -> list[Message]:
        _ = (conversation_id, limit, offset)
        return [
            Message(
                id=uuid4(),
                conversation_id=uuid4(),
                role="user",
                content="Merhaba",
                created_at=datetime(2026, 3, 9, 12, 0, tzinfo=UTC),
            )
        ]


class _NoConversationRepository(_FakeRepository):
    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        _ = (hotel_id, phone_hash)
        return None


def _request_with_db() -> SimpleNamespace:
    app = SimpleNamespace(state=SimpleNamespace(db_pool=object()))
    return SimpleNamespace(app=app)


@pytest.mark.asyncio
async def test_export_endpoint_returns_markdown_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    response = await test_chat.test_chat_export(
        request=_request_with_db(),
        phone="alpha",
        export_format="md",
    )

    assert response.status_code == 200
    assert response.media_type.startswith("text/markdown")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert b"# Test Konusma Transkripti" in response.body


@pytest.mark.asyncio
async def test_export_endpoint_without_active_conversation_raises_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_chat, "ConversationRepository", _NoConversationRepository)
    with pytest.raises(HTTPException) as exc:
        await test_chat.test_chat_export(
            request=_request_with_db(),
            phone="alpha",
            export_format="json",
        )
    assert exc.value.status_code == 404
    assert exc.value.detail == "No active conversation for this phone"
