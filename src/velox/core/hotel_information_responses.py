"""Deterministic responses for structured hotel-information matches."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import orjson

from velox.core.hotel_information_loader import get_hotel_information
from velox.core.hotel_information_matcher import HotelInformationMatch, match_hotel_information
from velox.models.conversation import InternalJSON, LLMResponse
from velox.models.hotel_information import HotelInformationEntry

HotelInformationToolRunner = Callable[[str, dict[str, Any]], Awaitable[str | dict[str, Any]]]


def find_structured_hotel_information_match(
    hotel_id: int,
    query: str,
) -> HotelInformationMatch | None:
    """Return a structured hotel-information match for a guest query."""
    dataset = get_hotel_information(hotel_id)
    if dataset is None:
        return None
    return match_hotel_information(dataset, query)


async def try_build_structured_hotel_information_response(
    *,
    hotel_id: int,
    query: str,
    language: str,
    tool_runner: HotelInformationToolRunner | None = None,
) -> tuple[LLMResponse | None, list[dict[str, Any]]]:
    """Build a deterministic response when the query matches structured hotel information."""
    match = find_structured_hotel_information_match(hotel_id, query)
    if match is None:
        return None, []

    tool_args = {"hotel_id": hotel_id, "query": query, "language": language}
    executed_calls: list[dict[str, Any]] = []
    payload = build_hotel_information_payload(match)

    if tool_runner is not None:
        raw_result = await tool_runner("hotel_info_lookup", tool_args)
        executed_calls.append(
            {
                "name": "hotel_info_lookup",
                "arguments": tool_args,
                "result": raw_result,
            }
        )
        tool_payload = _decode_tool_payload(raw_result)
        if _is_hotel_information_json_payload(tool_payload):
            payload = tool_payload

    response = build_hotel_information_response(payload, language=language)
    return response, executed_calls


def build_hotel_information_payload(match: HotelInformationMatch) -> dict[str, Any]:
    """Return a tool-style payload for one structured hotel-information match."""
    entry = match.entry
    payload = hotel_information_entry_payload(entry)
    payload.update(
        {
            "found": True,
            "topic": entry.id,
            "source": "HOTEL_INFORMATION_JSON",
            "source_path": f"hotel_information[id={entry.id}].answer_tr",
            "answer": entry.answer_tr,
            "answer_tr": entry.answer_tr,
            "match_score": match.score,
            "match_type": match.match_type,
            "matched_trigger": match.matched_trigger,
            "should_answer_directly": not entry.human_handoff_required,
        }
    )
    if entry.human_handoff_required:
        payload["handoff"] = {
            "needed": True,
            "reason": f"hotel_information_handoff_required:{entry.id}",
            "route_to_role": "ADMIN",
        }
        payload["risk_flags"] = ["UNRESOLVED_CASE"]
    else:
        payload["handoff"] = {"needed": False}
        payload["risk_flags"] = []
    return payload


def hotel_information_entry_payload(entry: HotelInformationEntry) -> dict[str, Any]:
    """Return JSON-serializable entry fields without renaming source keys."""
    return {
        "id": entry.id,
        "category": entry.category,
        "title_tr": entry.title_tr,
        "data_type": entry.data_type,
        "value": entry.value,
        "unit": entry.unit,
        "confidence": entry.confidence,
        "human_handoff_required": entry.human_handoff_required,
        "missing_information": entry.missing_information,
        "notes": entry.notes,
        "trigger_examples": entry.trigger_examples,
    }


def hotel_information_unresolved_payload() -> dict[str, Any]:
    """Return a safe unresolved payload when structured data cannot answer."""
    return {
        "found": False,
        "source": "HOTEL_INFORMATION_JSON",
        "human_handoff_required": True,
        "should_answer_directly": False,
        "handoff": {
            "needed": True,
            "reason": "hotel_information_no_verified_match",
            "route_to_role": "ADMIN",
        },
        "risk_flags": ["UNRESOLVED_CASE"],
    }


def build_hotel_information_response(
    payload: dict[str, Any],
    *,
    language: str,
) -> LLMResponse | None:
    """Build a guest response that uses only HOTEL_INFORMATION_JSON answer_tr."""
    if not _is_hotel_information_json_payload(payload):
        return None

    answer_tr = str(payload.get("answer_tr") or payload.get("answer") or "").strip()
    if not answer_tr:
        return None

    raw_handoff = payload.get("handoff")
    handoff = raw_handoff if isinstance(raw_handoff, dict) else {}
    handoff_needed = bool(payload.get("human_handoff_required")) or bool(handoff.get("needed"))
    normalized_handoff = dict(handoff)
    normalized_handoff["needed"] = handoff_needed
    if handoff_needed:
        normalized_handoff.setdefault(
            "reason",
            f"hotel_information_handoff_required:{payload.get('id') or payload.get('topic') or 'unknown'}",
        )
        normalized_handoff.setdefault("route_to_role", "ADMIN")

    risk_flags = _string_list(payload.get("risk_flags"))
    if handoff_needed and "UNRESOLVED_CASE" not in risk_flags:
        risk_flags.append("UNRESOLVED_CASE")

    response_language = "tr" if answer_tr else _normalize_language(language)
    return LLMResponse(
        user_message=answer_tr,
        internal_json=InternalJSON(
            language=response_language,
            intent="hotel_info",
            state="HANDOFF" if handoff_needed else "ANSWERED",
            entities={"hotel_information": _response_entity_payload(payload)},
            required_questions=[],
            tool_calls=[],
            notifications=[],
            handoff=normalized_handoff,
            risk_flags=risk_flags,
            escalation=_escalation_payload(normalized_handoff, risk_flags),
            next_step="handoff_to_admin" if handoff_needed else "answer_sent",
        ),
    )


def _decode_tool_payload(value: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        payload = orjson.loads(value)
    except orjson.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _is_hotel_information_json_payload(payload: dict[str, Any]) -> bool:
    return str(payload.get("source") or "").strip() == "HOTEL_INFORMATION_JSON" and bool(
        str(payload.get("answer_tr") or payload.get("answer") or "").strip()
    )


def _response_entity_payload(payload: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "topic",
        "category",
        "title_tr",
        "answer_tr",
        "data_type",
        "value",
        "unit",
        "confidence",
        "human_handoff_required",
        "missing_information",
        "notes",
        "trigger_examples",
        "source",
        "source_path",
        "match_score",
        "match_type",
        "matched_trigger",
        "should_answer_directly",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def _escalation_payload(handoff: dict[str, Any], risk_flags: list[str]) -> dict[str, Any]:
    if not bool(handoff.get("needed")):
        return {"level": "L0", "route_to_role": "NONE"}
    return {
        "level": "L1",
        "route_to_role": str(handoff.get("route_to_role") or "ADMIN"),
        "reason": str(handoff.get("reason") or "hotel_information_handoff_required"),
        "sla_hint": "medium",
        "risk_flags": risk_flags,
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _normalize_language(value: str) -> str:
    normalized = str(value or "tr").strip().lower()
    return normalized or "tr"
