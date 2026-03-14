from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from velox.core.event_processor import EventProcessor
from velox.core.idempotency import IDEMPOTENCY_NAMESPACE_APPROVAL, IdempotencyInput, build_idempotency_key
from velox.models.webhook_events import ApprovalEvent


class _AcquireContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


class _FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def dispatch(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((tool_name, kwargs))
        if tool_name == "booking_create_reservation":
            return {"reservation_id": "RSV-1", "voucher_no": "V-1"}
        if tool_name == "payment_request_prepayment":
            return {"payment_request_id": "PAY-1", "status": "REQUESTED"}
        raise AssertionError(f"unexpected tool: {tool_name}")


class _FakeConnection:
    def __init__(self, hold_row: dict[str, Any]) -> None:
        self._hold_row = hold_row
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    async def fetchrow(self, query: str, *args: object, timeout: float | None = None) -> dict[str, Any] | None:
        _ = timeout
        if "FROM approval_requests" in query:
            return {
                "request_id": "APR-1",
                "hotel_id": int(args[1]),
                "approval_type": "STAY",
                "reference_id": "S_HOLD_0001",
            }
        if "FROM stay_holds" in query:
            return dict(self._hold_row)
        raise AssertionError(f"unsupported fetchrow query: {query}")

    async def execute(self, query: str, *args: object, timeout: float | None = None) -> str:
        _ = timeout
        self.executed.append((query, tuple(args)))
        return "UPDATE 1"


def _build_processor(
    hold_row: dict[str, Any],
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[EventProcessor, _FakeConnection, _FakeDispatcher]:
    connection = _FakeConnection(hold_row)
    dispatcher = _FakeDispatcher()
    processor = EventProcessor(db_pool=_FakePool(connection), dispatcher=dispatcher)
    monkeypatch.setattr(processor, "_append_assistant_message", _noop_async)
    return processor, connection, dispatcher


async def _noop_async(*_args: Any, **_kwargs: Any) -> None:
    return None


@pytest.mark.asyncio
async def test_process_approval_event_skips_duplicate_stay_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_idempotency_key = build_idempotency_key(
        IdempotencyInput(
            namespace=IDEMPOTENCY_NAMESPACE_APPROVAL,
            reference_id="S_HOLD_0001",
            hotel_id=21966,
        )
    )
    hold_row = {
        "hold_id": "S_HOLD_0001",
        "hotel_id": 21966,
        "conversation_id": None,
        "status": "PAYMENT_PENDING",
        "approval_idempotency_key": existing_idempotency_key,
        "draft_json": {"phone": "", "total_price_eur": 100, "currency_display": "EUR"},
    }
    processor, _conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["duplicate"] is True
    assert dispatcher.calls == []


@pytest.mark.asyncio
async def test_process_approval_event_stay_moves_to_payment_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold_row = {
        "hold_id": "S_HOLD_0001",
        "hotel_id": 21966,
        "conversation_id": None,
        "status": "PENDING_APPROVAL",
        "approval_idempotency_key": None,
        "draft_json": {
            "phone": "",
            "checkin_date": "2026-09-10",
            "total_price_eur": 200,
            "currency_display": "EUR",
            "cancel_policy_type": "NON_REFUNDABLE",
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["status"] == "processed"
    tool_names = [name for name, _ in dispatcher.calls]
    assert tool_names == ["booking_create_reservation", "payment_request_prepayment"]

    status_updates = [
        args[1]
        for query, args in conn.executed
        if "UPDATE stay_holds" in query and "SET status = $2" in query and len(args) >= 2
    ]
    assert "PMS_PENDING" in status_updates
    assert "PMS_CREATED" in status_updates
    assert "PAYMENT_PENDING" in status_updates
