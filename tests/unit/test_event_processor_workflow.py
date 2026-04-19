from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import orjson
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
        self.create_result: dict[str, Any] = {"reservation_id": "RSV-1", "voucher_no": "V-1"}
        self.readback_result: dict[str, Any] = {"reservation_id": "RSV-1", "voucher_no": "V-1"}

    async def dispatch(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((tool_name, kwargs))
        if tool_name == "booking_create_reservation":
            return dict(self.create_result)
        if tool_name == "booking_get_reservation":
            return dict(self.readback_result)
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
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)

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
    assert tool_names == ["booking_create_reservation", "booking_get_reservation", "payment_request_prepayment"]

    status_updates = [
        args[1]
        for query, args in conn.executed
        if "UPDATE stay_holds" in query and "SET status = $2" in query and len(args) >= 2
    ]
    assert "PMS_PENDING" in status_updates
    assert "PMS_CREATED" in status_updates
    assert "PAYMENT_PENDING" in status_updates


@pytest.mark.asyncio
async def test_process_approval_event_stay_missing_reservation_identifiers_goes_manual_review(
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
            "cancel_policy_type": "FREE_CANCEL",
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.create_result = {"reservation_id": "", "voucher_no": ""}

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["status"] == "processed"
    assert result["reconciliation_action"] == "manual_review"
    tool_names = [name for name, _ in dispatcher.calls]
    assert tool_names == ["booking_create_reservation"]

    status_updates = [
        args[1]
        for query, args in conn.executed
        if "UPDATE stay_holds" in query and "SET status = $2" in query and len(args) >= 2
    ]
    assert "PMS_PENDING" in status_updates
    assert "MANUAL_REVIEW" in status_updates


@pytest.mark.asyncio
async def test_process_approval_event_stay_create_reservation_id_without_voucher_uses_readback_by_id(
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
            "cancel_policy_type": "FREE_CANCEL",
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.create_result = {"reservation_id": "TMP-ONLY", "voucher_no": ""}
    dispatcher.readback_result = {"reservation_id": "TMP-ONLY", "voucher_no": ""}

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["status"] == "processed"
    assert "reconciliation_action" not in result
    tool_names = [name for name, _ in dispatcher.calls]
    assert tool_names == ["booking_create_reservation", "booking_get_reservation", "payment_request_prepayment"]
    clear_manual_reason_updates = [
        query
        for query, _args in conn.executed
        if "SET manual_review_reason = NULL" in query
    ]
    assert clear_manual_reason_updates


@pytest.mark.asyncio
async def test_process_approval_event_manual_review_status_is_not_treated_as_duplicate(
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
        "status": "MANUAL_REVIEW",
        "approval_idempotency_key": existing_idempotency_key,
        "draft_json": {
            "phone": "",
            "checkin_date": "2026-09-10",
            "total_price_eur": 200,
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
        },
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

    assert result.get("duplicate") is not True
    tool_names = [name for name, _ in dispatcher.calls]
    assert "booking_create_reservation" in tool_names


@pytest.mark.asyncio
async def test_process_approval_event_does_not_persist_unverified_create_identifier(
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
            "checkout_date": "2026-09-12",
            "adults": 2,
            "room_type_id": 99,
            "board_type_id": 2,
            "rate_type_id": 11,
            "rate_code_id": 101,
            "price_agency_id": 777,
            "total_price_eur": 200,
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.create_result = {"reservation_id": "RSV-9", "voucher_no": "V-9"}
    dispatcher.readback_result = {}

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["reconciliation_action"] == "manual_review"
    persisted_ids = [
        args[1:]
        for query, args in conn.executed
        if "SET pms_reservation_id = COALESCE($2, pms_reservation_id)" in query
    ]
    assert persisted_ids == []
    cleared_ids = [
        args
        for query, args in conn.executed
        if "SET pms_reservation_id = NULL" in query
    ]
    assert ("S_HOLD_0001",) in cleared_ids


@pytest.mark.asyncio
async def test_process_approval_event_persists_verified_readback_voucher_only(
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
            "checkout_date": "2026-09-12",
            "adults": 2,
            "room_type_id": 99,
            "board_type_id": 2,
            "rate_type_id": 11,
            "rate_code_id": 101,
            "price_agency_id": 777,
            "total_price_eur": 200,
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.create_result = {"reservation_id": "TMP-9", "voucher_no": "V-9"}
    dispatcher.readback_result = {"reservation_id": "TMP-9", "voucher_no": "V-9"}

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    await processor.process_approval_event(event)

    persisted_ids = [
        args[1:]
        for query, args in conn.executed
        if "SET pms_reservation_id = COALESCE($2, pms_reservation_id)" in query
    ]
    assert ("TMP-9", "V-9") in persisted_ids


@pytest.mark.asyncio
async def test_process_approval_event_decodes_string_draft_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold_row = {
        "hold_id": "S_HOLD_0001",
        "hotel_id": 21966,
        "reservation_no": "VLX-21966-2604-0004",
        "conversation_id": None,
        "status": "PENDING_APPROVAL",
        "approval_idempotency_key": None,
        "draft_json": orjson.dumps(
            {
                "phone": "+905301112233",
                "guest_name": "Test User",
                "checkin_date": "2026-09-10",
                "checkout_date": "2026-09-12",
                "adults": 2,
                "room_type_id": 99,
                "board_type_id": 2,
                "rate_type_id": 11,
                "rate_code_id": 101,
                "price_agency_id": 777,
                "total_price_eur": 200,
                "currency_display": "EUR",
                "cancel_policy_type": "FREE_CANCEL",
            }
        ).decode(),
    }
    processor, _conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    await processor.process_approval_event(event)

    create_call = dispatcher.calls[0]
    assert create_call[0] == "booking_create_reservation"
    assert create_call[1]["draft"]["guest_name"] == "Test User"
    assert create_call[1]["draft"]["room_type_id"] == 99
    assert create_call[1]["draft"]["reservation_no"] == "VLX-21966-2604-0004"


@pytest.mark.asyncio
async def test_process_approval_event_stay_readback_room_type_mismatch_goes_manual_review(
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
            "cancel_policy_type": "FREE_CANCEL",
            "room_type_id": 396096,
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.readback_result = {
        "reservation_id": "RSV-1",
        "voucher_no": "V-1",
        "total_price": 200,
        "raw_data": {"room_type_id": 396097},
    }

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["status"] == "processed"
    assert result["reconciliation_action"] == "manual_review"
    assert [name for name, _ in dispatcher.calls] == ["booking_create_reservation", "booking_get_reservation"]
    assert any(
        "SET manual_review_reason = $2" in query and args[1] == "create_readback_mismatch"
        for query, args in conn.executed
    )


@pytest.mark.asyncio
async def test_process_approval_event_stay_readback_price_mismatch_goes_manual_review(
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
            "cancel_policy_type": "FREE_CANCEL",
            "room_type_id": 396096,
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.readback_result = {
        "reservation_id": "RSV-1",
        "voucher_no": "V-1",
        "total_price": 255,
        "raw_data": {"room_type_id": 396096},
    }

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["status"] == "processed"
    assert result["reconciliation_action"] == "manual_review"
    assert [name for name, _ in dispatcher.calls] == ["booking_create_reservation", "booking_get_reservation"]
    assert any(
        "SET manual_review_reason = $2" in query and args[1] == "create_readback_mismatch"
        for query, args in conn.executed
    )


@pytest.mark.asyncio
async def test_process_approval_event_persists_applied_draft_before_payment_request(
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
            "cancel_policy_type": "FREE_CANCEL",
            "room_type_id": 396096,
        },
    }
    processor, conn, dispatcher = _build_processor(hold_row, monkeypatch=monkeypatch)
    dispatcher.create_result = {
        "reservation_id": "RSV-1",
        "voucher_no": "V-1",
        "applied_draft": {
            "phone": "",
            "checkin_date": "2026-09-10",
            "total_price_eur": 255,
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
            "room_type_id": 396096,
        },
    }
    dispatcher.readback_result = {
        "reservation_id": "RSV-1",
        "voucher_no": "V-1",
        "total_price": 255,
        "raw_data": {"room_type_id": 396096},
    }

    event = ApprovalEvent(
        hotel_id=21966,
        approval_request_id="APR-1",
        approved=True,
        approved_by_role="ADMIN",
        timestamp=datetime.now(UTC),
    )
    result = await processor.process_approval_event(event)

    assert result["status"] == "processed"
    payment_call = next(kwargs for name, kwargs in dispatcher.calls if name == "payment_request_prepayment")
    assert payment_call["amount"] == 255.0
    assert any("SET draft_json = $2::jsonb" in query for query, _args in conn.executed)
