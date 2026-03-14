"""Integration-like tests for admin hold approval event bridging."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from velox.api.middleware.auth import TokenData
from velox.api.routes import admin
from velox.config.constants import Role


class _AcquireContext:
    def __init__(self, connection: "_FakeConnection") -> None:
        self._connection = connection

    async def __aenter__(self) -> "_FakeConnection":
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.hold_row = {
            "hold_id": "S_HOLD_0001",
            "status": "PENDING_APPROVAL",
            "hotel_id": 21966,
        }
        self.approval_row = {"request_id": "APR_1001"}

    async def fetchrow(self, query: str, *args: object) -> dict[str, Any] | None:
        if "FROM stay_holds WHERE hold_id = $1" in query:
            hold_id = str(args[0])
            if hold_id == self.hold_row["hold_id"]:
                return dict(self.hold_row)
            return None
        if "FROM approval_requests" in query and "ORDER BY created_at DESC" in query:
            return dict(self.approval_row)
        raise AssertionError(f"Unsupported fetchrow query: {query}")

    async def execute(self, query: str, *args: object) -> str:
        _ = (query, args)
        return "OK"


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


class _FakeEventProcessor:
    def __init__(self) -> None:
        self.events: list[Any] = []

    async def process_approval_event(self, event: Any) -> dict[str, Any]:
        self.events.append(event)
        return {"approval_request_id": event.approval_request_id, "approved": event.approved}


@pytest.mark.asyncio
async def test_admin_hold_approve_triggers_event_processor() -> None:
    """Approving hold from admin route should delegate to event processor."""
    fake_conn = _FakeConnection()
    fake_processor = _FakeEventProcessor()
    fake_request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                db_pool=_FakePool(fake_conn),
                event_processor=fake_processor,
            )
        )
    )
    user = TokenData(
        user_id=1,
        hotel_id=21966,
        username="ops_admin",
        role=Role.ADMIN,
        display_name="Ops Admin",
    )

    result = await admin.approve_hold(
        hold_id="S_HOLD_0001",
        body=admin.ApproveRequest(notes="ok"),
        request=fake_request,
        user=user,
    )

    assert result["status"] == "approved"
    assert result["hold_id"] == "S_HOLD_0001"
    assert result["result"]["approved"] is True

    assert len(fake_processor.events) == 1
    event = fake_processor.events[0]
    assert event.hotel_id == 21966
    assert event.approval_request_id == "APR_1001"
    assert event.approved is True
    assert event.approved_by_role == Role.ADMIN.value
    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo == UTC
