from velox.core.idempotency import (
    IDEMPOTENCY_NAMESPACE_APPROVAL,
    IDEMPOTENCY_NAMESPACE_CREATE,
    IdempotencyInput,
    build_idempotency_key,
)


def test_build_idempotency_key_is_deterministic() -> None:
    payload = IdempotencyInput(
        namespace=IDEMPOTENCY_NAMESPACE_APPROVAL,
        reference_id="S_HOLD_00010",
        hotel_id=21966,
    )

    assert build_idempotency_key(payload) == build_idempotency_key(payload)


def test_build_idempotency_key_changes_by_namespace() -> None:
    approval = IdempotencyInput(
        namespace=IDEMPOTENCY_NAMESPACE_APPROVAL,
        reference_id="S_HOLD_00010",
        hotel_id=21966,
    )
    create = IdempotencyInput(
        namespace=IDEMPOTENCY_NAMESPACE_CREATE,
        reference_id="S_HOLD_00010",
        hotel_id=21966,
    )

    assert build_idempotency_key(approval) != build_idempotency_key(create)
