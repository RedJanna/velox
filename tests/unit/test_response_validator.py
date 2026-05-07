"""Unit tests for response validator guardrails."""

from velox.core.response_validator import validate_guest_response
from velox.core.scope_classifier import ScopeDecision
from velox.models.conversation import InternalJSON, LLMResponse
from velox.models.hotel_profile import BoardType, HotelProfile, LocalizedText


def _hotel_profile_with_board(code: str, tr_name: str, en_name: str = "") -> HotelProfile:
    return HotelProfile(
        hotel_id=21966,
        hotel_name=LocalizedText(tr="Kassandra", en="Kassandra"),
        board_types=[
            BoardType(
                id=1,
                code=code,
                name=LocalizedText(tr=tr_name, en=en_name or tr_name),
            )
        ],
    )


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


def test_response_validator_keeps_unverified_menu_claim_in_automation() -> None:
    response = LLMResponse(
        user_message="Tatli secenekleri olarak baklava ve sutlac onerebilirim.",
        internal_json=InternalJSON(language="tr", tool_calls=[]),
    )

    validated = validate_guest_response(response, default_language="tr")

    lowered = validated.user_message.lower()
    assert "siparis ekranindan" in lowered
    assert "ekibimize iletiyorum" not in lowered
    assert validated.internal_json.state != "HANDOFF"
    assert validated.internal_json.handoff["needed"] is False
    assert validated.internal_json.escalation["level"] == "L0"
    assert "MENU_HALLUCINATION_RISK" not in validated.internal_json.risk_flags
    assert "menu_information_automation_fallback" in validated.internal_json.entities["response_validator"]["rules"]


def test_response_validator_blocks_toolless_stay_price_claim() -> None:
    response = LLMResponse(
        user_message="23-27 Mayis icin Deluxe oda 1081 EUR olarak musaittir.",
        internal_json=InternalJSON(language="tr", intent="stay_quote", tool_calls=[]),
    )

    validated = validate_guest_response(response, default_language="tr")

    assert "1081" not in validated.user_message
    assert validated.internal_json.state == "HANDOFF"
    assert validated.internal_json.handoff["needed"] is True
    assert "UNRESOLVED_CASE" in validated.internal_json.risk_flags
    assert "ungrounded_stay_live_claim_blocked" in validated.internal_json.entities["response_validator"]["rules"]


def test_response_validator_allows_missing_stay_slot_question_without_tools() -> None:
    response = LLMResponse(
        user_message="Hangi tarihler icin musaitlik kontrolu yapmamı istersiniz?",
        internal_json=InternalJSON(
            language="tr",
            intent="stay_availability",
            required_questions=["checkin_date"],
            tool_calls=[],
        ),
    )

    validated = validate_guest_response(response, default_language="tr")

    assert validated.internal_json.state != "HANDOFF"
    assert validated.user_message.startswith("Hangi tarihler")


def test_response_validator_blocks_unverified_campaign_meal_plan_claim() -> None:
    response = LLMResponse(
        user_message=(
            "May\u0131s doneminde kampanyal\u0131 paketlerimizde 2 \u00f6\u011f\u00fcn "
            "(kahvalt\u0131 + ak\u015fam yeme\u011fi) sunulmaktadir."
        ),
        internal_json=InternalJSON(language="tr", intent="other", tool_calls=[]),
    )

    validated = validate_guest_response(
        response,
        default_language="tr",
        hotel_profile=_hotel_profile_with_board("BB", "Oda + Kahvalti", "Bed & Breakfast"),
    )

    lowered = validated.user_message.lower()
    assert "2 ogun" not in lowered
    assert "aksam yemegi" not in lowered
    assert "oda + kahvalti" in lowered
    assert validated.internal_json.state == "HANDOFF"
    assert validated.internal_json.handoff["needed"] is True
    assert validated.internal_json.escalation["route_to_role"] == "ADMIN"
    assert "DATA_INCONSISTENCY" in validated.internal_json.risk_flags
    assert "unsupported_hotel_fact_claim_blocked" in validated.internal_json.entities["response_validator"]["rules"]
    assert any(note.get("to_role") == "ADMIN" for note in validated.internal_json.notifications)


def test_response_validator_blocks_unverified_campaign_claim_without_meal_plan() -> None:
    response = LLMResponse(
        user_message="Mayis kampanyamiz sezon basi avantajlariyla gecerlidir.",
        internal_json=InternalJSON(language="tr", intent="other", tool_calls=[]),
    )

    validated = validate_guest_response(
        response,
        default_language="tr",
        hotel_profile=_hotel_profile_with_board("BB", "Oda + Kahvalti", "Bed & Breakfast"),
    )

    assert "kampanyamiz" not in validated.user_message.lower()
    assert validated.internal_json.state == "HANDOFF"
    assert "DATA_INCONSISTENCY" in validated.internal_json.risk_flags


def test_response_validator_allows_profile_supported_half_board_claim() -> None:
    response = LLMResponse(
        user_message="Yarim pansiyon konseptimizde kahvalti ve aksam yemegi dahildir.",
        internal_json=InternalJSON(language="tr", intent="other", tool_calls=[]),
    )

    validated = validate_guest_response(
        response,
        default_language="tr",
        hotel_profile=_hotel_profile_with_board("HB", "Yarim Pansiyon", "Half Board"),
    )

    assert validated.internal_json.state != "HANDOFF"
    assert "DATA_INCONSISTENCY" not in validated.internal_json.risk_flags
