"""Scenario test S001: stay booking flow from greeting to approval."""

import pytest

from tests.scenarios.runner import ScenarioRunner


@pytest.mark.asyncio
async def test_s001_hotel_reservation_flow() -> None:
    """Run S001 hotel reservation scenario end-to-end with runner."""
    scenario = {
        "code": "S001",
        "name": "Hotel Reservation",
        "steps": [
            {
                "user": "Merhaba, oda bakmak istiyorum",
                "expect_intent": "stay_availability",
                "expect_state": "INTENT_DETECTED",
                "expect_tool_calls": [],
                "expect_reply_contains": ["tarih", "kisi"],
            },
            {
                "user": "15-18 Temmuz, 2 yetiskin",
                "expect_intent": "other",
                "expect_state": "READY_FOR_TOOL",
                "expect_tool_calls": ["booking_availability"],
                "expect_reply_contains": ["musaitlik"],
            },
            {
                "user": "fiyat teklifini goster",
                "expect_intent": "other",
                "expect_state": "TOOL_RUNNING",
                "expect_tool_calls": ["booking_quote"],
                "expect_reply_contains": ["teklif"],
            },
            {
                "user": "Evet onayliyorum",
                "expect_intent": "other",
                "expect_state": "PENDING_APPROVAL",
                "expect_tool_calls": ["stay_create_hold"],
                "expect_reply_contains": ["onaya"],
            },
            {
                "user": "admin onayi geldi",
                "expect_intent": "other",
                "expect_state": "CONFIRMED",
                "expect_tool_calls": [],
                "expect_reply_contains": ["kesinlesti"],
            },
        ],
    }
    runner = ScenarioRunner()
    result = await runner.run_scenario(scenario)
    assert result.code == "S001"
    assert result.passed is True
