"""Unit tests for restaurant tool edge cases."""

from __future__ import annotations

from datetime import date, time

import pytest

from velox.tools.restaurant import RestaurantCreateHoldTool


class _DummyRestaurantRepository:
    async def get_slot_by_id(self, *, hotel_id: int, slot_id: int) -> dict[str, object] | None:
        assert hotel_id == 21966
        assert slot_id == 42
        return {
            "slot_id": 42,
            "hotel_id": 21966,
            "date": date(2026, 8, 10),
            "time": time(20, 0),
            "area": "outdoor",
            "is_active": True,
        }

    async def get_available_slots(self, **_kwargs: object) -> list[object]:
        raise AssertionError("Daily-capacity-full flow should not query available slots")

    async def create_hold(self, _hold: object) -> object:
        raise AssertionError("Daily-capacity-full flow should not create a hold")


class _DummyApprovalRepository:
    pass


class _DummyNotificationRepository:
    pass


class _DailyCapacityFullSettingsRepository:
    async def get(self, hotel_id: int) -> object:
        assert hotel_id == 21966

        class _Settings:
            reservation_mode = type("_Mode", (), {"value": "AI_RESTAURAN"})()
            min_party_size = 1
            max_party_size = 12

        return _Settings()

    async def check_daily_capacity(self, hotel_id: int, target_date: date, new_party_size: int = 0) -> dict[str, object]:
        assert hotel_id == 21966
        assert target_date == date(2026, 8, 10)
        assert new_party_size == 4
        return {"enabled": True, "allowed": False, "count": 15, "max": 15, "party_size_total": 45, "party_size_max": 45}


@pytest.mark.asyncio
async def test_restaurant_create_hold_daily_capacity_full_returns_handoff_context() -> None:
    """Daily reservation max should preserve collected guest details and request handoff."""
    tool = RestaurantCreateHoldTool(
        restaurant_repository=_DummyRestaurantRepository(),
        approval_repository=_DummyApprovalRepository(),
        notification_repository=_DummyNotificationRepository(),
    )
    tool._settings_repository = _DailyCapacityFullSettingsRepository()  # type: ignore[attr-defined]

    result = await tool.execute(
        hotel_id=21966,
        slot_id=42,
        guest_name="Ali Veli",
        phone="+905551112233",
        party_size=4,
        area="outdoor",
        notes="Window side if possible",
    )

    assert result["available"] is False
    assert result["reason"] == "DAILY_CAPACITY_FULL"
    assert result["suggestion"] == "handoff"
    assert result["handoff_required"] is True
    assert result["count"] == 15
    assert result["max"] == 15
    assert result["collected_reservation_context"] == {
        "date": "2026-08-10",
        "time": "20:00:00",
        "party_size": 4,
        "guest_name": "Ali Veli",
        "phone": "+905551112233",
        "area": "outdoor",
        "notes": "Window side if possible",
    }
