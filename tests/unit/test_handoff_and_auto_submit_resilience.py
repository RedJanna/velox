"""Regression tests for reservation auto-submit and handoff resilience guards."""

from velox.api.routes.whatsapp_webhook import (
    _build_fallback_handoff_dedupe_key,
    _extract_handoff_ticket_id_from_tool_calls,
    _should_auto_submit_restaurant_hold,
    _should_auto_submit_stay_hold,
    _should_auto_submit_transfer_hold,
)
from velox.db.repositories.hotel import _normalize_dedupe_key
from velox.models.conversation import Conversation, InternalJSON, LLMResponse


def test_fallback_handoff_dedupe_key_is_capped_to_db_limit() -> None:
    """Fallback dedupe keys must stay within DB varchar(200) constraint."""
    conversation = Conversation(hotel_id=21966, phone_hash="x" * 64, phone_display="905551112233")
    response = LLMResponse(
        user_message="handoff",
        internal_json=InternalJSON(
            intent="other",
            state="HANDOFF",
            handoff={
                "needed": True,
                "reason": (
                    "Rate metadata (rate_type_id, rate_code_id, price_agency_id) required for stay_create_hold "
                    "not available in conversation context and requires manual operation review immediately."
                ),
            },
        ),
    )

    dedupe_key = _build_fallback_handoff_dedupe_key(conversation, response)
    assert len(dedupe_key) <= 200
    assert "sha1:" in dedupe_key


def test_extract_handoff_ticket_id_from_tool_calls_reads_executed_result() -> None:
    """Finalize handoff should reuse ticket id when LLM already opened one."""
    internal = InternalJSON(
        intent="other",
        state="HANDOFF",
        tool_calls=[
            {
                "name": "handoff_create_ticket",
                "status": "executed",
                "result": {"ticket_id": "T_999", "status": "OPEN"},
            }
        ],
    )
    assert _extract_handoff_ticket_id_from_tool_calls(internal) == "T_999"


def test_stay_auto_submit_accepts_needs_verification_when_tool_planned() -> None:
    """If stay_create_hold is planned and no missing questions remain, fallback should run."""
    internal = InternalJSON(
        intent="stay_booking_create",
        state="NEEDS_VERIFICATION",
        required_questions=[],
        tool_calls=[{"name": "stay_create_hold", "arguments": {"hotel_id": 21966}}],
    )
    assert _should_auto_submit_stay_hold(internal) is True


def test_transfer_auto_submit_accepts_needs_verification_when_tool_planned() -> None:
    """Transfer flow should recover when model plans tool call without executing it."""
    internal = InternalJSON(
        intent="transfer_booking_create",
        state="NEEDS_VERIFICATION",
        required_questions=[],
        tool_calls=[{"name": "transfer_create_hold", "arguments": {"hotel_id": 21966}}],
    )
    entities = {
        "route": "DALAMAN_AIRPORT_TO_HOTEL",
        "date": "2026-10-05",
        "time": "14:30",
        "pax_count": 2,
        "guest_name": "Test Guest",
        "phone": "+905551112233",
    }
    assert _should_auto_submit_transfer_hold(internal, entities, normalized_text="evet") is True


def test_restaurant_auto_submit_accepts_needs_verification_when_tool_planned() -> None:
    """Restaurant flow should also recover when tool call is planned in structured output."""
    internal = InternalJSON(
        intent="restaurant_booking_create",
        state="NEEDS_VERIFICATION",
        required_questions=[],
        tool_calls=[{"name": "restaurant_create_hold", "arguments": {"hotel_id": 21966}}],
    )
    entities = {
        "date": "2026-10-05",
        "time": "20:00",
        "party_size": 4,
        "guest_name": "Test Guest",
        "phone": "+905551112233",
    }
    assert _should_auto_submit_restaurant_hold(internal, entities, normalized_text="evet") is True


def test_ticket_dedupe_key_normalizer_caps_length() -> None:
    """Repository-level guard must keep dedupe keys safe for all flows."""
    long_value = "A" * 260
    normalized = _normalize_dedupe_key(long_value)
    assert normalized is not None
    assert len(normalized) <= 200
    assert "|sha1:" in normalized
