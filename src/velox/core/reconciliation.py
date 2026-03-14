"""Reconciliation decision rules for uncertain supplier create outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReconciliationAction(StrEnum):
    """Action to execute after evaluating supplier create uncertainty."""

    NOOP = "noop"
    MARK_CREATED = "mark_created"
    RETRY_CREATE = "retry_create"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True, slots=True)
class ReconciliationInput:
    """Signals observed from create + readback attempts."""

    create_http_timeout: bool
    create_response_success: bool
    reservation_found_by_id: bool
    reservation_found_by_voucher: bool
    readback_attempts_exhausted: bool


def decide_reconciliation_action(payload: ReconciliationInput) -> ReconciliationAction:
    """Returns deterministic action for uncertain create outcomes."""
    if payload.create_response_success:
        return ReconciliationAction.MARK_CREATED

    if payload.reservation_found_by_id or payload.reservation_found_by_voucher:
        return ReconciliationAction.MARK_CREATED

    if payload.create_http_timeout and not payload.readback_attempts_exhausted:
        return ReconciliationAction.NOOP

    if payload.create_http_timeout and payload.readback_attempts_exhausted:
        return ReconciliationAction.MANUAL_REVIEW

    if payload.readback_attempts_exhausted:
        return ReconciliationAction.RETRY_CREATE

    return ReconciliationAction.NOOP
