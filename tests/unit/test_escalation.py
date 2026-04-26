"""Unit tests for escalation matrix evaluation logic."""

from velox.config.constants import EscalationLevel, Role
from velox.escalation.engine import EscalationEngine


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
