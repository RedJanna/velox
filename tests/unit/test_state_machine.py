"""Unit tests for conversation state transitions."""

from velox.config.constants import ConversationState
from velox.core.state_machine import next_state


def test_state_sequence_from_greeting_to_pending_approval() -> None:
    """Happy-path sequence should follow the expected state chain."""
    state = ConversationState.GREETING
    state = next_state(state, "message_received")
    assert state == ConversationState.INTENT_DETECTED
    state = next_state(state, "missing_slots")
    assert state == ConversationState.NEEDS_VERIFICATION
    state = next_state(state, "slots_filled")
    assert state == ConversationState.READY_FOR_TOOL
    state = next_state(state, "tool_called")
    assert state == ConversationState.TOOL_RUNNING
    state = next_state(state, "results_presented")
    assert state == ConversationState.NEEDS_CONFIRMATION
    state = next_state(state, "user_confirmed")
    assert state == ConversationState.PENDING_APPROVAL


def test_pending_approval_to_confirmed_on_admin_approved() -> None:
    """Admin approval should move state to CONFIRMED."""
    state = next_state(ConversationState.PENDING_APPROVAL, "admin_approved")
    assert state == ConversationState.CONFIRMED


def test_any_state_transitions_to_handoff_on_escalation() -> None:
    """Escalation trigger should force HANDOFF regardless of current state."""
    assert next_state(ConversationState.GREETING, "escalation_triggered") == ConversationState.HANDOFF
    assert next_state(ConversationState.TOOL_RUNNING, "escalation_triggered") == ConversationState.HANDOFF
