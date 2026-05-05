"""Unit tests for season guards on stay and transfer reservation tools."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from velox.tools import booking as booking_tools
from velox.tools import transfer as transfer_tools
from velox.tools.booking import BookingAvailabilityTool, BookingQuoteTool, StayCreateHoldTool
from velox.tools.transfer import TransferCreateHoldTool


class _DummyReservationRepository:
    async def create_hold(self, _hold: object) -> object:
        raise AssertionError("Out-of-season stay hold should not hit repository")


class _DummyTransferRepository:
    async def create_hold(self, _hold: object) -> object:
        raise AssertionError("Out-of-season transfer hold should not hit repository")


@pytest.mark.asyncio
async def test_booking_availability_rejects_out_of_season_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        booking_tools,
        "get_profile",
        lambda _hotel_id: SimpleNamespace(season={"open": "04-20", "close": "11-10"}),
    )
    monkeypatch.setattr(booking_tools, "_hotel_today", lambda _profile: date(2026, 1, 1))

    async def _availability_should_not_run(**_kwargs: object) -> object:
        raise AssertionError("Out-of-season request should stop before Elektraweb availability call")

    monkeypatch.setattr(booking_tools, "availability", _availability_should_not_run)

    result = await BookingAvailabilityTool().execute(
        hotel_id=21966,
        checkin_date=date(2026, 4, 1),
        checkout_date=date(2026, 4, 3),
        adults=2,
    )

    assert result["available"] is False
    assert result["reason"] == "OUT_OF_SEASON"
    assert result["season"] == {"open": "04-20", "close": "11-10"}


@pytest.mark.asyncio
async def test_booking_quote_rejects_out_of_season_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        booking_tools,
        "get_profile",
        lambda _hotel_id: SimpleNamespace(season={"open": "04-20", "close": "11-10"}),
    )
    monkeypatch.setattr(booking_tools, "_hotel_today", lambda _profile: date(2026, 1, 1))

    async def _quote_should_not_run(**_kwargs: object) -> object:
        raise AssertionError("Out-of-season request should stop before Elektraweb quote call")

    monkeypatch.setattr(booking_tools, "quote", _quote_should_not_run)

    result = await BookingQuoteTool().execute(
        hotel_id=21966,
        checkin_date=date(2026, 4, 1),
        checkout_date=date(2026, 4, 3),
        adults=2,
    )

    assert result["available"] is False
    assert result["reason"] == "OUT_OF_SEASON"
    assert result["season"] == {"open": "04-20", "close": "11-10"}


@pytest.mark.asyncio
async def test_booking_availability_rejects_past_checkin_before_elektraweb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        booking_tools,
        "get_profile",
        lambda _hotel_id: SimpleNamespace(timezone="Europe/Istanbul", season={}),
    )
    monkeypatch.setattr(booking_tools, "_hotel_today", lambda _profile: date(2026, 5, 5))

    async def _availability_should_not_run(**_kwargs: object) -> object:
        raise AssertionError("Past-date request should stop before Elektraweb availability call")

    monkeypatch.setattr(booking_tools, "availability", _availability_should_not_run)

    result = await BookingAvailabilityTool().execute(
        hotel_id=21966,
        checkin_date=date(2026, 5, 3),
        checkout_date=date(2026, 5, 5),
        adults=2,
    )

    assert result["available"] is False
    assert result["reason"] == "CHECKIN_DATE_IN_PAST"
    assert result["current_date"] == "2026-05-05"
    assert result["required_questions"] == ["checkin_date"]


@pytest.mark.asyncio
async def test_booking_quote_rejects_past_checkin_before_elektraweb(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        booking_tools,
        "get_profile",
        lambda _hotel_id: SimpleNamespace(timezone="Europe/Istanbul", season={}),
    )
    monkeypatch.setattr(booking_tools, "_hotel_today", lambda _profile: date(2026, 5, 5))

    async def _quote_should_not_run(**_kwargs: object) -> object:
        raise AssertionError("Past-date request should stop before Elektraweb quote call")

    monkeypatch.setattr(booking_tools, "quote", _quote_should_not_run)

    result = await BookingQuoteTool().execute(
        hotel_id=21966,
        checkin_date=date(2026, 5, 3),
        checkout_date=date(2026, 5, 5),
        adults=2,
    )

    assert result["available"] is False
    assert result["reason"] == "CHECKIN_DATE_IN_PAST"
    assert result["next_step"] == "collect_future_checkin_date"
    assert result["required_questions"] == ["checkin_date"]


@pytest.mark.asyncio
async def test_stay_create_hold_rejects_out_of_season_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        booking_tools,
        "get_profile",
        lambda _hotel_id: SimpleNamespace(season={"open": "04-20", "close": "11-10"}, room_types=[]),
    )
    monkeypatch.setattr(booking_tools, "_hotel_today", lambda _profile: date(2026, 1, 1))

    result = await StayCreateHoldTool(_DummyReservationRepository()).execute(
        hotel_id=21966,
        draft={
            "checkin_date": "2026-04-01",
            "checkout_date": "2026-04-03",
            "room_type_id": 60,
            "board_type_id": 2,
            "rate_type_id": 10,
            "rate_code_id": 101,
            "total_price_eur": 200,
            "adults": 2,
            "guest_name": "Ali Veli",
            "phone": "+905551112233",
        },
    )

    assert result["available"] is False
    assert result["reason"] == "OUT_OF_SEASON"
    assert result["season"] == {"open": "04-20", "close": "11-10"}


@pytest.mark.asyncio
async def test_transfer_create_hold_rejects_out_of_season_date(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        transfer_tools,
        "get_profile",
        lambda _hotel_id: SimpleNamespace(season={"open": "04-20", "close": "11-10"}),
    )

    result = await TransferCreateHoldTool(_DummyTransferRepository()).execute(
        hotel_id=21966,
        route="DALAMAN_AIRPORT_TO_HOTEL",
        date="2026-04-01",
        time="12:00",
        pax_count=2,
        guest_name="Ali Veli",
        phone="+905551112233",
    )

    assert result["available"] is False
    assert result["reason"] == "OUT_OF_SEASON"
    assert result["season"] == {"open": "04-20", "close": "11-10"}
