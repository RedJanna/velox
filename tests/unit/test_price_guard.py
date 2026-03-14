from decimal import Decimal

from velox.core.price_guard import (
    PriceDecision,
    PriceGuardPolicy,
    evaluate_price_drift,
)


def test_price_guard_allows_small_delta() -> None:
    result = evaluate_price_drift(
        quoted_total=Decimal("100.00"),
        latest_total=Decimal("103.00"),
        policy=PriceGuardPolicy(
            max_percent_without_reconfirmation=Decimal("5.0"),
            max_absolute_without_reconfirmation=Decimal("25.00"),
        ),
    )
    assert result.decision is PriceDecision.continue_without_reconfirmation
    assert result.percent_delta == Decimal("3.00")
    assert result.absolute_delta == Decimal("3.00")


def test_price_guard_requires_reconfirmation_on_large_delta() -> None:
    result = evaluate_price_drift(
        quoted_total=Decimal("100.00"),
        latest_total=Decimal("120.00"),
    )
    assert result.decision is PriceDecision.require_guest_reconfirmation
    assert result.percent_delta == Decimal("20.00")
    assert result.absolute_delta == Decimal("20.00")


def test_price_guard_rejects_invalid_totals() -> None:
    result = evaluate_price_drift(
        quoted_total=Decimal("0.00"),
        latest_total=Decimal("120.00"),
    )
    assert result.decision is PriceDecision.reject_due_to_invalid_input

