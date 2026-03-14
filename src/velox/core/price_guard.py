"""Price drift policy checks between quote and PMS create stages."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum


class PriceDecision(StrEnum):
    """Decision returned by price-drift policy checks."""

    continue_without_reconfirmation = "CONTINUE_WITHOUT_RECONFIRMATION"
    require_guest_reconfirmation = "REQUIRE_GUEST_RECONFIRMATION"
    reject_due_to_invalid_input = "REJECT_DUE_TO_INVALID_INPUT"


@dataclass(frozen=True, slots=True)
class PriceGuardPolicy:
    """Threshold policy for deciding quote-vs-create drift handling."""

    max_percent_without_reconfirmation: Decimal = Decimal("5.0")
    max_absolute_without_reconfirmation: Decimal = Decimal("25.00")


@dataclass(frozen=True, slots=True)
class PriceGuardResult:
    """Computed decision and diagnostics for quote-vs-create price drift."""

    decision: PriceDecision
    percent_delta: Decimal
    absolute_delta: Decimal


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def evaluate_price_drift(
    *,
    quoted_total: Decimal,
    latest_total: Decimal,
    policy: PriceGuardPolicy | None = None,
) -> PriceGuardResult:
    """Evaluates whether create should continue or require reconfirmation."""
    if quoted_total <= 0 or latest_total <= 0:
        return PriceGuardResult(
            decision=PriceDecision.reject_due_to_invalid_input,
            percent_delta=Decimal("0.00"),
            absolute_delta=Decimal("0.00"),
        )

    active_policy = policy or PriceGuardPolicy()
    absolute_delta = _quantize(abs(latest_total - quoted_total))
    percent_delta = _quantize((absolute_delta / quoted_total) * Decimal("100"))

    if (
        percent_delta <= active_policy.max_percent_without_reconfirmation
        and absolute_delta <= active_policy.max_absolute_without_reconfirmation
    ):
        return PriceGuardResult(
            decision=PriceDecision.continue_without_reconfirmation,
            percent_delta=percent_delta,
            absolute_delta=absolute_delta,
        )

    return PriceGuardResult(
        decision=PriceDecision.require_guest_reconfirmation,
        percent_delta=percent_delta,
        absolute_delta=absolute_delta,
    )
