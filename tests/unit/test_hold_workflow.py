import pytest

from velox.core.hold_workflow import (
    HoldWorkflowEvent,
    HoldWorkflowState,
    apply_hold_transition,
)


def test_hold_workflow_happy_path_until_payment_pending() -> None:
    transition = apply_hold_transition(
        current_state=HoldWorkflowState.pending_approval,
        event=HoldWorkflowEvent.admin_approved,
    )
    assert transition.to_state is HoldWorkflowState.pms_pending

    transition = apply_hold_transition(
        current_state=transition.to_state,
        event=HoldWorkflowEvent.pms_create_succeeded,
    )
    assert transition.to_state is HoldWorkflowState.pms_created

    transition = apply_hold_transition(
        current_state=transition.to_state,
        event=HoldWorkflowEvent.payment_requested,
    )
    assert transition.to_state is HoldWorkflowState.payment_pending


def test_hold_workflow_supports_manual_review_for_uncertain_create() -> None:
    transition = apply_hold_transition(
        current_state=HoldWorkflowState.pms_pending,
        event=HoldWorkflowEvent.reconciliation_uncertain,
    )
    assert transition.to_state is HoldWorkflowState.manual_review


def test_hold_workflow_rejects_invalid_transition() -> None:
    with pytest.raises(ValueError):
        apply_hold_transition(
            current_state=HoldWorkflowState.pending_approval,
            event=HoldWorkflowEvent.payment_succeeded,
        )

