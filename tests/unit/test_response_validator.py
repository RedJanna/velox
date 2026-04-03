"""Unit tests for response validator guardrails."""

from velox.core.response_validator import validate_guest_response
from velox.core.scope_classifier import ScopeDecision
from velox.models.conversation import InternalJSON, LLMResponse


def test_response_validator_uses_fallback_for_empty_message() -> None:
    response = LLMResponse(user_message="", internal_json=InternalJSON(language="tr"))
    validated = validate_guest_response(response, default_language="tr")
    assert "yardimci olmak istiyorum" in validated.user_message.lower()
    assert validated.internal_json.entities.get("response_validator", {}).get("applied") is True


def test_response_validator_blocks_technical_leak() -> None:
    response = LLMResponse(
        user_message="Traceback: Internal Server Error. token=abc123",
        internal_json=InternalJSON(language="en"),
    )
    validated = validate_guest_response(response, default_language="en")
    assert "one short message" in validated.user_message.lower()


def test_response_validator_enforces_out_of_scope_refusal_consistency() -> None:
    response = LLMResponse(
        user_message="Bunu yapamam",
        internal_json=InternalJSON(language="tr"),
    )
    validated = validate_guest_response(
        response,
        default_language="tr",
        scope_decision=ScopeDecision.OUT_OF_SCOPE,
    )
    lowered = validated.user_message.lower()
    assert "dogrudan destek saglayamiyorum" in lowered
    assert "otel hizmetlerimizle ilgili" in lowered
