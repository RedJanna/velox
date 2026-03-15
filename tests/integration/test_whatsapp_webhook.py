"""Integration tests for WhatsApp webhook routes."""

import time
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from velox.adapters.whatsapp.webhook import IncomingMessage
from velox.api.routes import whatsapp_webhook
from velox.models.conversation import Conversation, InternalJSON, LLMResponse


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
    """Two-child bedding replies should not claim a single extra bed."""
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

    assert "tek ek yatak bilgisi doğru değildir" in reply
    assert "2 ek yatak veya 1 ek yatak + 1 sofa" in reply
    assert "**Premium**" in reply
    assert "**Penthouse**" in reply


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
