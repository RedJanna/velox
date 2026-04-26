"""Unit tests for escalation matrix evaluation logic."""

from velox.config.constants import EscalationLevel, RiskFlag, Role
from velox.core.pipeline import _filter_special_occasion_intake_flags
from velox.escalation.engine import EscalationEngine
from velox.escalation.risk_detector import detect_risk_flags_from_message
from velox.models.conversation import InternalJSON, LLMResponse


def _engine_with_loaded_matrix() -> EscalationEngine:
    """Build engine and load matrix from configured path."""
    engine = EscalationEngine()
    engine.load_matrix()
    return engine


def test_single_risk_flag_maps_to_expected_level_and_role() -> None:
    """Single risk should map to matrix-defined level and route."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["PAYMENT_CONFUSION"],
        intent="payment_inquiry",
        reference_id="R1",
        conversation_id="C1",
    )
    assert result.level == EscalationLevel.L2
    assert result.route_to_role == Role.SALES


def test_multiple_risk_flags_choose_highest_level() -> None:
    """When multiple flags exist, highest level should win."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["VIP_REQUEST", "LEGAL_REQUEST"],
        intent="other",
        reference_id="R2",
        conversation_id="C2",
    )
    assert result.level == EscalationLevel.L3
    assert result.route_to_role == Role.ADMIN


def test_dedupe_key_generation_is_deterministic() -> None:
    """Dedupe key should be stable and deterministic."""
    key = EscalationEngine._generate_dedupe_key("PAYMENT_CONFUSION", "payment_inquiry", "REF-9")
    assert key == "PAYMENT_CONFUSION|payment_inquiry|REF-9"


def test_l0_flag_returns_no_handoff_actions() -> None:
    """L0 flags should not force handoff actions."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["DATE_INVALID"],
        intent="stay_availability",
        reference_id="R3",
        conversation_id="C3",
    )
    assert result.level == EscalationLevel.L0
    assert "handoff.create_ticket" not in result.actions


def test_l3_flag_includes_ticket_and_notify_actions() -> None:
    """L3 matrix entries should trigger high-priority actions."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["LEGAL_REQUEST"],
        intent="complaint",
        reference_id="R4",
        conversation_id="C4",
    )
    assert result.level == EscalationLevel.L3
    assert "handoff.create_ticket" in result.actions
    assert "notify.send" in result.actions


def test_tool_error_repeat_includes_ticket_and_notify_actions() -> None:
    """Repeated tool failures should always create ticket + notify OPS."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["TOOL_ERROR_REPEAT"],
        intent="stay_booking_create",
        reference_id="R5",
        conversation_id="C5",
    )
    assert result.level == EscalationLevel.L2
    assert result.route_to_role == Role.OPS
    assert "handoff.create_ticket" in result.actions
    assert "notify.send" in result.actions


def test_unresolved_case_routes_to_admin_ticket_and_notify() -> None:
    """Unresolved cases must force ADMIN-visible handoff."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["UNRESOLVED_CASE"],
        intent="other",
        reference_id="R6",
        conversation_id="C6",
    )
    assert result.level == EscalationLevel.L2
    assert result.route_to_role == Role.ADMIN
    assert "handoff.create_ticket" in result.actions
    assert "notify.send" in result.actions


def test_handoff_action_gets_notify_even_if_matrix_omits_it() -> None:
    """Engine safety net should never allow ticket-only handoff actions."""
    engine = _engine_with_loaded_matrix()
    result = engine.evaluate(
        risk_flags=["ANGRY_COMPLAINT"],
        intent="complaint",
        reference_id="R7",
        conversation_id="C7",
    )
    assert "handoff.create_ticket" in result.actions
    assert "notify.send" in result.actions


def test_supported_special_occasion_missing_fields_does_not_force_handoff() -> None:
    """Supported special occasions should collect intake before approval handoff."""
    response = LLMResponse(
        user_message="Elbette, tarih ve rezervasyon numaranızı paylaşır mısınız?",
        internal_json=InternalJSON(
            intent="restaurant_booking_create",
            state="NEEDS_VERIFICATION",
            entities={"party_size": 2},
        ),
    )

    filtered = _filter_special_occasion_intake_flags(
        user_message_text="Doğum günü için 2 kişilik rezervasyon oluşturmak istiyorum",
        llm_response=response,
        risk_flags=[RiskFlag.SPECIAL_EVENT],
    )

    assert RiskFlag.SPECIAL_EVENT not in filtered


def test_supported_special_occasion_complete_intake_keeps_approval_handoff() -> None:
    """Complete supported special occasion intake should still notify a representative."""
    response = LLMResponse(
        user_message="Talebinizi onay için ekibimize iletiyorum.",
        internal_json=InternalJSON(
            intent="restaurant_booking_create",
            state="PENDING_APPROVAL",
            entities={
                "reservation_number": "R12345",
                "special_occasion_date": "2026-05-01",
                "party_size": 2,
                "request_details": "masa süslemesi",
                "is_surprise": True,
                "allergy_or_food_sensitivity": "yok",
            },
        ),
    )

    filtered = _filter_special_occasion_intake_flags(
        user_message_text="Doğum günü için rezervasyon R12345, 01/05, 2 kişi, sürpriz, alerji yok",
        llm_response=response,
        risk_flags=[RiskFlag.SPECIAL_EVENT],
    )

    assert RiskFlag.SPECIAL_EVENT in filtered


def test_direct_handoff_special_occasion_keeps_handoff_flag() -> None:
    """Wedding and similar special organizations must still go to human handoff."""
    response = LLMResponse(
        user_message="Talebinizi ekibimize iletiyorum.",
        internal_json=InternalJSON(intent="special_event_request", state="HANDOFF"),
    )

    filtered = _filter_special_occasion_intake_flags(
        user_message_text="Düğün organizasyonu yapmak istiyorum",
        llm_response=response,
        risk_flags=[RiskFlag.SPECIAL_EVENT],
    )

    assert RiskFlag.SPECIAL_EVENT in filtered


def test_direct_handoff_special_occasion_is_detected_without_organization_word() -> None:
    """Direct-handoff occasion types should be detected from the occasion name itself."""
    flags = detect_risk_flags_from_message("Düğün yapmak istiyorum")

    assert RiskFlag.SPECIAL_EVENT in flags


def test_generic_want_does_not_trigger_physical_operation_request() -> None:
    """Generic 'istiyorum' phrasing should not be treated as a physical operation."""
    flags = detect_risk_flags_from_message(
        "Doğum günü için 2 kişilik rezervasyon oluşturmak istiyorum"
    )

    assert RiskFlag.PHYSICAL_OPERATION_REQUEST not in flags
