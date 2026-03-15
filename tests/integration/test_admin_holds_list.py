"""Integration-like tests for admin hold listing workflow metadata."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import asyncpg
import orjson
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


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


class _FakeConnection:
    def __init__(self, *, legacy_fallback: bool) -> None:
        self._legacy_fallback = legacy_fallback
        self._workflow_query_called = False

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        _ = args
        if self._legacy_fallback and "json_build_object(" in query:
            raise asyncpg.CannotCoerceError("UNION could not convert type json to jsonb")
        if "FROM stay_holds" in query:
            if "workflow_state" in query and "NULL::text AS workflow_state" not in query:
                self._workflow_query_called = True
                if self._legacy_fallback:
                    raise asyncpg.UndefinedColumnError("workflow_state does not exist")
                return [
                    {
                        "hold_id": "S_HOLD_0001",
                        "type": "stay",
                        "hotel_id": 21966,
                        "status": "PAYMENT_PENDING",
                        "workflow_state": "PAYMENT_PENDING",
                        "draft_json": orjson.dumps({"guest_name": "Test User"}).decode(),
                        "expires_at": None,
                        "pms_create_started_at": None,
                        "pms_create_completed_at": None,
                        "manual_review_reason": None,
                        "approval_idempotency_key": "idem-1",
                        "create_idempotency_key": "idem-2",
                        "approved_by": "ADMIN",
                        "created_at": datetime.now(UTC),
                        "conversation_id": None,
                    }
                ]
            return [
                {
                    "hold_id": "S_HOLD_0001",
                    "type": "stay",
                    "hotel_id": 21966,
                    "status": "PENDING_APPROVAL",
                    "workflow_state": None,
                    "draft_json": orjson.dumps({"guest_name": "Test User"}).decode(),
                    "expires_at": None,
                    "pms_create_started_at": None,
                    "pms_create_completed_at": None,
                    "manual_review_reason": None,
                    "approval_idempotency_key": None,
                    "create_idempotency_key": None,
                    "approved_by": None,
                    "created_at": datetime.now(UTC),
                    "conversation_id": None,
                }
            ]
        return []

    async def fetchval(self, query: str, *args: Any) -> int:
        _ = (query, args)
        return 1


def _build_user() -> TokenData:
    return TokenData(
        user_id=1,
        hotel_id=21966,
        username="ops_admin",
        role=Role.ADMIN,
        display_name="Ops Admin",
    )


@pytest.mark.asyncio
async def test_list_holds_returns_workflow_fields_when_columns_exist() -> None:
    conn = _FakeConnection(legacy_fallback=False)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=_FakePool(conn))))

    result = await admin.list_holds(
        request=request,
        user=_build_user(),
        hotel_id=21966,
        hold_type="stay",
        status_filter=None,
        page=1,
        per_page=20,
    )

    assert result["total"] == 1
    item = result["items"][0]
    assert item["workflow_state"] == "PAYMENT_PENDING"
    assert item["draft_json"]["guest_name"] == "Test User"
    assert item["approval_idempotency_key"] == "idem-1"
    assert item["create_idempotency_key"] == "idem-2"


@pytest.mark.asyncio
async def test_list_holds_falls_back_when_workflow_columns_missing() -> None:
    conn = _FakeConnection(legacy_fallback=True)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=_FakePool(conn))))

    result = await admin.list_holds(
        request=request,
        user=_build_user(),
        hotel_id=21966,
        hold_type="stay",
        status_filter=None,
        page=1,
        per_page=20,
    )

    assert result["total"] == 1
    item = result["items"][0]
    assert item["status"] == "PENDING_APPROVAL"
    assert item["draft_json"]["guest_name"] == "Test User"
    assert conn._workflow_query_called is True


@pytest.mark.asyncio
async def test_list_holds_legacy_fallback_uses_jsonb_union_compatible_query() -> None:
    conn = _FakeConnection(legacy_fallback=True)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=_FakePool(conn))))

    result = await admin.list_holds(
        request=request,
        user=_build_user(),
        hotel_id=21966,
        hold_type=None,
        status_filter=None,
        page=1,
        per_page=20,
    )

    assert result["total"] == 1
