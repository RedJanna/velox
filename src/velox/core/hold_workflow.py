"""Canonical state machine for stay-hold approval and PMS creation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HoldWorkflowState(StrEnum):
    """Stable workflow states for a hold lifecycle."""

    pending_approval = "PENDING_APPROVAL"
    pms_pending = "PMS_PENDING"
    pms_created = "PMS_CREATED"
    payment_pending = "PAYMENT_PENDING"
    confirmed = "CONFIRMED"
    rejected = "REJECTED"
    expired = "EXPIRED"
    pms_failed = "PMS_FAILED"
    payment_expired = "PAYMENT_EXPIRED"
    manual_review = "MANUAL_REVIEW"


class HoldWorkflowEvent(StrEnum):
    """Events that trigger state transitions."""

    admin_approved = "ADMIN_APPROVED"
    admin_rejected = "ADMIN_REJECTED"
    hold_expired = "HOLD_EXPIRED"
    pms_create_started = "PMS_CREATE_STARTED"
    pms_create_succeeded = "PMS_CREATE_SUCCEEDED"
    pms_create_failed = "PMS_CREATE_FAILED"
    payment_requested = "PAYMENT_REQUESTED"
    payment_succeeded = "PAYMENT_SUCCEEDED"
    payment_expired = "PAYMENT_EXPIRED"
    reconciliation_uncertain = "RECONCILIATION_UNCERTAIN"


ALLOWED_TRANSITIONS: dict[HoldWorkflowState, dict[HoldWorkflowEvent, HoldWorkflowState]] = {
    HoldWorkflowState.pending_approval: {
        HoldWorkflowEvent.admin_approved: HoldWorkflowState.pms_pending,
        HoldWorkflowEvent.admin_rejected: HoldWorkflowState.rejected,
        HoldWorkflowEvent.hold_expired: HoldWorkflowState.expired,
    },
    HoldWorkflowState.pms_pending: {
        HoldWorkflowEvent.pms_create_succeeded: HoldWorkflowState.pms_created,
        HoldWorkflowEvent.pms_create_failed: HoldWorkflowState.pms_failed,
        HoldWorkflowEvent.reconciliation_uncertain: HoldWorkflowState.manual_review,
    },
    HoldWorkflowState.pms_created: {
        HoldWorkflowEvent.payment_requested: HoldWorkflowState.payment_pending,
    },
    HoldWorkflowState.payment_pending: {
        HoldWorkflowEvent.payment_succeeded: HoldWorkflowState.confirmed,
        HoldWorkflowEvent.payment_expired: HoldWorkflowState.payment_expired,
    },
}


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Resolved next state for a workflow transition request."""

    from_state: HoldWorkflowState
    event: HoldWorkflowEvent
    to_state: HoldWorkflowState


def apply_hold_transition(
    *,
    current_state: HoldWorkflowState,
    event: HoldWorkflowEvent,
) -> TransitionResult:
    """Applies a transition if allowed; raises ValueError when invalid."""
    transitions = ALLOWED_TRANSITIONS.get(current_state, {})
    next_state = transitions.get(event)
    if next_state is None:
        raise ValueError(
            f"invalid hold transition: {current_state.value} --{event.value}--> ?"
        )
    return TransitionResult(from_state=current_state, event=event, to_state=next_state)
