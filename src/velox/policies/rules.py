"""Business rule helpers for payment, rate mapping, transfer, and restaurant."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any


def prepayment_due_mode(cancel_policy_type: str) -> str:
    """Resolve payment due mode from cancel policy type."""
    return "NOW" if cancel_policy_type.upper() == "NON_REFUNDABLE" else "SCHEDULED"


def scheduled_prepayment_date(checkin_date: date) -> date:
    """Return prepayment date for FREE_CANCEL policy (checkin - 7 days)."""
    return checkin_date - timedelta(days=7)


def free_cancel_refund_deadline(checkin_date: date) -> date:
    """Return refund deadline date for FREE_CANCEL policy (checkin - 5 days)."""
    return checkin_date - timedelta(days=5)


def resolve_rate_type(rate_mapping: dict[str, Any], cancel_policy_type: str) -> int:
    """Resolve rate_type_id for given policy from profile rate mapping."""
    mapping = rate_mapping.get(cancel_policy_type.upper(), {})
    return int(mapping.get("rate_type_id", 0))


def select_transfer_vehicle(route: dict[str, Any], pax_count: int) -> tuple[str, Decimal]:
    """Select transfer vehicle and price according to pax capacity rules."""
    max_pax = int(route.get("max_pax", 0))
    if pax_count <= max_pax:
        return str(route.get("vehicle_type", "")), Decimal(str(route.get("price_eur", 0)))

    oversize = route.get("oversize_vehicle") or {}
    min_pax = int(oversize.get("min_pax", max_pax + 1))
    max_oversize = int(oversize.get("max_pax", 50))
    if pax_count < min_pax or pax_count > max_oversize:
        raise ValueError("pax_count_exceeds_transfer_capacity")

    vehicle = str(oversize.get("type", "oversize"))
    price = Decimal(str(oversize.get("price_eur", route.get("price_eur", 0))))
    return vehicle, price


def restaurant_group_booking_required(party_size: int, max_ai_party_size: int = 8) -> bool:
    """Return True when party size requires GROUP_BOOKING escalation."""
    return party_size > max_ai_party_size
