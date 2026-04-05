"""Unit tests for LLM response parser error signaling."""

from velox.llm.response_parser import ResponseParser


def test_parse_marks_missing_internal_json_as_parser_error() -> None:
    """Missing INTERNAL_JSON should not silently collapse into an empty structured payload."""
    parsed = ResponseParser.parse("Rezervasyonunuzu oluşturuyorum.")

    assert ResponseParser.extract_parser_error(parsed.internal_json) == "missing_internal_json"
    assert "STRUCTURED_OUTPUT_ERROR" in parsed.internal_json.risk_flags
    assert parsed.internal_json.next_step == "recover_from_structured_output_error"


def test_parse_normalizes_common_internal_json_schema_slips() -> None:
    """Recoverable schema slips should be normalized instead of triggering a hard parser error."""
    parsed = ResponseParser.parse(
        "Talebinizi aldim.\n"
        'INTERNAL_JSON: {"language":"tr","intent":"stay_booking_create","state":"READY_FOR_TOOL",'
        '"entities":[],"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
        '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_tool_result"}'
    )

    assert ResponseParser.extract_parser_error(parsed.internal_json) == ""
    assert parsed.internal_json.intent == "stay_booking_create"
    assert parsed.internal_json.state == "READY_FOR_TOOL"
    assert parsed.internal_json.entities == {}
    assert parsed.internal_json.risk_flags == []


def test_parse_balanced_internal_json_marker_ignores_trailing_noise() -> None:
    """Balanced extraction should keep valid JSON even when extra text follows the object."""
    parsed = ResponseParser.parse(
        "Bilgileri not ettim.\n"
        'INTERNAL_JSON: {"language":"tr","intent":"faq_info","state":"ANSWERED","entities":{"topic":"wifi"},'
        '"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
        '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"await_guest_reply"}'
        "\nEk yorum buraya sarkti."
    )

    assert ResponseParser.extract_parser_error(parsed.internal_json) == ""
    assert parsed.internal_json.intent == "faq_info"
    assert parsed.internal_json.entities["topic"] == "wifi"


def test_parse_normalizes_legacy_intent_and_state_aliases() -> None:
    """Legacy intent/state aliases should be coerced onto the canonical runtime contract."""
    parsed = ResponseParser.parse(
        "Bilgileri not ettim.\n"
        'INTERNAL_JSON: {"language":"tr","intent":"stay_availability_request","state":"collecting_missing_field",'
        '"entities":{},"required_questions":[],"tool_calls":[],"notifications":[],"handoff":{"needed":false},'
        '"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"ask_dates"}'
    )

    assert ResponseParser.extract_parser_error(parsed.internal_json) == ""
    assert parsed.internal_json.intent == "stay_availability"
    assert parsed.internal_json.state == "NEEDS_VERIFICATION"


def test_parse_normalizes_runtime_drifted_aliases() -> None:
    """Observed runtime drift aliases should map back to the canonical stay contract."""
    parsed = ResponseParser.parse(
        "Bilgileri not ettim.\n"
        'INTERNAL_JSON: {"language":"tr","intent":"check_availability","state":"awaiting_room_preference",'
        '"entities":{},"required_questions":[],"tool_calls":[{"tool":"booking_availability","args":{}}],"notifications":[],'
        '"handoff":{"needed":false},"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
        '"next_step":"ask_room_type"}'
    )

    assert ResponseParser.extract_parser_error(parsed.internal_json) == ""
    assert parsed.internal_json.intent == "stay_availability"
    assert parsed.internal_json.state == "NEEDS_VERIFICATION"


def test_parse_clamps_unknown_runtime_intent_and_state_to_canonical_contract() -> None:
    """Unknown runtime drift should be clamped onto canonical intent/state values."""
    parsed = ResponseParser.parse(
        "Bilgileri not ettim.\n"
        'INTERNAL_JSON: {"language":"tr","intent":"restaurant_reservation","state":"MISSING_DATE_SELECTION",'
        '"entities":{},"required_questions":[],"tool_calls":[],"notifications":[],'
        '"handoff":{"needed":false},"risk_flags":[],"escalation":{"level":"L0","route_to_role":"NONE"},'
        '"next_step":"ask_date"}'
    )

    assert ResponseParser.extract_parser_error(parsed.internal_json) == ""
    assert parsed.internal_json.intent == "restaurant_booking_create"
    assert parsed.internal_json.state == "NEEDS_VERIFICATION"
