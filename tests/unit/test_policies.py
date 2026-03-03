"""Unit tests for business policy helper rules."""

from datetime import date
from decimal import Decimal

from velox.policies.rules import (
    free_cancel_refund_deadline,
    prepayment_due_mode,
    resolve_rate_type,
    restaurant_group_booking_required,
    scheduled_prepayment_date,
    select_transfer_vehicle,
)


def test_free_cancel_policy_sets_scheduled_prepayment_7_days_before() -> None:
    """FREE_CANCEL should schedule prepayment seven days before check-in."""
    checkin = date(2026, 8, 20)
    assert prepayment_due_mode("FREE_CANCEL") == "SCHEDULED"
    assert scheduled_prepayment_date(checkin) == date(2026, 8, 13)


def test_non_refundable_policy_requires_immediate_prepayment() -> None:
    """NON_REFUNDABLE should require immediate prepayment."""
    assert prepayment_due_mode("NON_REFUNDABLE") == "NOW"


def test_free_cancel_refund_deadline_is_5_days_before_checkin() -> None:
    """Refund deadline helper should return checkin-5 days."""
    assert free_cancel_refund_deadline(date(2026, 8, 20)) == date(2026, 8, 15)


def test_rate_mapping_resolution_for_cancel_policy_types() -> None:
    """Rate mapping helper should resolve configured rate type ids."""
    mapping = {
        "FREE_CANCEL": {"rate_type_id": 10},
        "NON_REFUNDABLE": {"rate_type_id": 11},
    }
    assert resolve_rate_type(mapping, "FREE_CANCEL") == 10
    assert resolve_rate_type(mapping, "NON_REFUNDABLE") == 11


def test_transfer_pricing_vehicle_selection_based_on_pax() -> None:
    """Transfer helper should switch to oversize vehicle when needed."""
    route = {
        "vehicle_type": "Vito",
        "price_eur": 75,
        "max_pax": 7,
        "oversize_vehicle": {"type": "Sprinter", "price_eur": 100, "min_pax": 8, "max_pax": 14},
    }
    vehicle_std, price_std = select_transfer_vehicle(route, pax_count=6)
    vehicle_ovr, price_ovr = select_transfer_vehicle(route, pax_count=9)
    assert (vehicle_std, price_std) == ("Vito", Decimal("75"))
    assert (vehicle_ovr, price_ovr) == ("Sprinter", Decimal("100"))


def test_restaurant_group_booking_threshold_triggers_escalation() -> None:
    """Party size above max AI threshold should require group-booking escalation."""
    assert restaurant_group_booking_required(party_size=9, max_ai_party_size=8) is True
    assert restaurant_group_booking_required(party_size=8, max_ai_party_size=8) is False
