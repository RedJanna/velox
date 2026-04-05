"""Integration tests for WhatsApp webhook routes."""

import time
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from velox.adapters.whatsapp.webhook import IncomingMessage
from velox.api.routes import whatsapp_webhook
from velox.config.constants import EscalationLevel, RestaurantReservationMode, Role
from velox.core.burst_buffer import AggregatedMessage
from velox.models.conversation import Conversation, InternalJSON, LLMResponse, Message
from velox.models.escalation import EscalationResult
from velox.models.media import AudioTranscriptionResult, InboundMediaItem


class _FakeHandoffConversationRepository:
    conversation_id = uuid4()
    active_conversation = Conversation(
        id=conversation_id,
        hotel_id=21966,
        phone_hash="phone_hash",
        phone_display="905551112233",
        language="tr",
    )
    human_override = False
    pipeline_calls = 0
    assistant_messages: list[Message] = []
    user_messages: list[Message] = []

    @classmethod
    def reset(cls) -> None:
        cls.conversation_id = uuid4()
        cls.active_conversation = Conversation(
            id=cls.conversation_id,
            hotel_id=21966,
            phone_hash="phone_hash",
            phone_display="905551112233",
            language="tr",
        )
        cls.human_override = False
        cls.pipeline_calls = 0
        cls.assistant_messages = []
        cls.user_messages = []

    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        _ = (hotel_id, phone_hash)
        return self.__class__.active_conversation

    async def create(self, conv: Conversation) -> Conversation:
        self.__class__.active_conversation = conv
        return conv

    async def update_language(self, conversation_id, language: str) -> None:
        _ = conversation_id
        self.__class__.active_conversation.language = language

    async def add_message(self, msg: Message) -> Message:
        msg.id = uuid4()
        if msg.role == "assistant":
            self.__class__.assistant_messages.append(msg)
        elif msg.role == "user":
            self.__class__.user_messages.append(msg)
        return msg

    async def get_recent_messages(self, conversation_id, count: int = 20) -> list[Message]:
        _ = conversation_id
        return (self.__class__.user_messages + self.__class__.assistant_messages)[-count:]

    async def update_state(self, **kwargs) -> None:
        state = kwargs.get("state")
        if state:
            self.__class__.active_conversation.current_state = state
        entities = kwargs.get("entities")
        if isinstance(entities, dict):
            self.__class__.active_conversation.entities_json = entities

    async def set_human_override(self, conversation_id, enabled: bool) -> None:
        _ = conversation_id
        self.__class__.human_override = enabled

    async def get_human_override(self, conversation_id) -> bool:
        _ = conversation_id
        return self.__class__.human_override

    async def get_by_whatsapp_message_id(self, conversation_id, whatsapp_message_id: str) -> Message | None:
        _ = conversation_id
        for message in reversed(self.__class__.assistant_messages + self.__class__.user_messages):
            internal = message.internal_json or {}
            if internal.get("whatsapp_message_id") == whatsapp_message_id:
                return message
            if internal.get("message_id") == whatsapp_message_id:
                return message
        return None


class _FakeConversationLifecycleRepository:
    def __init__(self, active_conversation: Conversation | None) -> None:
        self.active_conversation = active_conversation
        self.closed_ids: list[str] = []
        self.created_conversations: list[Conversation] = []

    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        _ = (hotel_id, phone_hash)
        return self.active_conversation

    async def close(self, conversation_id) -> None:
        self.closed_ids.append(str(conversation_id))

    async def create(self, conv: Conversation) -> Conversation:
        conv.id = uuid4()
        self.created_conversations.append(conv)
        return conv


@pytest.fixture
async def webhook_client(reset_whatsapp_webhook_state: None) -> httpx.AsyncClient:
    """Build lightweight app exposing only whatsapp webhook routes."""
    _ = reset_whatsapp_webhook_state
    app = FastAPI()
    app.include_router(whatsapp_webhook.router, prefix="/api/v1")
    app.state.tool_dispatcher = None
    app.state.escalation_engine = None
    app.state.db_pool = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_create_or_get_conversation_keeps_recent_active_conversation() -> None:
    incoming = IncomingMessage(
        message_id="m-recent",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=int(time.time()),
        message_type="text",
    )
    active = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        phone_display="905551112233",
        language="tr",
        last_message_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    repository = _FakeConversationLifecycleRepository(active_conversation=active)

    result = await whatsapp_webhook._create_or_get_conversation(repository, incoming, 21966)

    assert result.id == active.id
    assert repository.closed_ids == []
    assert repository.created_conversations == []


@pytest.mark.asyncio
async def test_create_or_get_conversation_resets_after_20_minutes_of_inactivity() -> None:
    incoming = IncomingMessage(
        message_id="m-stale",
        phone="905551112233",
        display_name="Guest",
        text="hello",
        timestamp=int(time.time()),
        message_type="text",
    )
    active = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        phone_display="905551112233",
        language="tr",
        last_message_at=datetime.now(UTC) - timedelta(minutes=21),
    )
    repository = _FakeConversationLifecycleRepository(active_conversation=active)

    result = await whatsapp_webhook._create_or_get_conversation(repository, incoming, 21966)

    assert repository.closed_ids == [str(active.id)]
    assert len(repository.created_conversations) == 1
    assert result.id != active.id
    assert result.hotel_id == 21966
    assert result.language == "en"


# ── Proactive idle-reset (background loop) tests ───────────────────────────


class _FakeIdleResetRepository:
    """Minimal fake that records close() calls and returns canned idle conversations."""

    def __init__(
        self,
        idle_conversations: list[Conversation] | None = None,
        warn_conversations: list[Conversation] | None = None,
    ) -> None:
        self._idle = idle_conversations or []
        self._warn = warn_conversations or []
        self.closed_ids: list[str] = []

    async def get_idle_after_assistant(self, idle_seconds: int) -> list[Conversation]:
        _ = idle_seconds
        return self._idle

    async def get_idle_after_assistant_in_range(
        self, min_idle_seconds: int, max_idle_seconds: int,
    ) -> list[Conversation]:
        _ = (min_idle_seconds, max_idle_seconds)
        return self._warn

    async def close(self, conversation_id) -> None:
        self.closed_ids.append(str(conversation_id))


class _FakeWhatsAppClient:
    """Captures send_text_message calls."""

    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []

    async def send_text_message(self, to: str, body: str, *, force: bool = False) -> dict:
        _ = force
        self.sent_messages.append((to, body))
        return {"messages": [{"id": "fake"}]}


@pytest.mark.asyncio
async def test_idle_reset_loop_closes_and_sends_farewell(monkeypatch: pytest.MonkeyPatch) -> None:
    """The proactive idle-reset loop should close conversations and send
    a farewell WhatsApp message to the customer."""
    from velox.core import conversation_idle_reset as idle_mod

    stale_conv = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash_idle",
        phone_display="905550001122",
        language="tr",
        last_message_at=datetime.now(UTC) - timedelta(minutes=25),
    )
    fake_repo = _FakeIdleResetRepository(idle_conversations=[stale_conv])
    fake_wa = _FakeWhatsAppClient()

    monkeypatch.setattr(idle_mod, "ConversationRepository", lambda: fake_repo)
    monkeypatch.setattr(idle_mod, "get_whatsapp_client", lambda: fake_wa)
    monkeypatch.setattr(idle_mod, "get_profile", lambda hid: None)  # use defaults

    call_count = 0

    async def _fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise asyncio.CancelledError

    import asyncio

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    idle_mod.clear_warned_ids()

    await idle_mod.run_idle_reset_loop()

    assert fake_repo.closed_ids == [str(stale_conv.id)]
    # Should have sent a farewell ("closed") message
    assert len(fake_wa.sent_messages) >= 1
    farewell_phone, farewell_body = fake_wa.sent_messages[-1]
    assert farewell_phone == "905550001122"
    assert "kapatılmıştır" in farewell_body.lower() or "closed" in farewell_body.lower()


@pytest.mark.asyncio
async def test_idle_reset_loop_sends_warning_before_close(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loop should send a warning message when the customer is approaching
    the idle timeout but hasn't reached it yet."""
    from velox.core import conversation_idle_reset as idle_mod

    warn_conv = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash_warn",
        phone_display="905559998877",
        language="tr",
        last_message_at=datetime.now(UTC) - timedelta(minutes=16),
    )
    fake_repo = _FakeIdleResetRepository(
        warn_conversations=[warn_conv],
        idle_conversations=[],
    )
    fake_wa = _FakeWhatsAppClient()

    monkeypatch.setattr(idle_mod, "ConversationRepository", lambda: fake_repo)
    monkeypatch.setattr(idle_mod, "get_whatsapp_client", lambda: fake_wa)
    monkeypatch.setattr(idle_mod, "get_profile", lambda hid: None)

    call_count = 0

    async def _fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise asyncio.CancelledError

    import asyncio

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    idle_mod.clear_warned_ids()

    await idle_mod.run_idle_reset_loop()

    # Should NOT have closed anything
    assert fake_repo.closed_ids == []
    # Should have sent a warning message
    assert len(fake_wa.sent_messages) == 1
    warn_phone, warn_body = fake_wa.sent_messages[0]
    assert warn_phone == "905559998877"
    assert "5 dakika" in warn_body or "5 minutes" in warn_body


@pytest.mark.asyncio
async def test_idle_reset_loop_skips_when_no_stale_conversations(monkeypatch: pytest.MonkeyPatch) -> None:
    """No conversations should be closed when there are no stale ones."""
    from velox.core import conversation_idle_reset as idle_mod

    fake_repo = _FakeIdleResetRepository()

    monkeypatch.setattr(idle_mod, "ConversationRepository", lambda: fake_repo)
    monkeypatch.setattr(idle_mod, "get_profile", lambda hid: None)

    call_count = 0

    async def _fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise asyncio.CancelledError

    import asyncio

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    idle_mod.clear_warned_ids()

    await idle_mod.run_idle_reset_loop()

    assert fake_repo.closed_ids == []


@pytest.mark.asyncio
async def test_idle_reset_disabled_per_hotel_skips_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    """When conversation_idle_reset.enabled=False for a hotel, no warning
    or close should happen."""
    from velox.core import conversation_idle_reset as idle_mod
    from velox.models.hotel_profile import ConversationIdleResetConfig, HotelProfile, LocalizedText

    stale_conv = Conversation(
        id=uuid4(),
        hotel_id=99999,
        phone_hash="hash_disabled",
        phone_display="905551234567",
        language="tr",
        last_message_at=datetime.now(UTC) - timedelta(minutes=25),
    )
    fake_repo = _FakeIdleResetRepository(idle_conversations=[stale_conv])
    fake_wa = _FakeWhatsAppClient()

    disabled_profile = HotelProfile(
        hotel_id=99999,
        hotel_name=LocalizedText(tr="Test Otel", en="Test Hotel"),
        conversation_idle_reset=ConversationIdleResetConfig(enabled=False),
    )
    monkeypatch.setattr(idle_mod, "ConversationRepository", lambda: fake_repo)
    monkeypatch.setattr(idle_mod, "get_whatsapp_client", lambda: fake_wa)
    monkeypatch.setattr(idle_mod, "get_profile", lambda hid: disabled_profile)

    call_count = 0

    async def _fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise asyncio.CancelledError

    import asyncio

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    idle_mod.clear_warned_ids()

    await idle_mod.run_idle_reset_loop()

    assert fake_repo.closed_ids == []
    assert fake_wa.sent_messages == []


@pytest.mark.asyncio
async def test_get_verification_correct_and_incorrect_tokens(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET verify endpoint should return challenge only for matching token."""
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "verify_token", "verify-123")
    ok = await webhook_client.get(
        "/api/v1/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-123", "hub.challenge": "abc"},
    )
    bad = await webhook_client.get(
        "/api/v1/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "abc"},
    )
    assert ok.status_code == 200
    assert ok.text == "abc"
    assert bad.status_code == 403


@pytest.mark.asyncio
async def test_post_with_valid_signature_message_accepted(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid signature and parsed message should return accepted status."""
    incoming = IncomingMessage(
        message_id="m-accepted",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=int(time.time()),
        message_type="text",
    )
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", lambda *_: incoming)
    monkeypatch.setattr(whatsapp_webhook, "_schedule_background_task", lambda *_args, **_kwargs: None)
    response = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


@pytest.mark.asyncio
async def test_post_routes_to_resolved_hotel_id(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolved hotel id should be forwarded to background message processor."""
    incoming = IncomingMessage(
        message_id="m-routed-hotel",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=int(time.time()),
        message_type="text",
        phone_number_id="pn_33469",
    )
    captured: dict[str, int] = {}

    async def _resolve_hotel(*_args: Any, **_kwargs: Any) -> int | None:
        return 33469

    def _capture_schedule(_tasks: Any, _incoming: Any, hotel_id: int, *_args: Any, **_kwargs: Any) -> None:
        captured["hotel_id"] = hotel_id

    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", lambda *_: incoming)
    monkeypatch.setattr(whatsapp_webhook, "_resolve_hotel_id_for_incoming", _resolve_hotel)
    monkeypatch.setattr(whatsapp_webhook, "_schedule_background_task", _capture_schedule)

    response = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    assert captured["hotel_id"] == 33469


@pytest.mark.asyncio
async def test_post_with_unmapped_destination_skips_background_processing(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unmapped destination number should not enter background processing pipeline."""
    incoming = IncomingMessage(
        message_id="m-unmapped-hotel",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=int(time.time()),
        message_type="text",
        phone_number_id="pn_unknown",
    )
    called = {"scheduled": False}

    async def _resolve_hotel(*_args: Any, **_kwargs: Any) -> int | None:
        return None

    def _capture_schedule(*_args: Any, **_kwargs: Any) -> None:
        called["scheduled"] = True

    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", lambda *_: incoming)
    monkeypatch.setattr(whatsapp_webhook, "_resolve_hotel_id_for_incoming", _resolve_hotel)
    monkeypatch.setattr(whatsapp_webhook, "_schedule_background_task", _capture_schedule)

    response = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert called["scheduled"] is False


@pytest.mark.asyncio
async def test_post_with_invalid_signature_returns_403(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid signature should be rejected before payload processing."""
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: False)
    response = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": []},
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_status_update_payload_returns_ok_without_processing(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Status payloads (no user message) should return ok."""
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", lambda *_: None)
    response = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_deduplication_of_repeated_webhooks(
    webhook_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated webhook with same message id should be ignored on second call."""
    incoming = IncomingMessage(
        message_id="m-dedupe-1",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=int(time.time()),
        message_type="text",
    )

    def _parse(_: dict[str, Any]) -> IncomingMessage:
        return incoming

    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", _parse)
    monkeypatch.setattr(whatsapp_webhook, "_schedule_background_task", lambda *_args, **_kwargs: None)

    first = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    second = await webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert first.status_code == 200
    assert first.json() == {"status": "accepted"}
    assert second.status_code == 200
    assert second.json() == {"status": "ok"}


def test_child_quote_mismatch_creates_manual_verification_response() -> None:
    """Child occupancy mismatch should force manual quote verification."""
    executed_calls = [
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-08-03","checkout_date":"2026-08-04","adults":2,"chd_count":1,"chd_ages":[7],"currency":"EUR"}',
            "result": '{"error":"CHILD_OCCUPANCY_UNVERIFIED: PMS quote did not reflect requested child occupancy.","tool":"booking_quote"}',
        }
    ]
    response = whatsapp_webhook._build_child_quote_handoff_response(21966, executed_calls)
    assert response.internal_json.state == "HANDOFF"
    assert response.internal_json.entities["chd_count"] == 1
    assert "Çocuklu konaklamalarda" in response.user_message


def test_child_quote_mismatch_over_capacity_requests_room_split(monkeypatch: pytest.MonkeyPatch) -> None:
    """Over-capacity mismatch should ask room split instead of immediate handoff."""
    profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(pms_room_type_id=396094, name=SimpleNamespace(tr="Deluxe"), max_pax=4),
            SimpleNamespace(pms_room_type_id=396096, name=SimpleNamespace(tr="Premium"), max_pax=4),
        ]
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    executed_calls = [
        {
            "name": "booking_availability",
            "result": '{"rows":[{"room_type_id":396094,"room_to_sell":2,"stop_sell":false},{"room_type_id":396096,"room_to_sell":1,"stop_sell":false}]}',
        },
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-08-20","checkout_date":"2026-08-22","adults":4,"chd_count":2,"chd_ages":[15,13],"currency":"EUR"}',
            "result": '{"error":"CHILD_OCCUPANCY_UNVERIFIED: PMS quote did not reflect requested child occupancy.","tool":"booking_quote"}',
        },
    ]

    response = whatsapp_webhook._build_child_quote_handoff_response(21966, executed_calls)
    assert response.internal_json.state == "NEEDS_VERIFICATION"
    assert response.internal_json.intent == "stay_availability"
    assert response.internal_json.handoff == {"needed": False, "reason": None}
    assert "2 oda" in response.user_message
    assert "Deluxe" in response.user_message
    assert "Premium" in response.user_message


def test_quote_notes_only_added_when_booking_quote_was_executed() -> None:
    """Policy notes should not be appended to non-price follow-up messages."""
    no_quote_calls = [{"name": "faq_lookup"}]
    with_quote_calls = [{"name": "booking_quote"}]

    assert whatsapp_webhook._executed_booking_quote(no_quote_calls) is False
    assert whatsapp_webhook._executed_booking_quote(with_quote_calls) is True


def test_turkish_child_bedding_reply_uses_expected_preference_prompt() -> None:
    """2-child bedding reply should ask preference without contradictory extra lines."""
    reply = whatsapp_webhook._build_turkish_child_bedding_reply(
        21966,
        {"adults": 2, "chd_count": 2, "chd_ages": [7, 4]},
    )
    assert (
        "2 çocuklu konaklamalarda oda tipine ve uygunluğa göre 2 ek yatak veya 1 ek yatak + 1 sofa hazırlanabilir."
        in reply
    )
    assert "Hangisini tercih edersiniz?" in reply
    assert "tek ek yatak bilgisi doğru değildir" not in reply


def test_stay_hold_submission_detects_embedded_approval_request_id() -> None:
    """stay_create_hold tool result should count as approval when id is present."""
    executed_calls = [
        {
            "name": "stay_create_hold",
            "result": {"stay_hold_id": "S_HOLD_9001", "approval_request_id": "APR_9001"},
        }
    ]
    assert whatsapp_webhook._executed_stay_hold_submission(executed_calls) is True


@pytest.mark.asyncio
async def test_run_message_pipeline_mirrors_native_executed_calls_into_internal_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validator/persistence should see the real executed tool calls even when content reports none."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Wifi bilgisi hazir.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"faq_info","state":"ANSWERED","entities":{},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"await_guest_reply"}',
            [
                {
                    "name": "faq_lookup",
                    "arguments": {"hotel_id": 21966, "query": "wifi"},
                    "result": {"answer": "Wifi ucretsiz."},
                }
            ],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Wifi var mi?",
        expected_language="tr",
    )

    assert result.internal_json.tool_calls == [
        {
            "name": "faq_lookup",
            "status": "executed",
            "arguments": {"hotel_id": 21966, "query": "wifi"},
            "result": {"answer": "Wifi ucretsiz."},
        }
    ]


def test_merge_entities_with_context_ignores_null_and_blank_values() -> None:
    """Entity merge should keep prior values when LLM outputs null/blank placeholders."""
    merged = whatsapp_webhook._merge_entities_with_context(
        {
            "room_type_id": 3,
            "board_type_id": 2,
            "guest_name": "Deneme Denndim",
        },
        {
            "room_type_id": None,
            "board_type_id": None,
            "guest_name": "  ",
            "cancel_policy_type": "NON_REFUNDABLE",
        },
    )
    assert merged["room_type_id"] == 3
    assert merged["board_type_id"] == 2
    assert merged["guest_name"] == "Deneme Denndim"
    assert merged["cancel_policy_type"] == "NON_REFUNDABLE"


@pytest.mark.asyncio
async def test_run_message_pipeline_auto_submits_hold_when_next_step_requires_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline should create hold via fallback when LLM misses explicit tool calls."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Rezervasyon talebinizi isleme aliyorum.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"stay_booking_create","state":"READY_FOR_TOOL","entities":'
            '{"checkin_date":"2026-10-01","checkout_date":"2026-10-02","adults":2,"chd_count":0,'
            '"chd_ages":[],"guest_name":"Deneme Denndim","phone":"+909304498453",'
            '"room_type_id":2,"board_type_id":2,"cancel_policy_type":"NON_REFUNDABLE",'
            '"currency":"EUR","nationality":"TR"},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"Create stay hold and request ADMIN approval"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "booking_quote":
                return {
                    "offers": [
                        {
                            "room_type_id": 396097,
                            "board_type_id": 2,
                            "rate_type_id": 24171,
                            "rate_code_id": 301001,
                            "price_agency_id": 11,
                            "currency_code": "EUR",
                            "price": "140",
                            "discounted_price": "140",
                            "rate_type": "Iptal Edilemez",
                            "cancel_possible": False,
                        }
                    ]
                }
            if name == "stay_create_hold":
                draft = kwargs.get("draft", {})
                assert draft.get("room_type_id") == 396097
                assert draft.get("cancel_policy_type") == "NON_REFUNDABLE"
                return {
                    "stay_hold_id": "S_HOLD_9001",
                    "status": "PENDING_APPROVAL",
                    "approval_request_id": "APR_9001",
                    "approval_status": "REQUESTED",
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(
                id=2,
                pms_room_type_id=396097,
                name=SimpleNamespace(tr="Superior", en="Superior"),
            )
        ],
        rate_mapping={},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Iptal edilemez secenegiyle devam edelim",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["booking_quote", "stay_create_hold"]
    assert result.internal_json.state == "PENDING_APPROVAL"
    assert result.internal_json.next_step == "await_admin_approval"
    assert "Rezervasyon talebinizi aldik" in result.user_message


@pytest.mark.asyncio
async def test_run_message_pipeline_auto_submit_uses_previous_entities_when_llm_returns_null_room_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback hold submission should use prior entity context when current turn nulls critical fields."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Talebinizi onaya iletiyorum.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"stay_booking_create","state":"PENDING_APPROVAL","entities":'
            '{"checkin_date":"2026-10-01","checkout_date":"2026-10-06","adults":2,"chd_count":0,'
            '"chd_ages":[],"guest_name":"Udeneme UUdeneme","phone":"+905304498453",'
            '"room_type_id":null,"board_type_id":null,"cancel_policy_type":"NON_REFUNDABLE",'
            '"currency":"EUR","nationality":"TR"},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"admin_approval_wait"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "booking_quote":
                return {
                    "offers": [
                        {
                            "room_type_id": 396096,
                            "board_type_id": 2,
                            "rate_type_id": 24171,
                            "rate_code_id": 301001,
                            "price_agency_id": 11,
                            "currency_code": "EUR",
                            "price": "700",
                            "discounted_price": "700",
                            "rate_type": "Iptal Edilemez",
                            "cancel_possible": False,
                        }
                    ]
                }
            if name == "stay_create_hold":
                draft = kwargs.get("draft", {})
                assert draft.get("room_type_id") == 396096
                assert draft.get("notes") == ""
                return {
                    "stay_hold_id": "S_HOLD_9901",
                    "status": "PENDING_APPROVAL",
                    "approval_request_id": "APR_9901",
                    "approval_status": "REQUESTED",
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(
                id=3,
                pms_room_type_id=396096,
                name=SimpleNamespace(tr="Premium", en="Premium"),
            )
        ],
        rate_mapping={},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        entities_json={
            "room_type_id": 3,
            "board_type_id": 2,
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-06",
            "adults": 2,
            "guest_name": "Udeneme UUdeneme",
            "phone": "+905304498453",
            "cancel_policy_type": "NON_REFUNDABLE",
            "currency": "EUR",
            "nationality": "TR",
            "chd_count": 0,
            "chd_ages": [],
        },
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="evet",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["booking_quote", "stay_create_hold"]
    assert result.internal_json.state == "PENDING_APPROVAL"
    assert result.internal_json.next_step == "await_admin_approval"


@pytest.mark.asyncio
async def test_run_message_pipeline_auto_submits_hold_when_pending_approval_admin_wait_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chat Lab style pending-approval next step should still trigger hold fallback."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Rezervasyon talebinizi onaya iletiyorum.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"stay_booking_create","state":"PENDING_APPROVAL","entities":'
            '{"checkin_date":"2026-10-01","checkout_date":"2026-10-02","adults":2,"chd_count":0,'
            '"chd_ages":[],"guest_name":"Deneme Denndim","phone":"+909304498453",'
            '"room_type_id":2,"board_type_id":2,"cancel_policy_type":"FREE_CANCEL",'
            '"currency":"EUR","nationality":"TR"},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"admin_approval_wait"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "booking_quote":
                return {
                    "offers": [
                        {
                            "room_type_id": 396097,
                            "board_type_id": 2,
                            "rate_type_id": 24170,
                            "rate_code_id": 301001,
                            "price_agency_id": 11,
                            "currency_code": "EUR",
                            "price": "140",
                            "discounted_price": "140",
                            "rate_type": "Ucretsiz Iptal",
                            "cancel_possible": True,
                        }
                    ]
                }
            if name == "stay_create_hold":
                return {
                    "stay_hold_id": "S_HOLD_9002",
                    "status": "PENDING_APPROVAL",
                    "approval_request_id": "APR_9002",
                    "approval_status": "REQUESTED",
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(
                id=2,
                pms_room_type_id=396097,
                name=SimpleNamespace(tr="Superior", en="Superior"),
            )
        ],
        rate_mapping={},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="tamam onaya iletebiliriz",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["booking_quote", "stay_create_hold"]
    assert result.internal_json.state == "PENDING_APPROVAL"
    assert result.internal_json.next_step == "await_admin_approval"


@pytest.mark.asyncio
async def test_run_message_pipeline_auto_submits_hold_when_embedded_tool_calls_only_exist_in_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HAR-style free-text admin approval next step should still create the real hold."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Tesekkur ederiz.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"stay_booking_create","state":"PENDING_APPROVAL","entities":'
            '{"checkin_date":"2026-10-01","checkout_date":"2026-10-02","adults":2,"chd_count":0,'
            '"chd_ages":[],"room_type_id":2,"board_type_id":2,"currency":"EUR",'
            '"cancel_policy_type":"NON_REFUNDABLE","guest_name":"Deneme Denndim",'
            '"phone":"+905304498453","nationality":"TR"},'
            '"required_questions":[],"tool_calls":[{"name":"stay_create_hold","status":"called"},'
            '{"name":"approval_request","status":"called"}],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"Admin approval bekleniyor; onay sonrasi NON_REFUNDABLE icin '
            'payment_request_prepayment(NOW) tetiklenecek."}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "booking_quote":
                return {
                    "offers": [
                        {
                            "room_type_id": 396097,
                            "board_type_id": 2,
                            "rate_type_id": 24171,
                            "rate_code_id": 301001,
                            "price_agency_id": 11,
                            "currency_code": "EUR",
                            "price": "140",
                            "discounted_price": "140",
                            "rate_type": "Iptal Edilemez",
                            "cancel_possible": False,
                        }
                    ]
                }
            if name == "stay_create_hold":
                return {
                    "stay_hold_id": "S_HOLD_9003",
                    "status": "PENDING_APPROVAL",
                    "approval_request_id": "APR_9003",
                    "approval_status": "REQUESTED",
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(
                id=2,
                pms_room_type_id=396097,
                name=SimpleNamespace(tr="Superior", en="Superior"),
            )
        ],
        rate_mapping={},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="evet",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["booking_quote", "stay_create_hold"]
    assert dispatcher.calls[1][1]["conversation_id"] == str(conversation.id)
    assert result.internal_json.state == "PENDING_APPROVAL"
    assert result.internal_json.next_step == "await_admin_approval"


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_single_area_prompt_is_suppressed_and_auto_submitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Single-area restaurant profiles should not block on indoor/outdoor confirmation."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Iciniz mi disiniz mi tercih edersiniz?\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":'
            '{"date":"2026-08-10","time":"20:00","party_size":4,"guest_name":"Ali Veli","phone":"+905551112233"},'
            '"required_questions":["area"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"collect_restaurant_area"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "restaurant_availability":
                assert kwargs["area"] == "outdoor"
                return {
                    "available": True,
                    "options": [{"slot_id": "42", "time": "20:00:00", "area": "outdoor"}],
                }
            if name == "restaurant_create_hold":
                assert kwargs["area"] == "outdoor"
                return {
                    "restaurant_hold_id": "R_HOLD_9001",
                    "status": "PENDING_APPROVAL",
                    "approval_request_id": "APR_R_9001",
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        restaurant=SimpleNamespace(area_types=["outdoor"], hours={"dinner": "19:00-23:00"}),
        season={"open": "04-20", "close": "10-31"},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="devam edelim",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["restaurant_availability", "restaurant_create_hold"]
    assert result.internal_json.state == "PENDING_APPROVAL"
    assert result.internal_json.next_step == "await_admin_approval"
    assert result.internal_json.entities["area"] == "outdoor"
    assert "Restoran rezervasyon talebinizi aldik" in result.user_message
    assert [item["name"] for item in result.internal_json.tool_calls] == [
        "restaurant_availability",
        "restaurant_create_hold",
        "approval_request",
    ]


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_auto_submit_sets_confirmed_when_hold_is_finalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restaurant fallback should finalize the state when create_hold returns confirmed status."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Rezervasyon talebinizi onayliyorum.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_CONFIRMATION","entities":'
            '{"date":"2026-08-10","time":"20:00","party_size":2,"guest_name":"Ayse Kaya","phone":"+905551110000"},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"await_tool_result"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "restaurant_availability":
                return {
                    "available": True,
                    "options": [{"slot_id": "84", "time": "20:00:00", "area": "outdoor"}],
                }
            if name == "restaurant_create_hold":
                return {
                    "restaurant_hold_id": "R_HOLD_9010",
                    "status": "ONAYLANDI",
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        restaurant=SimpleNamespace(area_types=["outdoor"], hours={"dinner": "19:00-23:00"}),
        season={"open": "04-20", "close": "10-31"},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="evet",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["restaurant_availability", "restaurant_create_hold"]
    assert result.internal_json.state == "CONFIRMED"
    assert result.internal_json.next_step == "reservation_confirmed"
    assert "Restoran rezervasyonunuz onaylandi" in result.user_message


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_auto_submit_returns_deterministic_out_of_season_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Out-of-season restaurant fallback should ask for a new date instead of pretending success."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Restoran rezervasyonunuzu olusturuyorum.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"restaurant_booking_create","state":"READY_FOR_TOOL","entities":'
            '{"date":"2026-04-01","time":"20:00","party_size":4,"guest_name":"Ali Veli","phone":"+905551112233"},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"run_restaurant_availability"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "restaurant_availability":
                return {
                    "available": False,
                    "reason": "OUT_OF_SEASON",
                    "options": [],
                    "season": {"open": "04-20", "close": "10-31"},
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        restaurant=SimpleNamespace(area_types=["outdoor"], hours={"dinner": "19:00-23:00"}),
        season={"open": "04-20", "close": "10-31"},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 Nisan icin 4 kisilik restoran rezervasyonu olusturalim",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["restaurant_availability"]
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["date"]
    assert result.internal_json.handoff["needed"] is False
    assert "sezon disinda" in result.user_message.casefold()
    assert "20 Nisan" in result.user_message


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_real_conversation_regression_does_not_block_on_area_before_out_of_season_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Single-area restaurant flow should skip area question and immediately surface season rejection."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Ic mekan mi dis mekan mi tercih edersiniz?\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":'
            '{"date":"2026-04-01","time":"20:00","party_size":4,"guest_name":"Ali Veli","phone":"+905551112233"},'
            '"required_questions":["area"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"collect_restaurant_area"}',
            [],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "restaurant_availability":
                assert kwargs["area"] == "outdoor"
                return {
                    "available": False,
                    "reason": "OUT_OF_SEASON",
                    "options": [],
                    "season": {"open": "04-20", "close": "10-31"},
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        restaurant=SimpleNamespace(area_types=["outdoor"], hours={"dinner": "19:00-23:00"}),
        season={"open": "04-20", "close": "10-31"},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 Nisan icin 4 kisilik restoran rezervasyonu istiyorum",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert [item[0] for item in dispatcher.calls] == ["restaurant_availability"]
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["date"]
    assert result.internal_json.entities["area"] == "outdoor"
    assert "sezon disinda" in result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_stay_out_of_season_returns_deterministic_date_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stay season rejections should explain the season window and request another date."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Tarihinizi kontrol ediyorum.",
            [
                {
                    "name": "booking_availability",
                    "arguments": {
                        "hotel_id": 21966,
                        "checkin_date": "2026-04-01",
                        "checkout_date": "2026-04-03",
                        "adults": 2,
                    },
                    "result": {
                        "available": False,
                        "reason": "OUT_OF_SEASON",
                        "season": {"open": "04-20", "close": "10-31"},
                    },
                }
            ],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(season={"open": "04-20", "close": "10-31"})
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 Nisan - 3 Nisan icin oda ayirabilir misiniz?",
        dispatcher=None,
        expected_language="tr",
    )

    assert result.internal_json.intent == "stay_availability"
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["checkin_date"]
    assert result.internal_json.handoff["needed"] is False
    assert "sezon disinda" in result.user_message.casefold()
    assert "20 Nisan" in result.user_message


@pytest.mark.asyncio
async def test_run_message_pipeline_transfer_out_of_season_returns_deterministic_date_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transfer season rejections should ask for another in-season transfer date."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Transfer rezervasyonunu olusturuyorum.",
            [
                {
                    "name": "transfer_create_hold",
                    "arguments": {
                        "hotel_id": 21966,
                        "route": "DALAMAN_AIRPORT_TO_HOTEL",
                        "date": "2026-04-01",
                        "time": "12:00",
                        "pax_count": 2,
                    },
                    "result": {
                        "available": False,
                        "reason": "OUT_OF_SEASON",
                        "season": {"open": "04-20", "close": "10-31"},
                    },
                }
            ],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(season={"open": "04-20", "close": "10-31"})
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 Nisan icin Dalaman transferi ayirabilir misiniz?",
        dispatcher=None,
        expected_language="tr",
    )

    assert result.internal_json.intent == "transfer_booking_create"
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["date"]
    assert result.internal_json.handoff["needed"] is False
    assert "sezon disinda" in result.user_message.casefold()
    assert "20 Nisan" in result.user_message


@pytest.mark.asyncio
async def test_run_message_pipeline_parser_error_without_tools_returns_safe_retry_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing structured output should not pass through raw reservation promises."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return ("Rezervasyonunuzu olusturuyorum.", [])

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 Nisan icin rezervasyon olustur",
        expected_language="tr",
    )

    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.next_step == "restate_guest_request"
    assert "STRUCTURED_OUTPUT_ERROR" in result.internal_json.risk_flags
    assert result.internal_json.entities["response_parser"]["reason"] == "missing_internal_json"
    assert "tek kisa mesajla" in result.user_message.casefold()
    assert "olusturuyorum" not in result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_repairs_structured_output_before_retry_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parser errors should attempt schema repair before returning the generic retry response."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return ("Talebinizi aldim.", [])

    async def fake_repair_structured_output(**_kwargs: Any) -> dict[str, Any]:
        return {
            "user_message": "Talebinizi aldim. Tarih bilgisinizi paylasir misiniz?",
            "internal_json": {
                "language": "tr",
                "intent": "stay_booking_create",
                "state": "NEEDS_VERIFICATION",
                "entities": {"source": "repair"},
                "required_questions": ["checkin_date"],
                "tool_calls": [],
                "notifications": [],
                "handoff": {"needed": False},
                "risk_flags": [],
                "escalation": {"level": "L0", "route_to_role": "NONE"},
                "next_step": "collect_checkin_date",
            },
        }

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(
        run_tool_call_loop=fake_run_tool_call_loop,
        repair_structured_output=fake_repair_structured_output,
    )
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 Nisan icin rezervasyon olustur",
        expected_language="tr",
    )

    assert result.internal_json.intent == "stay_booking_create"
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["checkin_date"]
    assert "STRUCTURED_OUTPUT_ERROR" not in result.internal_json.risk_flags
    assert result.internal_json.entities["source"] == "repair"
    assert "scope_classifier" in result.internal_json.entities
    assert "tek kisa mesajla" not in result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_clears_stale_response_parser_context_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful turn should not inherit old response_parser metadata from conversation context."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "10-12 Haziran icin fiyat paylasabilirim.\n"
            'INTERNAL_JSON: {"language":"tr","intent":"stay_quote","state":"NEEDS_VERIFICATION",'
            '"entities":{"checkin_date":"2026-06-10","checkout_date":"2026-06-12","adults":2},'
            '"required_questions":["room_type_id"],"tool_calls":[],"notifications":[],'
            '"handoff":{"needed":false},"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"collect_room_type_id"}',
            [],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        entities_json={"response_parser": {"reason": "invalid_internal_json", "applied": True}},
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="10 haziran 12 haziran 2 yetiskin",
        expected_language="tr",
    )

    assert result.internal_json.intent == "stay_quote"
    assert "response_parser" not in result.internal_json.entities
    assert "scope_classifier" in result.internal_json.entities


def test_select_tool_definitions_for_restaurant_turn_returns_restaurant_shortlist() -> None:
    """Turn-level tool filtering should prefer restaurant tools over unrelated domains."""
    conversation = Conversation(
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        current_intent="restaurant_booking_create",
    )

    selected = whatsapp_webhook._select_tool_definitions_for_turn(
        conversation,
        "1 Nisan aksam yemegi icin masa ayirtmak istiyorum",
        whatsapp_webhook.get_tool_definitions(),
    )
    tool_names = whatsapp_webhook._extract_tool_definition_names(selected)

    assert "faq_lookup" in tool_names
    assert "restaurant_availability" in tool_names
    assert "restaurant_create_hold" in tool_names
    assert "approval_request" in tool_names
    assert "booking_availability" not in tool_names
    assert "transfer_get_info" not in tool_names
    assert "room_service_create_order" not in tool_names


@pytest.mark.asyncio
async def test_run_message_pipeline_clamps_stay_followup_when_llm_drifts_into_restaurant_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stay-only date follow-ups must not drift into restaurant intent when no restaurant tools were presented."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Restoran rezervasyonunuzu memnuniyetle oluşturalım.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":{},'
            '"required_questions":["time"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_restaurant_time"}',
            [],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        messages=[],
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="10 haziran 12 haziran 2 yetişkin",
        dispatcher=None,
        expected_language="tr",
    )

    assert result.internal_json.intent == "stay_availability"
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["chd_ages"]
    assert result.internal_json.next_step == "collect_stay_children_or_confirm_none"
    assert result.internal_json.entities["intent_domain_guard"]["applied"] is True
    assert result.internal_json.entities["stay_followup_hints"]["date_mentions"] == ["10 Haziran", "12 Haziran"]
    assert result.internal_json.entities["stay_followup_hints"]["adults"] == 2
    assert "Konaklama talebinizi not aldım" in result.user_message
    assert "Çocuk olacaksa yaşlarını paylaşır mısınız?" in result.user_message


def test_apply_turn_intent_domain_guard_normalizes_minor_month_typo_to_stay_followup() -> None:
    """Minor month typos should still trigger the stay-domain guard."""

    response = LLMResponse(
        user_message="Restoran için hangi saati tercih edersiniz?",
        internal_json=InternalJSON(
            language="tr",
            intent="restaurant_booking_create",
            state="NEEDS_VERIFICATION",
            entities={},
            required_questions=["time"],
            tool_calls=[],
            notifications=[],
            handoff={"needed": False},
            risk_flags=[],
            escalation={"level": "L0", "route_to_role": "NONE"},
            next_step="collect_restaurant_time",
        ),
    )

    meta = whatsapp_webhook._apply_turn_intent_domain_guard(
        response,
        normalized_text="10 haaziran",
        tool_names_presented=[
            "booking_availability",
            "booking_quote",
            "stay_create_hold",
            "handoff_create_ticket",
            "faq_lookup",
        ],
    )

    assert meta is not None
    assert response.internal_json.intent == "stay_availability"
    assert response.internal_json.required_questions == ["checkout_date"]
    assert response.internal_json.next_step == "collect_stay_checkout_date"
    assert response.internal_json.entities["stay_followup_hints"]["date_mentions"] == ["10 Haziran"]
    assert "10 Haziran" in response.user_message


@pytest.mark.asyncio
async def test_run_message_pipeline_replays_real_conversation_a71beafc_and_routes_to_season_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replay the real conversation transcript and ensure the final turn no longer blocks on area."""

    transcript_outputs = iter(
        [
            (
                "Vegan tatlı seçeneklerimizle ilgili memnuniyetle yardımcı olurum.\n"
                "INTERNAL_JSON: "
                '{"language":"tr","intent":"menu_inquiry","state":"ANSWERED","entities":{},'
                '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
                '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_guest_reply"}'
            ),
            (
                "Vegan tatlı seçeneklerimizle ilgili güncel bilgiyi restoran ekibimizden memnuniyetle teyit edebilirim.\n"
                "Hangi tarih ve saatte gelmeyi planlıyorsunuz?\nKaç kişi olacaksınız?\n"
                "INTERNAL_JSON: "
                '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":{},'
                '"required_questions":["date","time","party_size"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
                '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_restaurant_date_time_party_size"}'
            ),
            (
                "Teşekkür ederim.\n1 Nisan saat 19:00 için not aldım.\nKaç kişi olacaksınız?\n"
                "INTERNAL_JSON: "
                '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":'
                '{"date":"2026-04-01","time":"19:00"},'
                '"required_questions":["party_size"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
                '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_restaurant_party_size"}'
            ),
            (
                "Teşekkür ederim.\n1 Nisan saat 19:00 için 2 yetişkin olarak not aldım.\n"
                "Rezervasyonunuzu oluşturabilmem için ad soyadınızı rica edebilir miyim?\n"
                "INTERNAL_JSON: "
                '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":'
                '{"date":"2026-04-01","time":"19:00","party_size":2},'
                '"required_questions":["guest_name"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
                '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_restaurant_guest_name"}'
            ),
            (
                "Teşekkür ederim.\nRezervasyon kaydı için telefon numaranızı rica edebilir miyim?\n"
                "INTERNAL_JSON: "
                '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":'
                '{"date":"2026-04-01","time":"19:00","party_size":2,"guest_name":"Deneme Deneme"},'
                '"required_questions":["phone"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
                '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_restaurant_phone"}'
            ),
            (
                "Teşekkür ederim.\n\n"
                "1 Nisan saat 19:00 için 2 kişilik restoran rezervasyonunuzu oluşturuyorum.\n"
                "Vegan tatlı talebinizi de not olarak ekleyeceğim.\n\n"
                "Rezervasyonunuzu onaylamam için iç mekân mı, dış mekân mı tercih edersiniz?\n"
                "INTERNAL_JSON: "
                '{"language":"tr","intent":"restaurant_booking_create","state":"NEEDS_VERIFICATION","entities":'
                '{"date":"2026-04-01","time":"19:00","party_size":2,"guest_name":"Deneme Deneme","phone":"+905304498453"},'
                '"required_questions":["area"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
                '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_restaurant_area"}'
            ),
        ]
    )

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return next(transcript_outputs), []

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "restaurant_availability":
                return {
                    "available": False,
                    "reason": "OUT_OF_SEASON",
                    "options": [],
                    "season": {"open": "04-20", "close": "10-31"},
                }
            return {"error": "unexpected_tool"}

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        restaurant=SimpleNamespace(area_types=["outdoor"], hours={"dinner": "19:00-23:00"}),
        season={"open": "04-20", "close": "10-31"},
    )
    dispatcher = _Dispatcher()
    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        entities_json={},
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    user_turns = [
        "Vegan tatlılarınız konusunda yardımcı olur musun ?",
        "restoran",
        "1 nisan 19 00",
        "2 yetişkin",
        "Deneme Deneme",
        "+905304498453",
    ]

    last_result: LLMResponse | None = None
    for user_text in user_turns:
        last_result = await whatsapp_webhook._run_message_pipeline(
            conversation=conversation,
            normalized_text=user_text,
            dispatcher=dispatcher,
            expected_language="tr",
        )
        merged_entities = whatsapp_webhook._merge_entities_with_context(
            conversation.entities_json,
            last_result.internal_json.entities,
        )
        conversation.entities_json = merged_entities

    assert last_result is not None
    assert [item[0] for item in dispatcher.calls] == ["restaurant_availability"]
    assert last_result.internal_json.state == "NEEDS_VERIFICATION"
    assert last_result.internal_json.required_questions == ["date"]
    assert last_result.internal_json.entities["area"] == "outdoor"
    assert "sezon disinda" in last_result.user_message.casefold()
    assert "iç mekân mı, dış mekân mı" not in last_result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_emits_tool_trace_logs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline should log tool presentation and structured output trace data for diagnostics."""

    logged_events: list[tuple[str, dict[str, Any]]] = []

    class _Logger:
        def info(self, event: str, **kwargs: Any) -> None:
            logged_events.append((event, kwargs))

        def warning(self, event: str, **kwargs: Any) -> None:
            logged_events.append((event, kwargs))

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Wifi bilgisi hazır.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"faq_info","state":"ANSWERED","entities":{},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_guest_reply"}',
            [],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [{"role": "user", "content": "Wifi var mi?"}])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(id=uuid4(), hotel_id=21966, phone_hash="hash", language="tr")
    tool_defs = [{"type": "function", "function": {"name": "faq_lookup"}}]

    monkeypatch.setattr(whatsapp_webhook, "logger", _Logger())
    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: tool_defs)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Wifi var mi?",
        expected_language="tr",
    )

    assert result.internal_json.state == "ANSWERED"
    event_names = [event for event, _payload in logged_events]
    assert "llm_tool_trace_start" in event_names
    assert "llm_tool_trace_result" in event_names
    assert "llm_structured_output_trace" in event_names
    start_payload = next(payload for event, payload in logged_events if event == "llm_tool_trace_start")
    assert start_payload["tool_names"] == ["faq_lookup"]
    trace_payload = next(payload for event, payload in logged_events if event == "llm_structured_output_trace")
    assert trace_payload["parsed_intent"] == "faq_info"
    assert trace_payload["parser_error_reason"] is None


@pytest.mark.asyncio
async def test_run_message_pipeline_injects_context_into_llm_stay_hold_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live LLM tool calls should inherit hotel and conversation context automatically."""

    draft = {
        "checkin_date": "2026-10-01",
        "checkout_date": "2026-10-02",
        "room_type_id": 396097,
        "board_type_id": 2,
        "rate_type_id": 24171,
        "rate_code_id": 301001,
        "price_agency_id": 11,
        "currency_display": "EUR",
        "total_price_eur": 140,
        "adults": 2,
        "guest_name": "Deneme Denndim",
        "phone": "+905304498453",
        "cancel_policy_type": "NON_REFUNDABLE",
        "notes": "Yok",
    }

    async def fake_run_tool_call_loop(*, tool_executor: Any, **_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        tool_result = await tool_executor("stay_create_hold", {"draft": draft})
        return (
            "Talebinizi aldik.\n"
            "INTERNAL_JSON: "
            '{"language":"tr","intent":"stay_booking_create","state":"PENDING_APPROVAL","entities":'
            '{"checkin_date":"2026-10-01","checkout_date":"2026-10-02","adults":2,"chd_count":0,'
            '"chd_ages":[],"room_type_id":2,"cancel_policy_type":"NON_REFUNDABLE",'
            '"guest_name":"Deneme Denndim","phone":"+905304498453","nationality":"TR"},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
            '"next_step":"await_admin_approval"}',
            [
                {
                    "name": "stay_create_hold",
                    "arguments": {"draft": draft},
                    "result": tool_result,
                }
            ],
        )

    class _Dispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            return {
                "stay_hold_id": "S_HOLD_9010",
                "status": "PENDING_APPROVAL",
                "approval_request_id": "APR_9010",
                "approval_status": "REQUESTED",
            }

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
    )
    dispatcher = _Dispatcher()

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="evet",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert dispatcher.calls[0][0] == "stay_create_hold"
    assert dispatcher.calls[0][1]["hotel_id"] == 21966
    assert dispatcher.calls[0][1]["conversation_id"] == str(conversation.id)
    assert result.internal_json.state == "PENDING_APPROVAL"
    assert result.internal_json.next_step == "await_admin_approval"


def test_child_bedding_reply_uses_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two-child bedding replies should use the exact profile-driven bedding note."""
    profile = SimpleNamespace(
        facility_policies={
            "children": {
                "bedding_note_tr": (
                    "2 çocuklu konaklamalarda oda tipine ve uygunluğa göre 2 ek yatak "
                    "veya 1 ek yatak + 1 sofa hazırlanabilir."
                )
            }
        },
        room_types=[
            SimpleNamespace(name=SimpleNamespace(tr="Deluxe"), max_pax=3, extra_bed=True),
            SimpleNamespace(name=SimpleNamespace(tr="Premium"), max_pax=4, extra_bed=True),
            SimpleNamespace(name=SimpleNamespace(tr="Penthouse"), max_pax=4, extra_bed=True),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_turkish_child_bedding_reply(
        21966,
        {"adults": 2, "chd_count": 2},
    )

    assert "tek ek yatak bilgisi doğru değildir" not in reply
    assert "2 ek yatak veya 1 ek yatak + 1 sofa" in reply
    assert "Hangisini tercih edersiniz?" in reply


@pytest.mark.asyncio
async def test_process_incoming_message_skips_llm_after_handoff_lock(
    monkeypatch: pytest.MonkeyPatch,
    mock_whatsapp: Any,
) -> None:
    """Once handoff enables human override, later guest messages must not trigger LLM output."""
    _FakeHandoffConversationRepository.reset()

    async def _fake_pipeline(**_kwargs: Any) -> LLMResponse:
        _FakeHandoffConversationRepository.pipeline_calls += 1
        return LLMResponse(
            user_message="Sizi ilgili ekibimize iletiyorum.",
            internal_json=InternalJSON(
                language="tr",
                intent="human_handoff",
                state="HANDOFF",
                handoff={"needed": True, "reason": "explicit_request"},
                risk_flags=[],
                escalation={"level": "L0", "route_to_role": "NONE"},
                next_step="handoff_to_human",
            ),
        )

    monkeypatch.setattr(whatsapp_webhook, "ConversationRepository", _FakeHandoffConversationRepository)
    monkeypatch.setattr(whatsapp_webhook, "_run_message_pipeline", _fake_pipeline)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: mock_whatsapp)
    monkeypatch.setattr(whatsapp_webhook.settings, "operation_mode", "ai")

    first_incoming = IncomingMessage(
        message_id="handoff-first",
        phone="905551112233",
        display_name="Guest",
        text="Canli temsilciye baglar misiniz?",
        timestamp=int(time.time()),
        message_type="text",
    )
    second_incoming = IncomingMessage(
        message_id="handoff-second",
        phone="905551112233",
        display_name="Guest",
        text="Hala hatta misiniz?",
        timestamp=int(time.time()) + 1,
        message_type="text",
    )

    await whatsapp_webhook._process_incoming_message(
        incoming=first_incoming,
        hotel_id=21966,
        audit_context={"source_type": "test"},
        dispatcher=None,
        escalation_engine=None,
        tools={},
        db_pool=None,
    )

    assert _FakeHandoffConversationRepository.human_override is True
    assert _FakeHandoffConversationRepository.pipeline_calls == 1
    assert len(_FakeHandoffConversationRepository.assistant_messages) == 1
    assert mock_whatsapp.send_text_message.await_count == 1

    await whatsapp_webhook._process_incoming_message(
        incoming=second_incoming,
        hotel_id=21966,
        audit_context={"source_type": "test"},
        dispatcher=None,
        escalation_engine=None,
        tools={},
        db_pool=None,
    )

    assert _FakeHandoffConversationRepository.pipeline_calls == 1
    assert len(_FakeHandoffConversationRepository.assistant_messages) == 1
    assert len(_FakeHandoffConversationRepository.user_messages) == 2
    assert mock_whatsapp.send_text_message.await_count == 1


@pytest.mark.asyncio
async def test_process_burst_aggregated_skips_llm_after_handoff_lock(
    monkeypatch: pytest.MonkeyPatch,
    mock_whatsapp: Any,
) -> None:
    """Burst pipeline must also stop calling LLM once handoff locked the conversation."""
    _FakeHandoffConversationRepository.reset()

    async def _fake_pipeline(**_kwargs: Any) -> LLMResponse:
        _FakeHandoffConversationRepository.pipeline_calls += 1
        return LLMResponse(
            user_message="Sizi ilgili ekibimize iletiyorum.",
            internal_json=InternalJSON(
                language="tr",
                intent="human_handoff",
                state="HANDOFF",
                handoff={"needed": True, "reason": "explicit_request"},
                risk_flags=[],
                escalation={"level": "L0", "route_to_role": "NONE"},
                next_step="handoff_to_human",
            ),
        )

    monkeypatch.setattr(whatsapp_webhook, "ConversationRepository", _FakeHandoffConversationRepository)
    monkeypatch.setattr(whatsapp_webhook, "_run_message_pipeline", _fake_pipeline)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: mock_whatsapp)
    monkeypatch.setattr(whatsapp_webhook.settings, "operation_mode", "ai")

    first_aggregated = AggregatedMessage(
        phone="905551112233",
        display_name="Guest",
        phone_number_id=None,
        display_phone_number=None,
        combined_text="Canli temsilciye baglar misiniz?",
        original_texts=["Canli temsilciye baglar misiniz?"],
        message_ids=["burst-first"],
        first_timestamp=int(time.time()),
        last_timestamp=int(time.time()),
        part_count=1,
        message_type="text",
        audit_contexts=[{"source_type": "test"}],
    )
    second_aggregated = AggregatedMessage(
        phone="905551112233",
        display_name="Guest",
        phone_number_id=None,
        display_phone_number=None,
        combined_text="Hala hatta misiniz?",
        original_texts=["Hala hatta misiniz?"],
        message_ids=["burst-second"],
        first_timestamp=int(time.time()) + 1,
        last_timestamp=int(time.time()) + 1,
        part_count=1,
        message_type="text",
        audit_contexts=[{"source_type": "test"}],
    )

    await whatsapp_webhook._process_burst_aggregated(
        aggregated=first_aggregated,
        hotel_id=21966,
        dispatcher=None,
        escalation_engine=None,
        tools={},
        db_pool=None,
        redis_client=None,
    )

    assert _FakeHandoffConversationRepository.human_override is True
    assert _FakeHandoffConversationRepository.pipeline_calls == 1
    assert len(_FakeHandoffConversationRepository.assistant_messages) == 1
    assert mock_whatsapp.send_text_message.await_count == 1

    await whatsapp_webhook._process_burst_aggregated(
        aggregated=second_aggregated,
        hotel_id=21966,
        dispatcher=None,
        escalation_engine=None,
        tools={},
        db_pool=None,
        redis_client=None,
    )

    assert _FakeHandoffConversationRepository.pipeline_calls == 1
    assert len(_FakeHandoffConversationRepository.assistant_messages) == 1
    assert len(_FakeHandoffConversationRepository.user_messages) == 2
    assert mock_whatsapp.send_text_message.await_count == 1


@pytest.mark.asyncio
async def test_analyze_media_policy_response_returns_fallback_when_pipeline_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Media policy hook must return deterministic fallback even if pipeline crashes."""

    class _BrokenPipeline:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def process_first_image(self, **_kwargs: Any) -> Any:
            raise RuntimeError("inbound_media_table_missing")

    monkeypatch.setattr(whatsapp_webhook, "MediaPipelineService", _BrokenPipeline)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: SimpleNamespace())
    monkeypatch.setattr(whatsapp_webhook.settings, "media_analysis_enabled", True)

    response = await whatsapp_webhook._analyze_media_policy_response(
        hotel_id=21966,
        conversation_id="conv-media-fallback",
        language="tr",
        media_items=[
            InboundMediaItem(
                media_id="mid-fallback",
                media_type="image",
                mime_type="image/jpeg",
                whatsapp_message_id="wamid-fallback",
            )
        ],
    )

    assert response is not None
    assert response.internal_json.intent == "human_handoff"
    assert response.internal_json.state == "HANDOFF"
    assert response.internal_json.handoff.get("needed") is True


@pytest.mark.asyncio
async def test_process_voice_message_returns_transcript_when_pipeline_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Voice helper should pass high-confidence transcript into normal chat flow."""

    class _VoicePipeline:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def process_first_audio(self, **_kwargs: Any) -> Any:
            return SimpleNamespace(
                analyzed=True,
                transcription=AudioTranscriptionResult(
                    text="I need a transfer from Dalaman airport tonight.",
                    language="en",
                    confidence=0.91,
                    model_name="gpt-4o-mini-transcribe",
                    mime_type="audio/ogg",
                ),
                failure_reason=None,
            )

    monkeypatch.setattr(whatsapp_webhook, "VoicePipelineService", _VoicePipeline)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: SimpleNamespace())
    monkeypatch.setattr(whatsapp_webhook.settings, "audio_transcription_enabled", True)

    transcript, language, fallback = await whatsapp_webhook._process_voice_message(
        hotel_id=21966,
        conversation_id="conv-voice-ok",
        media_items=[
            InboundMediaItem(
                media_id="aud-ok",
                media_type="audio",
                mime_type="audio/ogg",
                whatsapp_message_id="wamid.voice.ok",
            )
        ],
    )

    assert transcript == "I need a transfer from Dalaman airport tonight."
    assert language == "en"
    assert fallback is None


@pytest.mark.asyncio
async def test_process_voice_message_returns_written_fallback_when_confidence_low(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Low-confidence voice transcripts must not auto-enter the free-form reply path."""

    class _VoicePipeline:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def process_first_audio(self, **_kwargs: Any) -> Any:
            return SimpleNamespace(
                analyzed=True,
                transcription=AudioTranscriptionResult(
                    text="yarin transfer",
                    language="tr",
                    confidence=0.20,
                    model_name="gpt-4o-mini-transcribe",
                    mime_type="audio/ogg",
                ),
                failure_reason=None,
            )

    monkeypatch.setattr(whatsapp_webhook, "VoicePipelineService", _VoicePipeline)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: SimpleNamespace())
    monkeypatch.setattr(whatsapp_webhook.settings, "audio_transcription_enabled", True)

    transcript, language, fallback = await whatsapp_webhook._process_voice_message(
        hotel_id=21966,
        conversation_id="conv-voice-low",
        media_items=[
            InboundMediaItem(
                media_id="aud-low",
                media_type="audio",
                mime_type="audio/ogg",
                whatsapp_message_id="wamid.voice.low",
            )
        ],
    )

    assert transcript is None
    assert language == "tr"
    assert fallback is not None
    assert fallback.internal_json.next_step == "ask_written_followup"


@pytest.mark.asyncio
async def test_process_incoming_message_resolves_reply_target_and_persists_outbound_whatsapp_id(
    monkeypatch: pytest.MonkeyPatch,
    mock_whatsapp: Any,
) -> None:
    """Reply-to metadata should resolve prior target content and persist outbound provider ids."""
    _FakeHandoffConversationRepository.reset()

    previous_assistant = Message(
        conversation_id=_FakeHandoffConversationRepository.conversation_id,
        role="assistant",
        content="Deluxe 180 EUR, Premium 220 EUR. Hangisini istersiniz?",
        internal_json={"whatsapp_message_id": "wamid.prev.1"},
    )
    _FakeHandoffConversationRepository.assistant_messages.append(previous_assistant)
    captured: dict[str, Any] = {}

    async def _fake_pipeline(**kwargs: Any) -> LLMResponse:
        captured["reply_context"] = kwargs.get("reply_context")
        return LLMResponse(
            user_message="Premium odayi ayiriyorum.",
            internal_json=InternalJSON(
                language="tr",
                intent="stay_booking_create",
                state="INFORMATION_GATHERING",
                risk_flags=[],
                escalation={"level": "L0", "route_to_role": "NONE"},
            ),
        )

    monkeypatch.setattr(whatsapp_webhook, "ConversationRepository", _FakeHandoffConversationRepository)
    monkeypatch.setattr(whatsapp_webhook, "_run_message_pipeline", _fake_pipeline)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: mock_whatsapp)
    monkeypatch.setattr(whatsapp_webhook.settings, "operation_mode", "ai")

    incoming = IncomingMessage(
        message_id="reply-live-1",
        phone="905551112233",
        display_name="Guest",
        text="bunu alalim",
        timestamp=int(time.time()),
        message_type="text",
        reply_to_message_id="wamid.prev.1",
        reply_to_from="905559998877",
    )

    await whatsapp_webhook._process_incoming_message(
        incoming=incoming,
        hotel_id=21966,
        audit_context={
            "source_type": "test",
            "message_id": incoming.message_id,
            "reply_to_message_id": incoming.reply_to_message_id,
            "reply_to_from": incoming.reply_to_from,
        },
        dispatcher=None,
        escalation_engine=None,
        tools={},
        db_pool=None,
    )

    assert captured["reply_context"] == {
        "present": True,
        "resolved": True,
        "reply_to_message_id": "wamid.prev.1",
        "reply_to_from": "905559998877",
        "target_message_db_id": None,
        "target_role": "assistant",
        "target_content": "Deluxe 180 EUR, Premium 220 EUR. Hangisini istersiniz?",
    }
    assert _FakeHandoffConversationRepository.assistant_messages[-1].internal_json["whatsapp_message_id"] == "wamid.1"


def test_parking_reply_uses_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parking questions should use the exact profile-driven parking reply."""
    profile = SimpleNamespace(
        facility_policies={
            "parking": {
                "reply_tr": (
                    "Aracınız için park yeri ayarlayabiliriz. Ücretsiz cadde park yerleri "
                    "mevcuttur, ayrıca otelin karşısında özel bir otopark da bulunmaktadır. "
                    "Varışınızda sizi park alanına yönlendireceğiz."
                )
            }
        }
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_turkish_parking_reply(21966)

    assert "Ücretsiz cadde park yerleri" in reply
    assert "Varışınızda sizi park alanına yönlendireceğiz." in reply


def test_payment_reply_uses_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Payment-method questions should use the exact profile-driven payment reply."""
    profile = SimpleNamespace(
        model_dump=lambda: {
            "payment": {
                "reply_tr": (
                    "Evet, kredi kartı dışında nakit ve havale kabul ediyoruz. "
                    "İsterseniz rezervasyon aşamasında size uygun ödeme yöntemini "
                    "birlikte netleştirebiliriz."
                )
            }
        }
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_turkish_payment_methods_reply(21966)

    assert "nakit ve havale kabul ediyoruz" in reply


def test_payment_intake_requests_reference_and_name_before_handoff() -> None:
    """Payment messages should collect minimum info before human handoff."""
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")
    response = whatsapp_webhook._build_payment_intake_response(
        conversation=conversation,
        normalized_text="odeme yapmak istiyorum",
        target_language="tr",
    )

    assert response is not None
    assert response.internal_json.state == "NEEDS_VERIFICATION"
    assert response.internal_json.intent == "payment_inquiry"
    assert "reference_id" in response.internal_json.required_questions
    assert "full_name" in response.internal_json.required_questions
    assert "Odeme ekibimize yonlendirebilmem" in response.user_message


def test_enforce_single_step_collection_reduces_required_questions() -> None:
    """Reservation verification should request only one missing field per turn."""
    response = LLMResponse(
        user_message="Lütfen giriş, çıkış ve yetişkin sayısını paylaşın.",
        internal_json=InternalJSON(
            language="tr",
            intent="stay_booking_create",
            state="NEEDS_VERIFICATION",
            entities={},
            required_questions=["checkin_date", "checkout_date", "adults"],
            handoff={"needed": False, "reason": None},
            next_step="collect_missing_slots",
        ),
    )

    whatsapp_webhook._enforce_single_step_collection(response)

    assert response.internal_json.required_questions == ["checkin_date"]
    assert "giriş tarihinizi" in response.user_message
    assert "çıkış" not in response.user_message.casefold()


def test_suppress_default_year_question_for_stay_quote() -> None:
    """Stay quote flow should remove default year clarification when user did not ask for year."""
    response = LLMResponse(
        user_message="Bu tarihleri hangi yıl için düşünüyorsunuz? (2026)",
        internal_json=InternalJSON(
            language="tr",
            intent="stay_quote",
            state="NEEDS_VERIFICATION",
            entities={},
            required_questions=["Hangi yıl?", "adults"],
            handoff={"needed": False, "reason": None},
            next_step="collect_missing_slots",
        ),
    )

    whatsapp_webhook._suppress_default_year_question(response, "13-15 haziran icin fiyat")

    assert response.internal_json.required_questions == ["adults"]
    assert "Kaç yetişkin" in response.user_message


def test_suppress_default_year_question_keeps_explicit_year_requests() -> None:
    """Year clarification should stay when guest explicitly referenced year."""
    response = LLMResponse(
        user_message="Bu tarihleri hangi yıl için düşünüyorsunuz?",
        internal_json=InternalJSON(
            language="tr",
            intent="stay_quote",
            state="NEEDS_VERIFICATION",
            entities={},
            required_questions=["Hangi yıl?"],
            handoff={"needed": False, "reason": None},
            next_step="collect_missing_slots",
        ),
    )

    whatsapp_webhook._suppress_default_year_question(response, "2027 yilinda fiyat alabilir miyim?")

    assert response.internal_json.required_questions == ["Hangi yıl?"]
    assert "hangi yıl" in response.user_message.casefold()


def test_payment_intake_completes_then_routes_to_handoff() -> None:
    """Once intake fields exist, payment flow should move to HANDOFF."""
    conversation = Conversation(
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        entities_json={
            "payment_intake": {
                "in_progress": True,
                "reference_id": "S_HOLD_1234",
                "full_name": "Ali Veli",
            }
        },
    )
    response = whatsapp_webhook._build_payment_intake_response(
        conversation=conversation,
        normalized_text="detaylari ilettim",
        target_language="tr",
    )

    assert response is not None
    assert response.internal_json.state == "HANDOFF"
    assert response.internal_json.handoff["needed"] is True
    assert "PAYMENT_CONFUSION" in response.internal_json.risk_flags


def test_handoff_lock_activates_for_handoff_state() -> None:
    """HANDOFF state should force the post-handoff conversation lock."""
    assert whatsapp_webhook._should_activate_handoff_lock("HANDOFF", {"needed": False}) is True


def test_handoff_lock_activates_for_explicit_handoff_flag() -> None:
    """handoff.needed should lock the conversation even if state was omitted."""
    assert whatsapp_webhook._should_activate_handoff_lock("", {"needed": True}) is True


def test_direct_admin_notify_required_when_route_is_not_admin() -> None:
    """Non-ADMIN escalations still require an immediate ADMIN handoff notify."""
    response = LLMResponse(
        user_message="Sizi ekibimize aktariyorum.",
        internal_json=InternalJSON(
            language="tr",
            intent="human_handoff",
            state="HANDOFF",
            handoff={"needed": True, "reason": "manual_review"},
            risk_flags=["GROUP_BOOKING"],
            escalation={"level": "L2", "route_to_role": "SALES", "sla_hint": "high"},
            next_step="handoff_to_sales",
        ),
    )

    escalation_result = EscalationResult(
        level=EscalationLevel.L2,
        route_to_role=Role.SALES,
        dedupe_key="GROUP_BOOKING|human_handoff|ref",
        reason="manual_review",
        sla_hint="high",
        actions=["handoff.create_ticket", "notify.send"],
        risk_flags_matched=["GROUP_BOOKING"],
    )

    assert whatsapp_webhook._resolve_handoff_assignment_role(response, escalation_result) == "SALES"
    assert whatsapp_webhook._should_send_direct_admin_handoff_notify("SALES", escalation_result) is True


def test_direct_admin_notify_skipped_when_escalation_already_routes_to_admin() -> None:
    """If escalation will notify ADMIN anyway, the direct notify should not duplicate it."""
    response = LLMResponse(
        user_message="Sizi ekibimize aktariyorum.",
        internal_json=InternalJSON(
            language="tr",
            intent="human_handoff",
            state="HANDOFF",
            handoff={"needed": True, "reason": "legal_review"},
            risk_flags=["LEGAL_REQUEST"],
            escalation={"level": "L3", "route_to_role": "ADMIN", "sla_hint": "high"},
            next_step="handoff_to_admin",
        ),
    )

    escalation_result = EscalationResult(
        level=EscalationLevel.L3,
        route_to_role=Role.ADMIN,
        dedupe_key="LEGAL_REQUEST|human_handoff|ref",
        reason="legal_review",
        sla_hint="high",
        actions=["handoff.create_ticket", "notify.send"],
        risk_flags_matched=["LEGAL_REQUEST"],
    )

    assert whatsapp_webhook._resolve_handoff_assignment_role(response, escalation_result) == "ADMIN"
    assert whatsapp_webhook._should_send_direct_admin_handoff_notify("ADMIN", escalation_result) is False


def test_fallback_handoff_assignment_defaults_to_admin() -> None:
    """HANDOFF without escalation routing should still open an ADMIN-owned ticket."""
    response = LLMResponse(
        user_message="Sizi ekibimize aktariyorum.",
        internal_json=InternalJSON(
            language="tr",
            intent="human_handoff",
            state="HANDOFF",
            handoff={"needed": True, "reason": "explicit_request"},
            risk_flags=[],
            escalation={"level": "L0", "route_to_role": "NONE"},
            next_step="handoff_to_human",
        ),
    )

    assert whatsapp_webhook._resolve_handoff_assignment_role(response, None) == "ADMIN"
    assert whatsapp_webhook._should_send_direct_admin_handoff_notify("ADMIN", None) is False


def test_admin_notify_required_if_admin_ticket_could_not_be_ensured() -> None:
    """If ADMIN-owned ticket creation fails, direct ADMIN notify must still fire."""
    assert whatsapp_webhook._should_send_direct_admin_handoff_notify(
        "ADMIN",
        None,
        ticket_ensured=False,
    ) is True


@pytest.mark.asyncio
async def test_stale_human_override_cache_is_self_healed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Phone-scoped Redis override must not block a fresh conversation when DB says false."""

    class _FakeRedis:
        def __init__(self) -> None:
            self.store = {"velox:human_override:phone_hash": "1"}

        async def get(self, key: str) -> str | None:
            return self.store.get(key)

        async def delete(self, key: str) -> int:
            existed = key in self.store
            self.store.pop(key, None)
            return 1 if existed else 0

    _FakeHandoffConversationRepository.reset()
    _FakeHandoffConversationRepository.human_override = False
    monkeypatch.setattr(whatsapp_webhook, "ConversationRepository", _FakeHandoffConversationRepository)
    redis = _FakeRedis()

    active = await whatsapp_webhook._is_human_override_active(
        "phone_hash",
        _FakeHandoffConversationRepository.conversation_id,
        redis,
    )

    assert active is False
    assert redis.store == {}


def test_handoff_transcript_summary_uses_recent_messages() -> None:
    """Immediate handoff notifications should summarize the latest turns only."""
    conversation_id = uuid4()
    messages = [
        Message(conversation_id=conversation_id, role="user", content="ilk mesaj"),
        Message(conversation_id=conversation_id, role="assistant", content="ilk cevap"),
        Message(conversation_id=conversation_id, role="user", content="ikinci mesaj"),
    ]

    summary = whatsapp_webhook._build_handoff_transcript_summary(messages)

    assert "[USER] ilk mesaj" in summary
    assert "[ASSISTANT] ilk cevap" in summary
    assert "[USER] ikinci mesaj" in summary


def test_elevator_reply_uses_profile_policy_for_russian(monkeypatch: pytest.MonkeyPatch) -> None:
    """Elevator questions should use profile-driven accessibility policy."""
    profile = SimpleNamespace(
        facility_policies={
            "accessibility": {
                "elevator_available": False,
                "reply_ru": "В нашем отеле лифта нет. На первом этаже есть доступные варианты номеров.",
            }
        }
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_elevator_reply(21966, "ru")

    assert "лифта нет" in reply


def test_elevator_detection_matches_russian_and_turkish() -> None:
    """Elevator detector should catch both Russian and Turkish variants."""
    assert whatsapp_webhook._is_elevator_question("В вашем отеле есть лифт?") is True
    assert whatsapp_webhook._is_elevator_question("Otelde asansör var mı?") is True


def test_detect_message_language_for_english_sentence() -> None:
    """Language detector should classify English reservation text as EN."""
    detected = whatsapp_webhook._detect_message_language(
        "I need airport transfer + dinner reservation + late checkout in one package.",
        fallback="tr",
    )
    assert detected == "en"


def test_detect_message_language_for_russian_sentence() -> None:
    """Language detector should classify Cyrillic reservation text as RU."""
    detected = whatsapp_webhook._detect_message_language(
        "В вашем отеле есть лифт?",
        fallback="tr",
    )
    assert detected == "ru"


def test_detect_message_language_sticky_mode_keeps_turkish_for_url_payload() -> None:
    """Sticky mode should not switch from Turkish due to technical URL tokens."""
    detected = whatsapp_webhook._detect_message_language(
        "https://kassandra-butik-otel.rezervasyonal.com/?Checkin=2026-09-01&Checkout=2026-09-05&Adult=2&child=0&language=tr",
        fallback="tr",
        sticky_mode=True,
    )
    assert detected == "tr"


@pytest.mark.asyncio
async def test_run_message_pipeline_locks_expected_language(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pipeline should lock internal language to detected guest input language."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Hello there\nINTERNAL_JSON: "
            '{"language":"tr","intent":"other","state":"INTENT_DETECTED","entities":{},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_user_input"}',
            [],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="I need airport transfer",
        expected_language="en",
    )
    assert result.internal_json.language == "en"


@pytest.mark.asyncio
async def test_run_message_pipeline_media_room_type_followup_is_profile_grounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Media follow-up room-type question must bypass LLM and stay profile-grounded."""
    llm_called = {"count": 0}

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        llm_called["count"] += 1
        return (
            "Bu görsele bakarak net bir oda tipi söylemem mümkün değil. "
            "Standart mı, Deluxe mi yoksa Süit mi?",
            [],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(name=SimpleNamespace(tr="Deluxe", en="Deluxe")),
            SimpleNamespace(name=SimpleNamespace(tr="Premium", en="Premium")),
        ]
    )
    conversation = Conversation(
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        entities_json={"media_analysis": {"intent": "general_photo_info", "confidence": 0.9}},
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Hangi oda tipi olduğunu söyler misiniz?",
        expected_language="tr",
    )

    assert llm_called["count"] == 0
    assert "Sistemimizde tanımlı oda tipleri: Deluxe, Premium." in result.user_message
    assert "Standart" not in result.user_message
    assert "Süit" not in result.user_message
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["checkin_date", "checkout_date", "adults"]


@pytest.mark.asyncio
async def test_run_message_pipeline_media_guard_rewrites_profile_unsupported_room_classes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If LLM emits unsupported room classes in media context, response must be rewritten."""
    llm_called = {"count": 0}

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        llm_called["count"] += 1
        return (
            "Bu görsele bakarak net bir oda tipi söylemem mümkün değil. Standart mı, Deluxe mi yoksa Süit mi?\n"
            'INTERNAL_JSON: {"language":"tr","intent":"faq_info","state":"INTENT_DETECTED","entities":{},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_user_input"}',
            [],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(name=SimpleNamespace(tr="Deluxe", en="Deluxe")),
            SimpleNamespace(name=SimpleNamespace(tr="Premium", en="Premium")),
        ]
    )
    conversation = Conversation(
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        entities_json={"media_analysis": {"intent": "general_photo_info", "confidence": 0.9}},
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: fake_profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Teşekkürler, devam edelim.",
        expected_language="tr",
    )

    assert llm_called["count"] == 1
    assert "Sistemimizde tanımlı oda tipleri: Deluxe, Premium." in result.user_message
    assert "Standart" not in result.user_message
    assert "Süit" not in result.user_message
    assert result.internal_json.state == "NEEDS_VERIFICATION"
    assert result.internal_json.required_questions == ["checkin_date", "checkout_date", "adults"]


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_manual_mode_bypasses_llm_and_forces_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restaurant requests in MANUEL mode must skip LLM/tool flow and hand off immediately."""
    llm_called = {"count": 0}

    class _ManualModeSettingsRepo:
        async def get(self, _hotel_id: int) -> Any:
            return SimpleNamespace(reservation_mode=RestaurantReservationMode.MANUEL)

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        llm_called["count"] += 1
        return ("", [])

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "RestaurantSettingsRepository", _ManualModeSettingsRepo)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Restoran rezervasyonu yapmak istiyorum",
        expected_language="tr",
    )

    assert llm_called["count"] == 0
    assert result.internal_json.intent == "restaurant_booking_create"
    assert result.internal_json.state == "HANDOFF"
    assert result.internal_json.handoff["needed"] is True
    assert result.internal_json.handoff["reason"] == "restaurant_manual_mode"
    assert "manuel modda" in result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_manual_mode_uses_existing_restaurant_context_without_keyword(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual mode should still hand off follow-up turns that continue restaurant intent context."""
    llm_called = {"count": 0}

    class _ManualModeSettingsRepo:
        async def get(self, _hotel_id: int) -> Any:
            return SimpleNamespace(reservation_mode=RestaurantReservationMode.MANUEL)

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        llm_called["count"] += 1
        return ("", [])

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        current_intent="restaurant_booking_create",
    )

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "RestaurantSettingsRepository", _ManualModeSettingsRepo)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="yarin 20:00 uygun mu",
        expected_language="tr",
    )

    assert llm_called["count"] == 0
    assert result.internal_json.state == "HANDOFF"
    assert result.internal_json.handoff["needed"] is True
    assert result.internal_json.handoff["reason"] == "restaurant_manual_mode"


@pytest.mark.asyncio
async def test_run_message_pipeline_restaurant_daily_capacity_full_routes_to_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restaurant daily max full should preserve collected details and route to human handoff."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Talebinizi kontrol ediyorum.\nINTERNAL_JSON: "
            '{"language":"tr","intent":"restaurant_booking_create","state":"TOOL_RUNNING","entities":{},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_tool_result"}',
            [
                {
                    "name": "restaurant_create_hold",
                    "arguments": {
                        "slot_id": 42,
                        "guest_name": "Ali Veli",
                        "phone": "+905551112233",
                        "party_size": 4,
                    },
                    "result": {
                        "available": False,
                        "reason": "DAILY_CAPACITY_FULL",
                        "suggestion": "handoff",
                        "handoff_required": True,
                        "count": 15,
                        "max": 15,
                        "collected_reservation_context": {
                            "date": "2026-08-10",
                            "time": "20:00:00",
                            "party_size": 4,
                            "guest_name": "Ali Veli",
                            "phone": "+905551112233",
                            "area": "outdoor",
                            "notes": "Window side if possible",
                        },
                    },
                }
            ],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="Akşam 8 için 4 kişilik restoran rezervasyonu yapmak istiyorum",
        expected_language="tr",
    )

    assert result.internal_json.state == "HANDOFF"
    assert result.internal_json.handoff["needed"] is True
    assert result.internal_json.handoff["reason"] == "restaurant_daily_capacity_full"
    assert result.internal_json.entities["guest_name"] == "Ali Veli"
    assert result.internal_json.entities["phone"] == "+905551112233"
    assert result.internal_json.entities["date"] == "2026-08-10"
    assert "gunluk restoran rezervasyon kotamiz" in result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_quote_error_uses_live_price_unavailable_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quote tool errors should trigger a handoff fallback without year clarification."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "2026 mi kontrol edelim?\nINTERNAL_JSON: "
            '{"language":"tr","intent":"stay_quote","state":"NEEDS_VERIFICATION","entities":{},'
            '"required_questions":["Hangi yıl?"],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"collect_missing_slots"}',
            [{"name": "booking_quote", "arguments": {}, "result": {"error": "provider timeout"}}],
        )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="13-15 haziran fiyat alabilir miyim",
        expected_language="tr",
    )

    assert result.internal_json.state == "HANDOFF"
    assert result.internal_json.handoff["needed"] is True
    assert result.internal_json.handoff["reason"] == "live_price_unavailable"
    assert "TOOL_UNAVAILABLE" in result.internal_json.risk_flags
    assert "canlı fiyat" in result.user_message.casefold()
    assert "yıl" not in result.user_message.casefold()


@pytest.mark.asyncio
async def test_run_message_pipeline_backfills_availability_for_quote_filtering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stay quote flow should auto-fetch availability when LLM called quote only."""

    async def fake_run_tool_call_loop(**_kwargs: Any) -> tuple[str, list[dict[str, Any]]]:
        return (
            "Fiyatlar hazir.\nINTERNAL_JSON: "
            '{"language":"tr","intent":"stay_quote","state":"READY_FOR_TOOL","entities":{},'
            '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
            '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"send_quote"}',
            [
                {
                    "name": "booking_quote",
                    "arguments": {
                        "checkin_date": "2026-10-01",
                        "checkout_date": "2026-10-06",
                        "adults": 2,
                        "chd_count": 0,
                        "currency": "EUR",
                    },
                    "result": {
                        "offers": [
                            {
                                "room_type_id": 396094,
                                "room_type": "DELUXE",
                                "rate_type_id": 24171,
                                "rate_type": "İptal Edilemez",
                                "price": "500",
                                "discounted_price": "500",
                                "currency_code": "EUR",
                                "room_area": 25,
                            },
                            {
                                "room_type_id": 396097,
                                "room_type": "SUPERIOR",
                                "rate_type_id": 24171,
                                "rate_type": "İptal Edilemez",
                                "price": "600",
                                "discounted_price": "600",
                                "currency_code": "EUR",
                                "room_area": 30,
                            },
                        ]
                    },
                }
            ],
        )

    class DispatcherStub:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, kwargs))
            if name == "booking_availability":
                return {
                    "rows": [
                        {"date": "2026-10-01", "room_type_id": 396094, "room_to_sell": 2, "stop_sell": False},
                        {"date": "2026-10-02", "room_type_id": 396094, "room_to_sell": 2, "stop_sell": False},
                        {"date": "2026-10-03", "room_type_id": 396094, "room_to_sell": 2, "stop_sell": False},
                        {"date": "2026-10-04", "room_type_id": 396094, "room_to_sell": 2, "stop_sell": False},
                        {"date": "2026-10-05", "room_type_id": 396094, "room_to_sell": 2, "stop_sell": False},
                    ]
                }
            return {}

    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(pms_room_type_id=396094, name=SimpleNamespace(tr="Deluxe"), size_m2=25),
            SimpleNamespace(pms_room_type_id=396097, name=SimpleNamespace(tr="Superior"), size_m2=30),
        ],
    )

    fake_builder = SimpleNamespace(build_messages=lambda *_args, **_kwargs: [])
    fake_client = SimpleNamespace(run_tool_call_loop=fake_run_tool_call_loop)
    dispatcher = DispatcherStub()
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    monkeypatch.setattr(whatsapp_webhook, "get_prompt_builder", lambda: fake_builder)
    monkeypatch.setattr(whatsapp_webhook, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(whatsapp_webhook, "get_tool_definitions", lambda: [])
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    result = await whatsapp_webhook._run_message_pipeline(
        conversation=conversation,
        normalized_text="1 ekim 6 ekim 2 yetiskin fiyat nedir",
        dispatcher=dispatcher,
        expected_language="tr",
    )

    assert any(name == "booking_availability" for name, _kwargs in dispatcher.calls)
    assert "Deluxe (25m2)" in result.user_message
    assert "Superior (30m2)" not in result.user_message


def test_booking_quote_failed_or_empty_uses_latest_attempt_only() -> None:
    """Earlier quote failures should not override a later successful quote."""
    executed_calls = [
        {"name": "booking_quote", "result": {"error": "timeout"}},
        {"name": "booking_quote", "result": {"offers": [{"id": "offer-1"}]}},
    ]
    assert whatsapp_webhook._booking_quote_failed_or_empty(executed_calls) is False

    executed_calls_latest_error = [
        {"name": "booking_quote", "result": {"offers": [{"id": "offer-1"}]}},
        {"name": "booking_quote", "result": {"error": "timeout"}},
    ]
    assert whatsapp_webhook._booking_quote_failed_or_empty(executed_calls_latest_error) is True


def test_parking_detection_does_not_match_havale() -> None:
    """Parking detection must not confuse 'havale' with 'vale'."""
    assert whatsapp_webhook._is_parking_question("Kredi kartı dışında havale kabul ediyor musunuz?") is False
    assert whatsapp_webhook._is_payment_method_question("Kredi kartı dışında havale kabul ediyor musunuz?") is True


def test_deterministic_turkish_quote_reply_uses_live_rate_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stay quote replies should be built from live FREE_CANCEL/NON_REFUNDABLE offers only."""
    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(
                pms_room_type_id=396094,
                name=SimpleNamespace(tr="Deluxe"),
                size_m2=25,
            ),
            SimpleNamespace(
                pms_room_type_id=396097,
                name=SimpleNamespace(tr="Superior"),
                size_m2=30,
            ),
            SimpleNamespace(
                pms_room_type_id=397738,
                name=SimpleNamespace(tr="Exclusive Land"),
                size_m2=40,
            ),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)
    executed_calls = [
        {
            "name": "booking_quote",
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24169,"rate_type":"Kontrat","price":"710","discounted_price":"497","currency_code":"EUR","room_area":25,"cancel_possible":false},'
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"710","discounted_price":"496.9","currency_code":"EUR","room_area":25,"cancel_possible":false},'
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"781","discounted_price":"546.7","currency_code":"EUR","room_area":25,"cancel_possible":true},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"729","discounted_price":"510.3","currency_code":"EUR","room_area":30,"cancel_possible":false},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"801.9","discounted_price":"561.3","currency_code":"EUR","room_area":30,"cancel_possible":true},'
                '{"room_type_id":397738,"room_type":"EXCLUSIVE LAND","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"748","discounted_price":"523.6","currency_code":"EUR","room_area":40,"cancel_possible":false},'
                '{"room_type_id":397738,"room_type":"EXCLUSIVE LAND","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"822.8","discounted_price":"575.9","currency_code":"EUR","room_area":40,"cancel_possible":true}'
                ']}'
            ),
        }
    ]

    reply = whatsapp_webhook._build_deterministic_turkish_stay_quote_reply(21966, executed_calls)

    assert reply is not None
    assert "Deluxe (25m2)" in reply
    assert "İptal edilemez: 495 €" in reply
    assert "Ücretsiz İptal: 545 €" in reply
    assert "Superior (30m2)" in reply
    assert "Exclusive Sokak Manzaralı (40m2)" in reply
    assert "Kontrat" not in reply


def test_deterministic_turkish_quote_reply_formats_multi_room_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Different occupancies should be rendered as separate customer messages."""
    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(pms_room_type_id=396094, name=SimpleNamespace(tr="Deluxe"), size_m2=25),
            SimpleNamespace(pms_room_type_id=396097, name=SimpleNamespace(tr="Superior"), size_m2=30),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    executed_calls = [
        {
            "name": "booking_quote",
            "arguments": '{"adults":3,"chd_count":0}',
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"500","discounted_price":"500","currency_code":"EUR","room_area":25,"cancel_possible":false},'
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"550","discounted_price":"550","currency_code":"EUR","room_area":25,"cancel_possible":true}'
                ']}'
            ),
        },
        {
            "name": "booking_quote",
            "arguments": '{"adults":1,"chd_count":2}',
            "result": (
                '{"offers":['
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"600","discounted_price":"600","currency_code":"EUR","room_area":30,"cancel_possible":false},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"650","discounted_price":"650","currency_code":"EUR","room_area":30,"cancel_possible":true}'
                ']}'
            ),
        },
    ]

    messages = whatsapp_webhook._build_deterministic_turkish_stay_quote_messages(21966, executed_calls)

    assert len(messages) == 2
    assert messages[0].startswith("1. Oda")
    assert messages[1].startswith("2. Oda")
    assert "Deluxe (25m2)" in messages[0]
    assert "Superior (30m2)" in messages[1]


def test_deterministic_quote_reply_filters_out_unavailable_room_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quote reply must not include room types excluded by booking_availability."""
    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(pms_room_type_id=396094, name=SimpleNamespace(tr="Deluxe"), size_m2=25),
            SimpleNamespace(pms_room_type_id=396097, name=SimpleNamespace(tr="Superior"), size_m2=30),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    executed_calls = [
        {
            "name": "booking_availability",
            "arguments": '{"checkin_date":"2026-10-01","checkout_date":"2026-10-06","adults":2}',
            "result": '{"rows":[{"room_type_id":396094,"room_to_sell":2,"stop_sell":false},{"room_type_id":396097,"room_to_sell":0,"stop_sell":false}]}',
        },
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-10-01","checkout_date":"2026-10-06","adults":2}',
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"500","discounted_price":"500","currency_code":"EUR","room_area":25,"cancel_possible":false},'
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"550","discounted_price":"550","currency_code":"EUR","room_area":25,"cancel_possible":true},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"600","discounted_price":"600","currency_code":"EUR","room_area":30,"cancel_possible":false},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"650","discounted_price":"650","currency_code":"EUR","room_area":30,"cancel_possible":true}'
                ']}'
            ),
        },
    ]

    messages = whatsapp_webhook._build_deterministic_turkish_stay_quote_messages(21966, executed_calls)

    assert len(messages) == 1
    assert "Deluxe (25m2)" in messages[0]
    assert "Superior (30m2)" not in messages[0]


def test_deterministic_quote_reply_returns_no_availability_when_sellable_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """If no sellable room exists, quote message should become explicit no-availability notice."""
    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(pms_room_type_id=396094, name=SimpleNamespace(tr="Deluxe"), size_m2=25),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    executed_calls = [
        {
            "name": "booking_availability",
            "arguments": '{"checkin_date":"2026-10-01","checkout_date":"2026-10-06","adults":2}',
            "result": '{"rows":[{"date":"2026-10-01","room_type_id":396094,"room_to_sell":0,"stop_sell":true}]}',
        },
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-10-01","checkout_date":"2026-10-06","adults":2}',
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"500","discounted_price":"500","currency_code":"EUR","room_area":25,"cancel_possible":false}'
                ']}'
            ),
        },
    ]

    messages = whatsapp_webhook._build_deterministic_turkish_stay_quote_messages(21966, executed_calls)

    assert messages == [whatsapp_webhook.TR_NO_AVAILABLE_ROOM_FOR_QUOTE]


def test_deterministic_turkish_quote_reply_merges_same_occupancy_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """FREE_CANCEL and NON_REFUNDABLE calls for same room request must merge into one message."""
    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(pms_room_type_id=396094, name=SimpleNamespace(tr="Deluxe"), size_m2=25),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    executed_calls = [
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-04-21","checkout_date":"2026-04-22","adults":1,"chd_count":0}',
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"85","discounted_price":"85","currency_code":"EUR","room_area":25,"cancel_possible":false}'
                ']}'
            ),
        },
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-04-21","checkout_date":"2026-04-22","adults":1,"chd_count":0}',
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"90","discounted_price":"90","currency_code":"EUR","room_area":25,"cancel_possible":true}'
                ']}'
            ),
        },
    ]

    messages = whatsapp_webhook._build_deterministic_turkish_stay_quote_messages(21966, executed_calls)

    assert len(messages) == 1
    assert "1. Oda" not in messages[0]
    assert "2026-04-21 - 2026-04-22 tarihleri arasında 1 gece" in messages[0]
    assert "İptal edilemez: 85 €" in messages[0]
    assert "Ücretsiz İptal: 90 €" in messages[0]


def test_normalized_turkish_quote_reply_keeps_notes_single() -> None:
    """Deterministic quote text should receive the required notes exactly once."""
    reply = whatsapp_webhook._normalize_turkish_stay_quote_reply(
        "Deluxe (25m2)\nİptal edilemez: 495 €\nÜcretsiz İptal: 545 €",
        "3 Ağustos ile 5 Ağustos arasında 1 yetişkin + 1 çocuk (8 yaş) için fiyat alabilir miyim?",
    )

    assert reply.count(whatsapp_webhook.TR_FREE_CANCEL_NOTE) == 1
    assert reply.count(whatsapp_webhook.TR_NON_REFUNDABLE_NOTE) == 1
    assert reply.count(whatsapp_webhook.TR_ROOM_NUMBER_NOTE) == 1
