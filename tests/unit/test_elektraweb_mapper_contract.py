"""Non-regression contract tests for Elektraweb response parsing.

These tests intentionally protect quote/availability parsing behavior.
If any of these fail, do not "fix the test" blindly; keep parser compatibility.
"""

from velox.adapters.elektraweb.mapper import parse_availability, parse_quote


def test_quote_parser_contract_accepts_direct_list() -> None:
    """Quote parser must accept a direct list payload from Elektra."""
    raw = [
        {
            "id": "of1",
            "room-type-id": 66,
            "board-type-id": 2,
            "rate-type-id": 10,
            "rate-code-id": 101,
            "price-agency-id": 1,
            "currency-code": "EUR",
            "price": "120.0",
            "discounted-price": "100.0",
            "cancellation-penalty": {},
        }
    ]
    parsed = parse_quote(raw)
    assert len(parsed.offers) == 1
    assert parsed.offers[0].room_type_id == 66


def test_quote_parser_contract_accepts_wrapped_data_list() -> None:
    """Quote parser must accept wrapped list payload under 'data' key."""
    raw = {
        "data": [
            {
                "id": "of1",
                "room-type-id": 66,
                "board-type-id": 2,
                "rate-type-id": 10,
                "rate-code-id": 101,
                "price-agency-id": 1,
                "currency-code": "EUR",
                "price": "120.0",
                "discounted-price": "100.0",
                "cancellation-penalty": {},
            }
        ]
    }
    parsed = parse_quote(raw)
    assert len(parsed.offers) == 1
    assert parsed.offers[0].room_type_id == 66


def test_availability_parser_contract_accepts_wrapped_data_list() -> None:
    """Availability parser must accept wrapped list payload under 'data' key."""
    raw = {
        "data": [
            {"date": "2026-08-10", "room-type-id": 66, "room-to-sell": 3},
            {"date": "2026-08-11", "room-type-id": 66, "room-to-sell": 2},
        ]
    }
    parsed = parse_availability(raw)
    assert parsed.available is True
    assert len(parsed.rows) == 2
    assert parsed.rows[0].room_type_id == 66
