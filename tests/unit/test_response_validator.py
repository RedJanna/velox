"""Unit tests for response validator guardrails."""

from velox.core.response_validator import validate_guest_response
from velox.core.scope_classifier import ScopeDecision
from velox.models.conversation import InternalJSON, LLMResponse


def test_response_validator_uses_fallback_for_empty_message() -> None:
    response = LLMResponse(user_message="", internal_json=InternalJSON(language="tr"))
    validated = validate_guest_response(response, default_language="tr")
    assert "ekibimize iletiyorum" in validated.user_message.lower()
    assert validated.internal_json.state == "HANDOFF"
    assert validated.internal_json.handoff["needed"] is True
    assert "UNRESOLVED_CASE" in validated.internal_json.risk_flags
    assert validated.internal_json.entities.get("response_validator", {}).get("applied") is True


def test_response_validator_blocks_technical_leak() -> None:
    response = LLMResponse(
        user_message="Traceback: Internal Server Error. token=abc123",
        internal_json=InternalJSON(language="en"),
    )
    validated = validate_guest_response(response, default_language="en")
    assert "forwarding it to our team" in validated.user_message.lower()
    assert validated.internal_json.state == "HANDOFF"
    assert "UNRESOLVED_CASE" in validated.internal_json.risk_flags


def test_response_validator_allows_google_maps_link() -> None:
    response = LLMResponse(
        user_message="Restoran konum linki: https://maps.app.goo.gl/pMiKmhV57YVvAghe6",
        internal_json=InternalJSON(language="tr"),
    )
    validated = validate_guest_response(response, default_language="tr")
    assert "maps.app.goo.gl" in validated.user_message
    assert "yardimci olmak istiyorum" not in validated.user_message.lower()


def test_response_validator_blocks_non_maps_url() -> None:
    response = LLMResponse(
        user_message="Detaylar icin bakin: https://example.com/help-center",
        internal_json=InternalJSON(language="tr"),
    )
    validated = validate_guest_response(response, default_language="tr")
    assert "ekibimize iletiyorum" in validated.user_message.lower()
    assert validated.internal_json.state == "HANDOFF"
    assert "UNRESOLVED_CASE" in validated.internal_json.risk_flags


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


def test_response_validator_blocks_toolless_reservation_commitment() -> None:
    response = LLMResponse(
        user_message="Restoran rezervasyonunuzu olusturuyorum, birazdan tamamliyorum.",
        internal_json=InternalJSON(language="tr", tool_calls=[]),
    )

    validated = validate_guest_response(response, default_language="tr")

    lowered = validated.user_message.lower()
    assert "ilgili ekibimize iletiyorum" in lowered
    assert "rezervasyonunuzu olusturuyorum" not in lowered
    assert validated.internal_json.state == "HANDOFF"
    assert validated.internal_json.handoff["needed"] is True
    assert "PHYSICAL_OPERATION_REQUEST" in validated.internal_json.risk_flags
    assert "toolless_commitment_blocked" in validated.internal_json.entities["response_validator"]["rules"]


def test_response_validator_routes_unverified_menu_claim_to_handoff() -> None:
    response = LLMResponse(
        user_message="Tatli secenekleri olarak baklava ve sutlac onerebilirim.",
        internal_json=InternalJSON(language="tr", tool_calls=[]),
    )

    validated = validate_guest_response(response, default_language="tr")

    assert "ilgili ekibimize iletiyorum" in validated.user_message.lower()
    assert validated.internal_json.state == "HANDOFF"
    assert validated.internal_json.handoff["needed"] is True
    assert "MENU_HALLUCINATION_RISK" in validated.internal_json.risk_flags
