"""Scenario test S024: restaurant booking flow."""

import pytest

from tests.scenarios.runner import ScenarioRunner


@pytest.mark.asyncio
async def test_s024_restaurant_reservation_flow() -> None:
    """Run S024 restaurant reservation scenario end-to-end with runner."""
    scenario = {
        "code": "S024",
        "name": "Restaurant Reservation",
        "steps": [
            {
                "user": "Merhaba, restoran rezervasyonu yapmak istiyorum",
                "expect_intent": "restaurant_booking_create",
                "expect_state": "INTENT_DETECTED",
                "expect_tool_calls": [],
                "expect_reply_contains": ["tarih", "kisi"],
            },
            {
                "user": "restoran icin 10 Agustos saat 20:00 4 kisi",
                "expect_intent": "restaurant_booking_create",
                "expect_state": "READY_FOR_TOOL",
                "expect_tool_calls": ["restaurant_availability"],
                "expect_reply_contains": ["musaitlik"],
            },
            {
                "user": "restoran icin fiyat teklifini de paylas",
                "expect_intent": "restaurant_booking_create",
                "expect_state": "TOOL_RUNNING",
                "expect_tool_calls": ["restaurant_availability"],
                "expect_reply_contains": ["teklif"],
            },
            {
                "user": "evet restoran rezervasyonunu onayliyorum",
                "expect_intent": "restaurant_booking_create",
                "expect_state": "PENDING_APPROVAL",
                "expect_tool_calls": ["restaurant_create_hold"],
                "expect_reply_contains": ["onaya"],
            },
            {
                "user": "admin onayi geldi restoran",
                "expect_intent": "restaurant_booking_create",
                "expect_state": "CONFIRMED",
                "expect_tool_calls": [],
                "expect_reply_contains": ["kesinlesti"],
            },
        ],
    }
    runner = ScenarioRunner()
    result = await runner.run_scenario(scenario)
    assert result.code == "S024"
    assert result.passed is True
