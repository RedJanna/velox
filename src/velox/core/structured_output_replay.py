"""Helpers for replaying structured-output failure conversations."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from velox.config.constants import ConversationState, Intent
from velox.llm.response_parser import ResponseParser
from velox.models.conversation import Conversation, Message

_PARSER_ENTITY_KEY = "response_parser"
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_NUMERIC_SEQUENCE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)")


@dataclass(frozen=True, slots=True)
class StructuredOutputReplayCandidate:
    """Replay-ready view of a single assistant failure turn."""

    conversation_id: UUID
    hotel_id: int
    language: str
    assistant_message_id: UUID
    assistant_created_at: datetime
    parser_reason: str
    trigger_user_message_id: UUID | None
    trigger_user_text: str
    assistant_text: str


def extract_parser_reason_from_internal_json(internal_json: dict[str, Any] | None) -> str:
    """Extract the persisted parser error reason from a message payload."""
    if not isinstance(internal_json, dict):
        return ""
    entities = internal_json.get("entities")
    if isinstance(entities, dict):
        parser_meta = entities.get(_PARSER_ENTITY_KEY)
        if isinstance(parser_meta, dict):
            reason = str(parser_meta.get("reason") or "").strip()
            if reason:
                return reason
    return ""


def build_replay_candidate(
    conversation: Conversation,
    history: list[Message],
    assistant_message_id: UUID,
) -> StructuredOutputReplayCandidate | None:
    """Build a replay candidate for the target assistant failure message."""
    ordered = sorted(history, key=lambda item: (item.created_at, str(item.id or "")))
    assistant_index = next(
        (
            index
            for index, message in enumerate(ordered)
            if message.id == assistant_message_id and message.role == "assistant"
        ),
        None,
    )
    if assistant_index is None:
        return None

    assistant_message = ordered[assistant_index]
    if conversation.id is None or assistant_message.id is None:
        return None
    parser_reason = extract_parser_reason_from_internal_json(assistant_message.internal_json)
    if not parser_reason:
        return None

    trigger_user_message = next(
        (message for message in reversed(ordered[:assistant_index]) if message.role == "user"),
        None,
    )

    return StructuredOutputReplayCandidate(
        conversation_id=conversation.id,
        hotel_id=conversation.hotel_id,
        language=str(conversation.language or "tr"),
        assistant_message_id=assistant_message.id,
        assistant_created_at=assistant_message.created_at,
        parser_reason=parser_reason,
        trigger_user_message_id=trigger_user_message.id if trigger_user_message is not None else None,
        trigger_user_text=trigger_user_message.content if trigger_user_message is not None else "",
        assistant_text=assistant_message.content,
    )


def build_replay_conversation(
    conversation: Conversation,
    history: list[Message],
    trigger_user_message_id: UUID | None,
) -> Conversation:
    """Reconstruct the conversation checkpoint immediately before the failed assistant turn."""
    ordered = sorted(history, key=lambda item: (item.created_at, str(item.id or "")))
    if trigger_user_message_id is not None:
        trigger_index = next(
            (index for index, message in enumerate(ordered) if message.id == trigger_user_message_id),
            len(ordered) - 1,
        )
        relevant_history = ordered[: trigger_index + 1]
    else:
        relevant_history = ordered

    prior_history = (
        relevant_history[:-1]
        if relevant_history and relevant_history[-1].role == "user"
        else relevant_history
    )
    checkpoint_assistant = next(
        (
            message
            for message in reversed(prior_history)
            if message.role == "assistant" and isinstance(message.internal_json, dict)
        ),
        None,
    )

    checkpoint_language = conversation.language
    checkpoint_state: ConversationState | str = conversation.current_state
    checkpoint_intent: Intent | str | None = conversation.current_intent
    checkpoint_entities = dict(conversation.entities_json)
    checkpoint_risk_flags = list(conversation.risk_flags)

    if checkpoint_assistant is not None and isinstance(checkpoint_assistant.internal_json, dict):
        internal_json = checkpoint_assistant.internal_json
        checkpoint_language = str(internal_json.get("language") or checkpoint_language or "tr")
        checkpoint_state = _coerce_state(internal_json.get("state"), checkpoint_state)
        checkpoint_intent = _coerce_intent(internal_json.get("intent"), checkpoint_intent)
        entities = internal_json.get("entities")
        if isinstance(entities, dict):
            checkpoint_entities = dict(entities)
        risk_flags = internal_json.get("risk_flags")
        if isinstance(risk_flags, list):
            checkpoint_risk_flags = [str(flag) for flag in risk_flags if str(flag or "").strip()]

    return Conversation(
        id=conversation.id,
        hotel_id=conversation.hotel_id,
        phone_hash=conversation.phone_hash,
        phone_display=conversation.phone_display,
        language=checkpoint_language,
        current_state=checkpoint_state,
        current_intent=checkpoint_intent,
        entities_json=checkpoint_entities,
        risk_flags=checkpoint_risk_flags,
        is_active=conversation.is_active,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
        messages=relevant_history,
    )


def analyze_original_assistant_output(raw_content: str) -> dict[str, Any]:
    """Run the current parser over the persisted assistant output."""
    parsed = ResponseParser.parse(raw_content)
    parser_reason = ResponseParser.extract_parser_error(parsed.internal_json)
    return {
        "current_parser_reason": parser_reason or None,
        "current_intent": str(parsed.internal_json.intent or "").strip() or None,
        "current_state": str(parsed.internal_json.state or "").strip() or None,
        "current_user_message_preview": sanitize_replay_preview(parsed.user_message, max_length=200),
    }


def sanitize_replay_preview(text: str, *, max_length: int = 240) -> str:
    """Redact obvious PII from replay previews before printing or exporting them."""
    preview = str(text or "")[:max_length]
    preview = _EMAIL_PATTERN.sub("[redacted-email]", preview)
    return _NUMERIC_SEQUENCE_PATTERN.sub(_mask_sensitive_number_match, preview)


def resolve_replay_time_window(
    *,
    since_hours: int | None = None,
    since: str | None = None,
    until: str | None = None,
    now: datetime | None = None,
) -> tuple[datetime | None, datetime | None]:
    """Resolve CLI time filters into an aware UTC window."""
    if since_hours is not None and since_hours < 1:
        raise ValueError("since_hours must be greater than or equal to 1")
    if since_hours is not None and since:
        raise ValueError("since_hours and since cannot be used together")

    current_time = _ensure_aware_datetime(now or datetime.now(UTC))
    since_at = _parse_replay_datetime(since) if since else None
    until_at = _parse_replay_datetime(until) if until else None

    if since_hours is not None:
        since_at = current_time - timedelta(hours=since_hours)
    if since_at is not None and until_at is not None and since_at > until_at:
        raise ValueError("since must be earlier than or equal to until")
    return since_at, until_at


def build_replay_summary(results: list[dict[str, Any]], *, run_llm: bool) -> dict[str, Any]:
    """Aggregate replay results into a compact summary for ops review."""
    summary: dict[str, Any] = {
        "candidate_count": len(results),
        "parser_reason_counts": _count_non_empty(entry.get("parser_reason") for entry in results),
        "assistant_created_at_window": _summarize_datetime_field(
            entry.get("assistant_created_at") for entry in results
        ),
        "system_prompt_length": _summarize_numeric_field(entry.get("system_prompt_length") for entry in results),
        "tool_count": _summarize_numeric_field(entry.get("tool_count") for entry in results),
    }
    if not run_llm:
        return summary

    llm_entries: list[dict[str, Any]] = []
    for entry in results:
        llm_replay = entry.get("llm_replay")
        if isinstance(llm_replay, dict):
            llm_entries.append(llm_replay)
    status_counts = _count_non_empty(item.get("status") for item in llm_entries)
    ok_entries = [item for item in llm_entries if str(item.get("status") or "") == "ok"]
    clean_replay_count = len(
        [item for item in ok_entries if not str(item.get("parser_error_reason") or "").strip()]
    )
    remaining_parser_error_count = len(
        [item for item in ok_entries if str(item.get("parser_error_reason") or "").strip()]
    )

    summary["llm_replay"] = {
        "status_counts": status_counts,
        "clean_replay_count": clean_replay_count,
        "remaining_parser_error_count": remaining_parser_error_count,
        "intent_counts": _count_non_empty(item.get("intent") for item in ok_entries),
        "state_counts": _count_non_empty(item.get("state") for item in ok_entries),
        "intent_domain_guard_counts": _count_non_empty(
            item.get("intent_domain_guard_reason") for item in ok_entries
        ),
    }
    return summary


def _coerce_state(value: Any, fallback: ConversationState | str) -> ConversationState | str:
    """Coerce persisted state strings back into the ConversationState enum when possible."""
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        return ConversationState(text)
    except ValueError:
        return fallback


def _coerce_intent(value: Any, fallback: Intent | str | None) -> Intent | str | None:
    """Coerce persisted intent strings back into the Intent enum when possible."""
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        return Intent(text)
    except ValueError:
        return fallback


def _mask_sensitive_number_match(match: re.Match[str]) -> str:
    """Mask phone/card-like number sequences while keeping dates untouched."""
    value = match.group(0)
    digit_count = sum(1 for char in value if char.isdigit())
    if digit_count < 10:
        return value
    return "[redacted-number]"


def _count_non_empty(values: Any) -> dict[str, int]:
    """Count non-empty values as strings for stable JSON output."""
    counter: Counter[str] = Counter()
    for value in values:
        text = str(value or "").strip()
        if text:
            counter[text] += 1
    return dict(sorted(counter.items()))


def _summarize_numeric_field(values: Any) -> dict[str, int | float] | None:
    """Return min/max/avg stats for numeric replay fields."""
    numbers = [int(value) for value in values if isinstance(value, int | float)]
    if not numbers:
        return None
    return {
        "min": min(numbers),
        "max": max(numbers),
        "avg": round(sum(numbers) / len(numbers), 2),
    }


def _parse_replay_datetime(raw_value: Any) -> datetime:
    """Parse an ISO-like replay datetime and normalize it to UTC."""
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError("datetime filter must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(raw_value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid datetime filter: {raw_value}") from exc
    return _ensure_aware_datetime(parsed)


def _ensure_aware_datetime(value: datetime) -> datetime:
    """Normalize naive datetimes to UTC and preserve aware values in UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _summarize_datetime_field(values: Any) -> dict[str, str] | None:
    """Return min/max ISO-8601 timestamps for replay time windows."""
    timestamps: list[datetime] = []
    for value in values:
        if isinstance(value, datetime):
            timestamps.append(_ensure_aware_datetime(value))
            continue
        if isinstance(value, str) and value.strip():
            try:
                timestamps.append(_parse_replay_datetime(value))
            except ValueError:
                continue
    if not timestamps:
        return None
    return {
        "min": min(timestamps).isoformat(),
        "max": max(timestamps).isoformat(),
    }
