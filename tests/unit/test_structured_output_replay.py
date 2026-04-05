"""Unit tests for structured-output replay helpers."""

from datetime import datetime, timedelta
from uuid import uuid4

from velox.core.structured_output_replay import (
    analyze_original_assistant_output,
    build_replay_summary,
    build_replay_candidate,
    build_replay_conversation,
    resolve_replay_time_window,
    sanitize_replay_preview,
)
from velox.models.conversation import Conversation, Message


def test_build_replay_candidate_extracts_parser_reason_and_trigger_user() -> None:
    """The replay candidate should bind the failure turn to the triggering user message."""
    conversation_id = uuid4()
    user_message_id = uuid4()
    assistant_message_id = uuid4()
    now = datetime.now()
    conversation = Conversation(id=conversation_id, hotel_id=21966, phone_hash="hash", language="tr")
    history = [
        Message(conversation_id=conversation_id, id=user_message_id, role="user", content="fiyat alabilir miyim", created_at=now),
        Message(
            conversation_id=conversation_id,
            id=assistant_message_id,
            role="assistant",
            content="Tekrar yazar misiniz?",
            internal_json={
                "entities": {"response_parser": {"reason": "missing_internal_json", "applied": True}},
                "risk_flags": ["STRUCTURED_OUTPUT_ERROR"],
            },
            created_at=now + timedelta(seconds=1),
        ),
    ]

    candidate = build_replay_candidate(conversation, history, assistant_message_id)

    assert candidate is not None
    assert candidate.parser_reason == "missing_internal_json"
    assert candidate.trigger_user_message_id == user_message_id
    assert candidate.trigger_user_text == "fiyat alabilir miyim"


def test_build_replay_conversation_uses_latest_prior_assistant_checkpoint() -> None:
    """Replay checkpoint should restore the last assistant state before the failed turn."""
    conversation_id = uuid4()
    first_assistant_id = uuid4()
    trigger_user_id = uuid4()
    assistant_failure_id = uuid4()
    now = datetime.now()
    conversation = Conversation(
        id=conversation_id,
        hotel_id=21966,
        phone_hash="hash",
        language="tr",
        current_state="GREETING",
        current_intent="other",
    )
    history = [
        Message(conversation_id=conversation_id, role="user", content="merhaba", created_at=now),
        Message(
            conversation_id=conversation_id,
            id=first_assistant_id,
            role="assistant",
            content="Tarih alabilir miyim?",
            internal_json={
                "language": "tr",
                "intent": "stay_booking_create",
                "state": "NEEDS_VERIFICATION",
                "entities": {"checkin_date": "2026-05-01"},
                "risk_flags": [],
            },
            created_at=now + timedelta(seconds=1),
        ),
        Message(
            conversation_id=conversation_id,
            id=trigger_user_id,
            role="user",
            content="2 gece kalacagim",
            created_at=now + timedelta(seconds=2),
        ),
        Message(
            conversation_id=conversation_id,
            id=assistant_failure_id,
            role="assistant",
            content="Tekrar yazar misiniz?",
            internal_json={
                "entities": {"response_parser": {"reason": "missing_internal_json", "applied": True}},
                "risk_flags": ["STRUCTURED_OUTPUT_ERROR"],
            },
            created_at=now + timedelta(seconds=3),
        ),
    ]

    replay_conversation = build_replay_conversation(conversation, history, trigger_user_id)

    assert replay_conversation.current_state == "NEEDS_VERIFICATION"
    assert replay_conversation.current_intent == "stay_booking_create"
    assert replay_conversation.entities_json == {"checkin_date": "2026-05-01"}
    assert replay_conversation.messages[-1].id == trigger_user_id
    assert replay_conversation.messages[-1].role == "user"


def test_analyze_original_assistant_output_reports_current_parser_result() -> None:
    """The analysis helper should expose whether the current parser still fails on the stored output."""
    analysis = analyze_original_assistant_output("Rezervasyonunuzu oluşturuyorum.")

    assert analysis["current_parser_reason"] == "missing_internal_json"
    assert analysis["current_intent"] is None


def test_sanitize_replay_preview_masks_sensitive_sequences_but_preserves_dates() -> None:
    """Replay previews should hide PII-like content without destroying normal booking fields."""
    preview = sanitize_replay_preview(
        "Bana +90 555 123 45 67 numarasindan ve ali@example.com adresinden ulasin. Gelis 2026-05-01."
    )

    assert "[redacted-number]" in preview
    assert "[redacted-email]" in preview
    assert "2026-05-01" in preview


def test_build_replay_summary_aggregates_batch_statistics() -> None:
    """Replay batches should expose concise aggregate counts for regression tracking."""
    summary = build_replay_summary(
        [
            {
                "parser_reason": "invalid_internal_json",
                "assistant_created_at": "2026-04-04T07:32:21.721873+00:00",
                "system_prompt_length": 6300,
                "tool_count": 10,
                "llm_replay": {
                    "status": "ok",
                    "intent": "stay_availability_request",
                    "state": "collecting_missing_fields",
                    "parser_error_reason": None,
                    "intent_domain_guard_reason": "stay_followup_without_restaurant_tools",
                },
            },
            {
                "parser_reason": "missing_internal_json",
                "assistant_created_at": "2026-04-04T07:36:52.854449+00:00",
                "system_prompt_length": 6400,
                "tool_count": 8,
                "llm_replay": {
                    "status": "ok",
                    "intent": "stay_availability_request",
                    "state": "needs_verification",
                    "parser_error_reason": "missing_internal_json",
                    "intent_domain_guard_reason": None,
                },
            },
            {
                "parser_reason": "invalid_internal_json",
                "assistant_created_at": "2026-04-04T17:13:55.421995+00:00",
                "system_prompt_length": 6200,
                "tool_count": 9,
                "llm_replay": {
                    "status": "error",
                    "error_type": "RuntimeError",
                },
            },
        ],
        run_llm=True,
    )

    assert summary["candidate_count"] == 3
    assert summary["parser_reason_counts"] == {
        "invalid_internal_json": 2,
        "missing_internal_json": 1,
    }
    assert summary["assistant_created_at_window"] == {
        "min": "2026-04-04T07:32:21.721873+00:00",
        "max": "2026-04-04T17:13:55.421995+00:00",
    }
    assert summary["system_prompt_length"] == {"min": 6200, "max": 6400, "avg": 6300.0}
    assert summary["tool_count"] == {"min": 8, "max": 10, "avg": 9.0}
    assert summary["llm_replay"]["status_counts"] == {"error": 1, "ok": 2}
    assert summary["llm_replay"]["clean_replay_count"] == 1
    assert summary["llm_replay"]["remaining_parser_error_count"] == 1
    assert summary["llm_replay"]["intent_counts"] == {"stay_availability_request": 2}
    assert summary["llm_replay"]["state_counts"] == {
        "collecting_missing_fields": 1,
        "needs_verification": 1,
    }
    assert summary["llm_replay"]["intent_domain_guard_counts"] == {
        "stay_followup_without_restaurant_tools": 1,
    }


def test_resolve_replay_time_window_supports_relative_and_absolute_filters() -> None:
    """Replay windows should support both since-hours and absolute ISO timestamps."""
    now = datetime(2026, 4, 4, 18, 0, 0)

    since_at, until_at = resolve_replay_time_window(since_hours=24, now=now)

    assert since_at == datetime(2026, 4, 3, 18, 0, 0, tzinfo=since_at.tzinfo)
    assert until_at is None

    since_at, until_at = resolve_replay_time_window(
        since="2026-04-04T07:00:00Z",
        until="2026-04-04T18:00:00+00:00",
    )

    assert since_at.isoformat() == "2026-04-04T07:00:00+00:00"
    assert until_at.isoformat() == "2026-04-04T18:00:00+00:00"


def test_resolve_replay_time_window_rejects_invalid_ranges() -> None:
    """Replay windows should fail fast on ambiguous or reversed filters."""
    try:
        resolve_replay_time_window(since_hours=0)
    except ValueError as exc:
        assert "greater than or equal to 1" in str(exc)
    else:
        raise AssertionError("Expected non-positive since-hours to fail")

    try:
        resolve_replay_time_window(since_hours=24, since="2026-04-04T07:00:00Z")
    except ValueError as exc:
        assert "cannot be used together" in str(exc)
    else:
        raise AssertionError("Expected conflicting relative and absolute filters to fail")

    try:
        resolve_replay_time_window(since="not-a-timestamp")
    except ValueError as exc:
        assert "invalid datetime filter" in str(exc)
    else:
        raise AssertionError("Expected invalid ISO datetime filter to fail")

    try:
        resolve_replay_time_window(
            since="2026-04-04T18:00:00Z",
            until="2026-04-04T07:00:00Z",
        )
    except ValueError as exc:
        assert "earlier than or equal" in str(exc)
    else:
        raise AssertionError("Expected reversed time range to fail")
