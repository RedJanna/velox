"""Integration-like tests for admin stay cancellation route."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from velox.api.middleware.auth import TokenData
from velox.api.routes import admin
from velox.config.constants import Role


class _AcquireContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.hold_row = {
            "hold_id": "S_HOLD_0002",
            "status": "CONFIRMED",
            "hotel_id": 21966,
            "pms_reservation_id": "RES-9002",
            "voucher_no": "V-9002",
        }
        self.execute_calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetchrow(self, query: str, *args: object) -> dict[str, Any] | None:
        if "FROM stay_holds WHERE hold_id = $1" in query:
            hold_id = str(args[0])
            if hold_id == self.hold_row["hold_id"]:
                return dict(self.hold_row)
            return None
        raise AssertionError(f"Unsupported fetchrow query: {query}")

    async def execute(self, query: str, *args: object) -> str:
        self.execute_calls.append((query, args))
        return "OK"


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


@pytest.mark.asyncio
async def test_admin_cancel_hold_reservation_calls_elektra_and_updates_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_conn = _FakeConnection()
    captured: list[dict[str, object]] = []

    async def _fake_cancel_reservation(*, hotel_id: int, reservation_id: str, reason: str) -> dict[str, object]:
        captured.append({"hotel_id": hotel_id, "reservation_id": reservation_id, "reason": reason})
        return {"ok": True}

    monkeypatch.setattr(admin, "cancel_reservation", _fake_cancel_reservation)

    fake_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=_FakePool(fake_conn))))
    user = TokenData(
        user_id=1,
        hotel_id=21966,
        username="ops_admin",
        role=Role.ADMIN,
        display_name="Ops Admin",
    )

    result = await admin.cancel_hold_reservation(
        hold_id="S_HOLD_0002",
        body=admin.CancelReservationRequest(reason="guest_request"),
        request=fake_request,
        user=user,
    )

    assert result["status"] == "cancelled"
    assert result["reservation_id"] == "RES-9002"
    assert result["voucher_no"] == "V-9002"
    assert captured == [{"hotel_id": 21966, "reservation_id": "RES-9002", "reason": "guest_request"}]
    assert any(args[1] == "CANCELLED" for _query, args in fake_conn.execute_calls)


@pytest.mark.asyncio
async def test_admin_cancel_hold_reservation_resolves_reservation_id_from_voucher(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_conn = _FakeConnection()
    fake_conn.hold_row["pms_reservation_id"] = None
    fake_conn.hold_row["voucher_no"] = "V-4455"
    captured: list[dict[str, object]] = []

    async def _fake_get_reservation(*, hotel_id: int, voucher_no: str, reservation_id: str | None = None):
        _ = reservation_id
        return SimpleNamespace(reservation_id="RES-4455", voucher_no=voucher_no)

    async def _fake_cancel_reservation(*, hotel_id: int, reservation_id: str, reason: str) -> dict[str, object]:
        captured.append({"hotel_id": hotel_id, "reservation_id": reservation_id, "reason": reason})
        return {"ok": True}

    monkeypatch.setattr(admin, "get_reservation", _fake_get_reservation)
    monkeypatch.setattr(admin, "cancel_reservation", _fake_cancel_reservation)

    fake_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=_FakePool(fake_conn))))
    user = TokenData(
        user_id=1,
        hotel_id=21966,
        username="ops_admin",
        role=Role.ADMIN,
        display_name="Ops Admin",
    )

    result = await admin.cancel_hold_reservation(
        hold_id="S_HOLD_0002",
        body=admin.CancelReservationRequest(reason="guest_request"),
        request=fake_request,
        user=user,
    )

    assert result["status"] == "cancelled"
    assert result["reservation_id"] == "RES-4455"
    assert captured == [{"hotel_id": 21966, "reservation_id": "RES-4455", "reason": "guest_request"}]
