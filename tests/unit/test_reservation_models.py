"""Unit tests for stay reservation request models."""

from datetime import date

import pytest

from velox.models.reservation import BookingQuoteRequest


def test_booking_quote_request_derives_child_count_from_ages() -> None:
    """Child count should be derived from provided child ages."""
    request = BookingQuoteRequest(
        hotel_id=21966,
        checkin_date=date(2026, 8, 3),
        checkout_date=date(2026, 8, 4),
        adults=2,
        chd_ages=[7],
    )
    assert request.chd_count == 1


def test_booking_quote_request_rejects_inconsistent_child_count() -> None:
    """Mismatched child count and ages should fail validation."""
    with pytest.raises(ValueError):
        BookingQuoteRequest(
            hotel_id=21966,
            checkin_date=date(2026, 8, 3),
            checkout_date=date(2026, 8, 4),
            adults=2,
            chd_count=2,
            chd_ages=[7],
        )
