"""Unit tests for approval WhatsApp alert fallback behavior."""

from __future__ import annotations

import httpx
import pytest

from velox.tools.approval import ApprovalRequestTool


class _DummyApprovalRepo:
    async def create(self, **_kwargs: object) -> dict[str, object]:
        return {"approval_request_id": "APR_1", "status": "REQUESTED"}


class _DummyNotificationRepo:
    async def create(self, **_kwargs: object) -> dict[str, str]:
        return {"notification_id": "N_1", "status": "PENDING"}


class _DummyPhoneRepo:
    async def get_active_phones(self, _hotel_id: int) -> list[str]:
        return ["+905551112233"]


class _FakeWhatsAppClient:
    def __init__(self) -> None:
        self.template_calls = 0
        self.text_calls = 0
        self._first_text_call = True

    async def send_text_message(self, **_kwargs: object) -> dict[str, object]:
        self.text_calls += 1
        if self._first_text_call:
            self._first_text_call = False
            request = httpx.Request("POST", "https://graph.facebook.com/v21.0/messages")
            response = httpx.Response(
                400,
                request=request,
                json={"error": {"code": 131047, "message": "Session closed"}},
            )
            raise httpx.HTTPStatusError("session_closed", request=request, response=response)
        return {"messages": [{"id": "wamid.ok"}]}

    async def send_template_message(self, **_kwargs: object) -> dict[str, object]:
        self.template_calls += 1
        return {"messages": [{"id": "wamid.template"}]}


@pytest.mark.asyncio
async def test_approval_alert_reopens_chat_window_on_session_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Approval alerts should fallback to template and retry text on closed session errors."""
    fake_client = _FakeWhatsAppClient()
    monkeypatch.setattr("velox.tools.approval.get_whatsapp_client", lambda: fake_client)

    async def _noop_sync(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(ApprovalRequestTool, "_sync_reference_status", staticmethod(_noop_sync))

    tool = ApprovalRequestTool(
        approval_repository=_DummyApprovalRepo(),
        notification_repository=_DummyNotificationRepo(),
        notification_phone_repository=_DummyPhoneRepo(),
    )

    result = await tool.execute(
        hotel_id=21966,
        approval_type="STAY",
        reference_id="S_HOLD_999",
        details_summary="Konaklama talebi",
    )

    assert result["approval_request_id"] == "APR_1"
    assert fake_client.template_calls == 1
    assert fake_client.text_calls == 2
