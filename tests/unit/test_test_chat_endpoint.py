"""Unit tests for Chat Lab send endpoint idempotency behavior."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException

from velox.api.routes import test_chat
from velox.core.chat_lab_attachments import ChatLabAttachmentError
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
    messages: list[Message] = []
    human_override = False

    @classmethod
    def reset(cls) -> None:
        cls.user_insert_count = 0
        cls.assistant_insert_count = 0
        cls.assistant_by_client_id = {}
        cls.last_update_state_kwargs = None
        cls.messages = []
        cls.human_override = False

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
        self.__class__.messages.append(msg.model_copy(deep=True))
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
        return [message.model_copy(deep=True) for message in self.__class__.messages[-count:]]

    async def update_state(self, **kwargs) -> None:
        self.__class__.last_update_state_kwargs = kwargs

    async def get_assistant_by_client_message_id(self, conversation_id, client_message_id: str) -> Message | None:
        _ = conversation_id
        return self.__class__.assistant_by_client_id.get(client_message_id)

    async def get_by_id(self, conversation_id) -> Conversation | None:
        _ = conversation_id
        return self.active_conversation

    async def update_message_internal_json(self, message_id, internal_json: dict[str, Any]) -> None:
        for message in self.__class__.messages:
            if message.id == message_id:
                message.internal_json = dict(internal_json)
                return

    async def set_human_override(self, conversation_id, enabled: bool) -> None:
        _ = conversation_id
        self.__class__.human_override = enabled

    async def get_human_override(self, conversation_id) -> bool:
        _ = conversation_id
        return bool(self.__class__.human_override)

    async def close(self, conversation_id) -> None:
        _ = conversation_id
        self.__class__.active_conversation.is_active = False
        self.__class__.human_override = False


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> int:
        existed = key in self.store
        self.store.pop(key, None)
        return 1 if existed else 0


def _request_with_db() -> SimpleNamespace:
    app = SimpleNamespace(state=SimpleNamespace(db_pool=object(), tool_dispatcher=None))
    return SimpleNamespace(app=app)


class _FakeAttachmentService:
    def __init__(self) -> None:
        self.resolve_calls: list[dict[str, Any]] = []
        self.attach_calls: list[dict[str, Any]] = []

    async def resolve_assets_for_message(self, *, hotel_id: int, attachment_ids: list[str]) -> list[Any]:
        self.resolve_calls.append({"hotel_id": hotel_id, "attachment_ids": list(attachment_ids)})
        return [
            SimpleNamespace(
                id="11111111-1111-1111-1111-111111111111",
                kind="image",
                mime_type="image/png",
                file_name="test-image.png",
                size_bytes=1024,
                sha256="a" * 64,
            )
        ]

    async def attach_assets_to_message(self, *, asset_ids: list[str], message_id: Any) -> None:
        self.attach_calls.append({"asset_ids": list(asset_ids), "message_id": message_id})


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

    assert first.user_message_id
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


@pytest.mark.asyncio
async def test_test_chat_passes_resolved_reply_context_to_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()
    prior_assistant = Message(
        id=uuid4(),
        conversation_id=_FakeRepository.conversation_id,
        role="assistant",
        content="Premium oda 220 EUR, deluxe oda 180 EUR.",
        created_at=datetime.now(UTC),
    )
    _FakeRepository.messages = [prior_assistant.model_copy(deep=True)]
    pipeline_kwargs: dict[str, Any] = {}

    async def _fake_pipeline(**kwargs) -> LLMResponse:
        pipeline_kwargs.update(kwargs)
        return LLMResponse(
            user_message="Premium odayi not ettim.",
            internal_json=InternalJSON(language="tr", intent="stay_booking_create", state="ASK_DATES"),
        )

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "_run_message_pipeline", _fake_pipeline)

    request = _request_with_db()
    body = test_chat.TestChatRequest(
        message="Bunu alalim",
        phone="test_user_123",
        client_message_id="cl_test_reply_001",
        reply_to_message_id=str(prior_assistant.id),
    )

    response = await test_chat.test_chat(body=body, request=request)

    reply_context = pipeline_kwargs.get("reply_context")
    assert isinstance(reply_context, dict)
    assert reply_context["present"] is True
    assert reply_context["resolved"] is True
    assert reply_context["reply_to_message_id"] == str(prior_assistant.id)
    assert reply_context["target_role"] == "assistant"
    assert "Premium oda" in reply_context["target_content"]
    assert response.user_message_id


@pytest.mark.asyncio
async def test_test_chat_handoff_activates_guard_and_finalize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()
    finalize_calls: list[dict[str, Any]] = []
    activate_calls: list[dict[str, Any]] = []

    class _FakeDispatcher:
        async def dispatch(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
            if tool_name == "handoff_create_ticket":
                return {"ticket_id": "T-001", "status": "OPEN"}
            if tool_name == "notify_send":
                return {"notification_id": "N-001", "status": "queued"}
            return {"status": "ok"}

    async def _fake_pipeline(**kwargs) -> LLMResponse:
        _ = kwargs
        return LLMResponse(
            user_message="Sizi canli temsilciye aktariyorum.",
            internal_json=InternalJSON(
                language="tr",
                intent="human_handoff",
                state="HANDOFF",
                handoff={"needed": True, "reason": "Guest requested live agent"},
                escalation={"level": "L2", "route_to_role": "ADMIN", "sla_hint": "medium"},
                risk_flags=["HUMAN_REQUEST"],
                next_step="Await human agent response",
            ),
        )

    async def _fake_activate(**kwargs) -> None:
        activate_calls.append(kwargs)
        await kwargs["conversation_repository"].set_human_override(kwargs["conversation"].id, True)

    async def _fake_finalize(**kwargs) -> None:
        finalize_calls.append(kwargs)

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "_run_message_pipeline", _fake_pipeline)
    monkeypatch.setattr(test_chat, "_activate_handoff_guard", _fake_activate)
    monkeypatch.setattr(test_chat, "_finalize_handoff_transition", _fake_finalize)

    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(db_pool=object(), tool_dispatcher=_FakeDispatcher(), redis=None),
        ),
    )
    body = test_chat.TestChatRequest(
        message="canli temsilci istiyorum",
        phone="test_user_123",
        client_message_id="cl_test_handoff_001",
    )

    response = await test_chat.test_chat(body=body, request=request)

    assert response.blocked is False
    assert _FakeRepository.human_override is True
    assert len(activate_calls) == 1
    assert len(finalize_calls) == 1
    assert response.internal_json["handoff_lock_activated"] is True


@pytest.mark.asyncio
async def test_test_chat_blocks_pipeline_when_human_override_is_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()
    _FakeRepository.human_override = True
    pipeline_calls = {"count": 0}

    async def _fake_pipeline(**kwargs) -> LLMResponse:
        _ = kwargs
        pipeline_calls["count"] += 1
        return LLMResponse(
            user_message="Bu cevap uretilmemeli.",
            internal_json=InternalJSON(language="tr", intent="other", state="GREETING"),
        )

    async def _fake_is_human_override_active(*args, **kwargs) -> bool:
        _ = (args, kwargs)
        return True

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "_run_message_pipeline", _fake_pipeline)
    monkeypatch.setattr(test_chat, "_is_human_override_active", _fake_is_human_override_active)

    request = _request_with_db()
    body = test_chat.TestChatRequest(
        message="hala orada misin",
        phone="test_user_123",
        client_message_id="cl_test_blocked_001",
    )

    response = await test_chat.test_chat(body=body, request=request)

    assert response.blocked is True
    assert response.block_reason == "human_override_active"
    assert response.assistant_message_id == ""
    assert pipeline_calls["count"] == 0
    assert _FakeRepository.assistant_insert_count == 0


@pytest.mark.asyncio
async def test_test_chat_reset_clears_human_override_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()
    redis = _FakeRedis()
    phone_hash = _FakeRepository.active_conversation.phone_hash
    redis.store[f"velox:human_override:{phone_hash}"] = "1"

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)

    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(db_pool=object(), redis=redis)),
    )

    result = await test_chat.test_chat_reset(request=request, phone="test_user_123")

    assert result["status"] == "reset"
    assert f"velox:human_override:{phone_hash}" not in redis.store


@pytest.mark.asyncio
async def test_test_chat_supports_attachment_only_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()
    attachment_service = _FakeAttachmentService()
    pipeline_inputs: list[str] = []

    async def _fake_pipeline(**kwargs) -> LLMResponse:
        pipeline_inputs.append(str(kwargs.get("normalized_text") or ""))
        return LLMResponse(
            user_message="Dosyanizi aldim.",
            internal_json=InternalJSON(language="tr", intent="other", state="GREETING"),
        )

    async def _fake_human_override(*_args, **_kwargs) -> bool:
        return False

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "_run_message_pipeline", _fake_pipeline)
    monkeypatch.setattr(test_chat, "_is_human_override_active", _fake_human_override)
    monkeypatch.setattr(test_chat, "attachment_service", attachment_service)

    request = _request_with_db()
    body = test_chat.TestChatRequest(
        message="",
        phone="test_user_123",
        client_message_id="cl_test_attachment_only_001",
        attachments=[{"asset_id": "11111111-1111-1111-1111-111111111111"}],
    )

    response = await test_chat.test_chat(body=body, request=request)

    assert response.user_message_id
    assert response.assistant_message_id
    assert pipeline_inputs
    assert "Kullanici dosya paylasti" in pipeline_inputs[0]
    assert _FakeRepository.messages
    first_user_message = _FakeRepository.messages[0]
    assert first_user_message.content.startswith("Ek gonderildi")
    assert isinstance(first_user_message.internal_json, dict)
    assert len(first_user_message.internal_json.get("attachments") or []) == 1
    assert attachment_service.attach_calls


@pytest.mark.asyncio
async def test_test_chat_returns_400_when_attachment_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeRepository.reset()

    class _FailingAttachmentService:
        async def resolve_assets_for_message(self, **_kwargs) -> list[Any]:
            raise ChatLabAttachmentError("Eklerden biri bulunamadi.")

    monkeypatch.setattr(test_chat, "ConversationRepository", _FakeRepository)
    monkeypatch.setattr(test_chat, "attachment_service", _FailingAttachmentService())

    request = _request_with_db()
    body = test_chat.TestChatRequest(
        message="Merhaba",
        phone="test_user_123",
        client_message_id="cl_test_attachment_error_001",
        attachments=[{"asset_id": "bad"}],
    )

    with pytest.raises(HTTPException) as exc_info:
        await test_chat.test_chat(body=body, request=request)

    assert exc_info.value.status_code == 400
    assert "Eklerden biri bulunamadi" in str(exc_info.value.detail)
