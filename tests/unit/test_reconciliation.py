from velox.core.reconciliation import (
    ReconciliationAction,
    ReconciliationInput,
    decide_reconciliation_action,
)


def test_reconciliation_marks_created_when_readback_finds_reservation() -> None:
    result = decide_reconciliation_action(
        ReconciliationInput(
            create_http_timeout=True,
            create_response_success=False,
            reservation_found_by_id=True,
            reservation_found_by_voucher=False,
            readback_attempts_exhausted=False,
        )
    )

    assert result is ReconciliationAction.MARK_CREATED


def test_reconciliation_moves_to_manual_review_on_timeout_after_exhaustion() -> None:
    result = decide_reconciliation_action(
        ReconciliationInput(
            create_http_timeout=True,
            create_response_success=False,
            reservation_found_by_id=False,
            reservation_found_by_voucher=False,
            readback_attempts_exhausted=True,
        )
    )

    assert result is ReconciliationAction.MANUAL_REVIEW


def test_reconciliation_requests_retry_when_non_timeout_and_unresolved() -> None:
    result = decide_reconciliation_action(
        ReconciliationInput(
            create_http_timeout=False,
            create_response_success=False,
            reservation_found_by_id=False,
            reservation_found_by_voucher=False,
            readback_attempts_exhausted=True,
        )
    )

    assert result is ReconciliationAction.RETRY_CREATE

