"""Integration-like tests for admin message send persistence."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

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


class _FakeConnection:
    def __init__(self) -> None:
        self.updated_internal_json: dict[str, Any] | None = None

    async def fetchrow(self, query: str, *args: object) -> dict[str, Any] | None:
        if "SELECT id, hotel_id, phone_display FROM conversations" in query:
            return {
                "id": args[0],
                "hotel_id": 21966,
                "phone_display": "905551112233",
            }
        if "SELECT id, role, content, internal_json FROM messages" in query:
            return {
                "id": args[0],
                "role": "assistant",
                "content": "Mesaj hazir.",
                "internal_json": {"send_blocked": True, "approval_pending": True},
            }
        if "SELECT internal_json FROM messages" in query:
            return {
                "internal_json": {"wa_id": "905551112233"},
            }
        raise AssertionError(f"Unsupported fetchrow query: {query}")

    async def execute(self, query: str, *args: object) -> str:
        if "UPDATE messages" in query and "whatsapp_message_id" in query:
            self.updated_internal_json = orjson.loads(str(args[0]))
            return "UPDATE 1"
        raise AssertionError(f"Unsupported execute query: {query}")


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


@pytest.mark.asyncio
async def test_admin_send_persists_whatsapp_message_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Approved admin sends should persist the provider WhatsApp message id for reply resolution."""
    conversation_id = uuid4()
    message_id = uuid4()
    connection = _FakeConnection()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=_FakePool(connection))))
    user = TokenData(
        user_id=1,
        hotel_id=21966,
        username="ops_admin",
        role=Role.ADMIN,
        display_name="Ops Admin",
    )

    class _FakeWhatsAppClient:
        async def send_text_message(self, **_kwargs: Any) -> dict[str, Any]:
            return {"messages": [{"id": "wamid.admin.1"}]}

    monkeypatch.setattr(admin, "get_whatsapp_client", lambda: _FakeWhatsAppClient())

    result = await admin.approve_and_send_message(
        conversation_id=conversation_id,
        message_id=message_id,
        request=request,
        user=user,
    )

    assert result["status"] == "sent"
    assert connection.updated_internal_json is not None
    assert connection.updated_internal_json["send_blocked"] is False
    assert connection.updated_internal_json["approval_pending"] is False
    assert connection.updated_internal_json["approved_by"] == "ops_admin"
    assert connection.updated_internal_json["whatsapp_message_id"] == "wamid.admin.1"
