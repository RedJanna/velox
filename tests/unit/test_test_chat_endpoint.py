"""Unit tests for Chat Lab send endpoint idempotency behavior."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from velox.api.routes import test_chat
from velox.models.conversation import Conversation, InternalJSON, LLMResponse, Message


class _FakeRepository:
    conversation_id = uuid4()
    active_conversation = Conversation(
        id=conversation_id,
        hotel_id=21966,
        phone_hash="phone_hash",
        phone_display="test_user_123",
        language="tr",
    )
    user_insert_count = 0
    assistant_insert_count = 0
    assistant_by_client_id: dict[str, Message] = {}
    last_update_state_kwargs: dict[str, Any] | None = None

    @classmethod
    def reset(cls) -> None:
        cls.user_insert_count = 0
        cls.assistant_insert_count = 0
        cls.assistant_by_client_id = {}
        cls.last_update_state_kwargs = None

    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        _ = (hotel_id, phone_hash)
        return self.active_conversation

    async def create(self, conv: Conversation) -> Conversation:
        self.active_conversation = conv
        return conv

    async def update_language(self, conversation_id, language: str) -> None:
        _ = (conversation_id, language)

    async def add_message(self, msg: Message) -> Message:
        msg.id = uuid4()
        msg.created_at = datetime.now(UTC)
        if msg.role == "user":
            self.__class__.user_insert_count += 1
        if msg.role == "assistant":
            self.__class__.assistant_insert_count += 1
            client_message_id = str((msg.internal_json or {}).get("client_message_id") or "")
            if client_message_id:
                self.__class__.assistant_by_client_id[client_message_id] = msg
        return msg

    async def get_recent_messages(self, conversation_id, count: int = 20) -> list[Message]:
        _ = (conversation_id, count)
        return []

    async def update_state(self, **kwargs) -> None:
        self.__class__.last_update_state_kwargs = kwargs

    async def get_assistant_by_client_message_id(self, conversation_id, client_message_id: str) -> Message | None:
        _ = conversation_id
        return self.__class__.assistant_by_client_id.get(client_message_id)

    async def get_by_id(self, conversation_id) -> Conversation | None:
        _ = conversation_id
        return self.active_conversation


def _request_with_db() -> SimpleNamespace:
    app = SimpleNamespace(state=SimpleNamespace(db_pool=object(), tool_dispatcher=None))
    return SimpleNamespace(app=app)


@pytest.mark.asyncio
async def test_test_chat_deduplicates_by_client_message_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeRepository.reset()
    pipeline_calls = {"count": 0}

    async def _fake_pipeline(**kwargs) -> LLMResponse:
        _ = kwargs
        pipeline_calls["count"] += 1
        return LLMResponse(
            user_message="Merhaba, size yardimci olayim.",
            internal_json=InternalJSON(language="tr", intent="greeting", state="GREETING"),
        )

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "_run_message_pipeline", _fake_pipeline)

    request = _request_with_db()
    body = test_chat.TestChatRequest(
        message="Merhaba",
        phone="test_user_123",
        client_message_id="cl_test_001",
    )

    first = await test_chat.test_chat(body=body, request=request)
    second = await test_chat.test_chat(body=body, request=request)

    assert first.assistant_message_id == second.assistant_message_id
    assert pipeline_calls["count"] == 1
    assert _FakeRepository.user_insert_count == 1
    assert _FakeRepository.assistant_insert_count == 1


@pytest.mark.asyncio
async def test_test_chat_merges_entities_without_overwriting_with_nulls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()
    _FakeRepository.active_conversation = Conversation(
        id=_FakeRepository.conversation_id,
        hotel_id=21966,
        phone_hash="phone_hash",
        phone_display="test_user_123",
        language="tr",
        entities_json={"room_type_id": 3, "board_type_id": 2, "guest_name": "Deneme Denndim"},
    )

    async def _fake_pipeline(**kwargs) -> LLMResponse:
        _ = kwargs
        return LLMResponse(
            user_message="Onaya iletiyorum.",
            internal_json=InternalJSON(
                language="tr",
                intent="stay_booking_create",
                state="PENDING_APPROVAL",
                entities={
                    "room_type_id": None,
                    "board_type_id": None,
                    "guest_name": "  ",
                    "cancel_policy_type": "NON_REFUNDABLE",
                },
            ),
        )

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "_run_message_pipeline", _fake_pipeline)

    request = _request_with_db()
    body = test_chat.TestChatRequest(
        message="evet",
        phone="test_user_123",
        client_message_id="cl_test_merge_001",
    )
    _ = await test_chat.test_chat(body=body, request=request)

    assert _FakeRepository.last_update_state_kwargs is not None
    entities = _FakeRepository.last_update_state_kwargs.get("entities")
    assert isinstance(entities, dict)
    assert entities["room_type_id"] == 3
    assert entities["board_type_id"] == 2
    assert entities["guest_name"] == "Deneme Denndim"
    assert entities["cancel_policy_type"] == "NON_REFUNDABLE"
