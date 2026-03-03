"""Unit tests for slot and input verification helpers."""

from datetime import date

from velox.core.verification import (
    validate_currency_code,
    validate_guest_counts,
    validate_phone_number,
    validate_stay_dates,
)


def test_date_validation_requires_future_and_checkout_after_checkin() -> None:
    """Stay date validation should enforce chronological order."""
    today = date(2026, 1, 10)
    assert validate_stay_dates(date(2026, 1, 11), date(2026, 1, 13), today=today) is True
    assert validate_stay_dates(date(2026, 1, 11), date(2026, 1, 11), today=today) is False
    assert validate_stay_dates(date(2026, 1, 9), date(2026, 1, 11), today=today) is False


def test_guest_count_validation_for_adults_and_child_ages() -> None:
    """Guest count validation should reject invalid adults and child ages."""
    assert validate_guest_counts(adults=2, chd_ages=[3, 7]) is True
    assert validate_guest_counts(adults=0, chd_ages=[]) is False
    assert validate_guest_counts(adults=2, chd_ages=[-1]) is False
    assert validate_guest_counts(adults=2, chd_ages=[18]) is False


def test_phone_number_validation_for_international_format() -> None:
    """Phone validator should accept valid E.164-like input."""
    assert validate_phone_number("+905332503277") is True
    assert validate_phone_number("12345") is False


def test_currency_code_validation_iso_like() -> None:
    """Currency validation should enforce 3 uppercase alphabetic chars."""
    assert validate_currency_code("EUR") is True
    assert validate_currency_code("TRY") is True
    assert validate_currency_code("usd") is False
    assert validate_currency_code("EURO") is False
