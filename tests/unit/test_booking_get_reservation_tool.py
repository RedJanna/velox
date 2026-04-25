"""Unit tests for reservation verification tool persistence."""

from __future__ import annotations

import pytest

from velox.tools import booking
from velox.tools.booking import BookingGetReservationTool


class _SnapshotRepository:
    def __init__(self) -> None:
        self.snapshot = None

    async def upsert_external_snapshot(self, snapshot) -> None:
        self.snapshot = snapshot


class _ReservationDetail:
    success = True

    def model_dump(self, *, mode: str) -> dict[str, str | bool]:
        assert mode == "json"
        return {
            "success": True,
            "reservation_id": "RSV-100",
            "voucher_no": "V-100",
            "checkin_date": "2026-07-10",
            "checkout_date": "2026-07-12",
            "state": "Reservation",
            "total_price": "1200.00",
        }


@pytest.mark.asyncio
async def test_booking_get_reservation_persists_minimal_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful lookups are saved without raw phone or guest name fields."""

    async def _fake_get_reservation(**_kwargs):
        return _ReservationDetail()

    repository = _SnapshotRepository()
    monkeypatch.setattr(booking, "get_reservation", _fake_get_reservation)

    result = await BookingGetReservationTool(repository).execute(
        hotel_id=21966,
        contact_phone="+905551112233",
        checkin_date="2026-07-10",
    )

    assert result["reservation_id"] == "RSV-100"
    assert repository.snapshot.lookup_key == "reservation:RSV-100"
    assert repository.snapshot.phone_hash != "+905551112233"
    assert "phone" not in repository.snapshot.snapshot_json
