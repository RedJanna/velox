"""Input verification helpers for date, guest, phone, and currency checks."""

from datetime import date

import phonenumbers


def validate_stay_dates(
    checkin_date: date,
    checkout_date: date,
    *,
    today: date | None = None,
) -> bool:
    """Validate stay dates: future-like and checkout strictly after checkin."""
    reference = today or date.today()
    return checkin_date >= reference and checkout_date > checkin_date


def validate_guest_counts(adults: int, chd_ages: list[int] | None = None) -> bool:
    """Validate adult/child counts and child ages."""
    if adults < 1:
        return False
    for age in chd_ages or []:
        if age < 0 or age > 17:
            return False
    return True


def validate_phone_number(phone: str, region: str | None = None) -> bool:
    """Validate international phone number via phonenumbers parser."""
    try:
        parsed = phonenumbers.parse(phone, region)
    except phonenumbers.NumberParseException:
        return False
    return phonenumbers.is_valid_number(parsed)


def validate_currency_code(currency: str) -> bool:
    """Validate ISO-like 3-letter uppercase currency code."""
    return len(currency) == 3 and currency.isalpha() and currency.upper() == currency
