"""Unit tests for stay draft normalization and validation."""

from datetime import date
from decimal import Decimal

import pytest

from velox.models.reservation import StayDraft


def test_stay_draft_normalizes_phone_name_and_email() -> None:
    """StayDraft should normalize key guest fields."""
    draft = StayDraft(
        checkin_date=date(2026, 7, 10),
        checkout_date=date(2026, 7, 12),
        room_type_id=396094,
        board_type_id=44512,
        rate_type_id=24171,
        rate_code_id=183668,
        total_price_eur=Decimal("320"),
        adults=2,
        guest_name="  Ali   Veli ",
        phone=" 0532 111 22 33 ",
        email="  Ali.Veli@Example.COM ",
    )
    assert draft.guest_name == "Ali Veli"
    assert draft.phone == "+05321112233"
    assert draft.email == "ali.veli@example.com"


def test_stay_draft_rejects_invalid_date_order() -> None:
    """checkout_date must be strictly after checkin_date."""
    with pytest.raises(ValueError, match="checkout_date"):
        StayDraft(
            checkin_date=date(2026, 7, 12),
            checkout_date=date(2026, 7, 12),
            room_type_id=396094,
            board_type_id=44512,
            rate_type_id=24171,
            rate_code_id=183668,
            total_price_eur=Decimal("120"),
            adults=2,
            guest_name="Ali Veli",
            phone="+905321112233",
        )
