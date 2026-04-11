"""Unit tests for customer-visible reservation note formatting."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from velox.tools import booking as booking_tools
from velox.tools import transfer as transfer_tools
from velox.tools.booking import StayCreateHoldTool
from velox.tools.transfer import TransferCreateHoldTool
from velox.utils.customer_notes import format_customer_visible_note


def test_format_customer_visible_note_wraps_fragment() -> None:
    assert (
        format_customer_visible_note("window side if possible")
        == "Misafirimiz şu notu iletti: Window side if possible."
    )


def test_format_customer_visible_note_drops_empty_markers() -> None:
    assert format_customer_visible_note("No special request") == ""
    assert format_customer_visible_note("özel istek yok") == ""


def test_format_customer_visible_note_rewrites_internal_jargon() -> None:
    note = format_customer_visible_note("ops handoff admin, pms issue")
    assert note == (
        "Misafirimiz şu notu iletti: Operasyon ekibi ilgili ekip yönlendirmesi "
        "yetkili ekip, rezervasyon sistemi issue."
    )


class _CaptureReservationRepository:
    def __init__(self) -> None:
        self.last_hold: Any = None

    async def create_hold(self, hold: Any) -> Any:
        self.last_hold = hold
        return SimpleNamespace(
            hold_id="S_HOLD_1001",
            status=SimpleNamespace(value="PENDING_APPROVAL"),
        )


class _CaptureTransferRepository:
    def __init__(self) -> None:
        self.last_hold: Any = None

    async def create_hold(self, hold: Any) -> Any:
        self.last_hold = hold
        return SimpleNamespace(
            hold_id="TR_HOLD_1001",
            status=SimpleNamespace(value="PENDING_APPROVAL"),
            route=hold.route,
            date=hold.date,
            time=hold.time,
            pax_count=hold.pax_count,
            guest_name=hold.guest_name,
            phone=hold.phone,
            flight_no=hold.flight_no,
            vehicle_type=hold.vehicle_type,
            baby_seat=hold.baby_seat,
            price_eur=hold.price_eur,
            notes=hold.notes,
        )


class _DummyApprovalTool:
    async def execute(self, **_kwargs: Any) -> dict[str, Any]:
        return {"approval_request_id": "APR_TR_1001", "status": "REQUESTED"}


@pytest.mark.asyncio
async def test_stay_create_hold_formats_customer_visible_note_before_save(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _CaptureReservationRepository()
    monkeypatch.setattr(booking_tools, "get_profile", lambda _hotel_id: None)

    result = await StayCreateHoldTool(repository).execute(
        hotel_id=21966,
        draft={
            "checkin_date": "2026-08-01",
            "checkout_date": "2026-08-03",
            "room_type_id": 60,
            "board_type_id": 2,
            "rate_type_id": 10,
            "rate_code_id": 101,
            "total_price_eur": 450,
            "adults": 2,
            "guest_name": "Ali Veli",
            "phone": "+905551112233",
            "notes": "erken giris mumkunse",
        },
    )

    assert repository.last_hold is not None
    assert repository.last_hold.draft_json["notes"] == "Misafirimiz şu notu iletti: Erken giris mumkunse."
    assert result["stay_hold_id"] == "S_HOLD_1001"


@pytest.mark.asyncio
async def test_transfer_create_hold_formats_customer_visible_note_before_save(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _CaptureTransferRepository()
    tool = TransferCreateHoldTool(repository, _DummyApprovalTool())
    monkeypatch.setattr(transfer_tools, "get_profile", lambda _hotel_id: None)

    async def _fake_info(**_kwargs: Any) -> dict[str, Any]:
        return {
            "route": "DALAMAN_AIRPORT_TO_HOTEL",
            "duration_min": 60,
            "price_eur": 45,
            "vehicle_type": "sedan",
            "max_pax": 4,
            "baby_seat_available": True,
            "notes": "",
        }

    tool._info_tool.execute = _fake_info  # type: ignore[method-assign]

    result = await tool.execute(
        hotel_id=21966,
        route="DALAMAN_AIRPORT_TO_HOTEL",
        date="2026-08-01",
        time="12:30",
        pax_count=2,
        guest_name="Ayse Yilmaz",
        phone="+905551112244",
        notes="flight delay nedeniyle 20 dk gec gelebiliriz",
    )

    assert repository.last_hold is not None
    assert repository.last_hold.notes == (
        "Misafirimiz şu notu iletti: Flight delay nedeniyle 20 dk gec gelebiliriz."
    )
    assert result["transfer_hold_id"] == "TR_HOLD_1001"
    assert result["approval_request_id"] == "APR_TR_1001"
    assert result["approval_status"] == "REQUESTED"
    assert result.get("ops_notification", {}).get("reason") == "FLIGHT_DELAY_REPORTED"
