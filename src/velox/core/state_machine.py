"""Conversation state transition helpers."""

from velox.config.constants import ConversationState

_TRANSITIONS: dict[tuple[ConversationState, str], ConversationState] = {
    (ConversationState.GREETING, "message_received"): ConversationState.INTENT_DETECTED,
    (ConversationState.INTENT_DETECTED, "missing_slots"): ConversationState.NEEDS_VERIFICATION,
    (ConversationState.NEEDS_VERIFICATION, "slots_filled"): ConversationState.READY_FOR_TOOL,
    (ConversationState.READY_FOR_TOOL, "tool_called"): ConversationState.TOOL_RUNNING,
    (ConversationState.TOOL_RUNNING, "results_presented"): ConversationState.NEEDS_CONFIRMATION,
    (ConversationState.NEEDS_CONFIRMATION, "user_confirmed"): ConversationState.PENDING_APPROVAL,
    (ConversationState.PENDING_APPROVAL, "admin_approved"): ConversationState.CONFIRMED,
}


def next_state(current: ConversationState, event: str) -> ConversationState:
    """Return next state based on current state and domain event."""
    if event == "escalation_triggered":
        return ConversationState.HANDOFF
    return _TRANSITIONS.get((current, event), current)
