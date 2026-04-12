"""Regression tests for admin stay-holds routes."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from velox.api.middleware.auth import TokenData
from velox.api.routes import admin_holds
from velox.config.constants import HoldStatus, Role
from velox.models.reservation import StayHold


def _admin_user() -> TokenData:
    return TokenData(
        user_id=1,
        hotel_id=21966,
        username="admin",
        role=Role.ADMIN,
        display_name="Admin",
    )


@pytest.mark.asyncio
async def test_list_stay_holds_count_query_uses_stay_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    """Count query must keep the `sh` alias because archived clause references it."""
    observed: dict[str, Any] = {}

    async def _fake_fetch(_query: str, *_args: object) -> list[dict[str, Any]]:
        return []

    async def _fake_fetchval(query: str, *_args: object) -> int:
        observed["query"] = query
        return 0

    monkeypatch.setattr(admin_holds, "fetch", _fake_fetch)
    monkeypatch.setattr(admin_holds, "fetchval", _fake_fetchval)

    result = await admin_holds.list_stay_holds(
        user=_admin_user(),
        hotel_id=21966,
        status=None,
        reservation_no=None,
        archived=False,
        page=1,
        per_page=30,
    )

    assert result["total"] == 0
    assert "FROM stay_holds sh" in str(observed.get("query", ""))


class _FakeReservationRepository:
    def __init__(self, source_hold: StayHold | None) -> None:
        self._source_hold = source_hold
        self.created_input: StayHold | None = None

    async def get_by_hold_id(self, hold_id: str) -> StayHold | None:
        if self._source_hold is None:
            return None
        if hold_id != self._source_hold.hold_id:
            return None
        return self._source_hold

    async def create_hold(self, hold: StayHold) -> StayHold:
        self.created_input = hold.model_copy(deep=True)
        created = hold.model_copy(deep=True)
        created.hold_id = "S_HOLD_9999"
        created.reservation_no = "VLX-21966-2604-9999"
        return created


@pytest.mark.asyncio
async def test_clone_stay_hold_creates_new_hold_with_fresh_reservation_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_hold = StayHold(
        hold_id="S_HOLD_010",
        hotel_id=21966,
        conversation_id=None,
        draft_json={
            "guest_name": "Udeneme Uudeneme",
            "phone": "+905304498453",
            "email": "gonenomeralperen@gmail.com",
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-06",
            "adults": 2,
            "chd_ages": [11, 12],
            "total_price_eur": 1329.9,
            "room_type_id": 11,
            "board_type_id": 2,
            "rate_type_id": 24178,
            "rate_code_id": 183666,
            "cancel_policy_type": "FREE_CANCEL",
            "notes": "1 adet ekstra yatak talebi",
            "reservation_no": "VLX-21966-2604-0010",
        },
        status=HoldStatus.PAYMENT_PENDING,
        reservation_no="VLX-21966-2604-0010",
    )
    fake_repo = _FakeReservationRepository(source_hold)
    monkeypatch.setattr(admin_holds, "ReservationRepository", lambda: fake_repo)

    result = await admin_holds.clone_stay_hold_from_panel(
        hold_id="S_HOLD_010",
        user=_admin_user(),
    )

    assert result["status"] == "created"
    assert result["hold_id"] == "S_HOLD_9999"
    assert result["reservation_no"] == "VLX-21966-2604-9999"
    assert result["source_hold_id"] == "S_HOLD_010"
    assert result["source_reservation_no"] == "VLX-21966-2604-0010"

    assert fake_repo.created_input is not None
    assert fake_repo.created_input.hotel_id == 21966
    assert fake_repo.created_input.status == HoldStatus.PENDING_APPROVAL
    assert fake_repo.created_input.conversation_id is None
    assert "reservation_no" not in fake_repo.created_input.draft_json
    assert str(fake_repo.created_input.draft_json.get("notes", "")).startswith(
        "Misafirimiz şu notu iletti:"
    )


@pytest.mark.asyncio
async def test_clone_stay_hold_returns_404_when_source_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_repo = _FakeReservationRepository(source_hold=None)
    monkeypatch.setattr(admin_holds, "ReservationRepository", lambda: fake_repo)

    with pytest.raises(HTTPException) as exc:
        await admin_holds.clone_stay_hold_from_panel(
            hold_id="S_HOLD_404",
            user=_admin_user(),
        )

    assert exc.value.status_code == 404
