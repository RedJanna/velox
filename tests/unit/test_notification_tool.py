"""Unit tests for notification helpers."""

from __future__ import annotations

from velox.tools import notification


def test_notify_tool_formats_a118_message_for_delivery() -> None:
    message = notification.NotifySendTool._format_message_for_delivery(
        hotel_id=21966,
        to_role="ADMIN",
        message="ignored",
        metadata={
            "format_standard": "A11.8",
            "level": "L2",
            "intent": "human_handoff",
            "hotel_name": "Kassandra",
            "guest_name": "Test Guest",
            "phone": "+905551112233",
            "transcript_summary": "Need help",
            "requested_action": "call guest",
            "reference_id": "T_1",
            "risk_flags": ["ANGRY_COMPLAINT"],
            "priority": "high",
        },
    )
    assert "[VELOX-L2] ADMIN | human_handoff" in message
    assert "Hotel: Kassandra (#21966)" in message
    assert "Misafir: Test Guest | +90***33" in message


async def test_send_admin_whatsapp_alerts_sends_unique_phones(monkeypatch) -> None:
    sent: list[tuple[str, str]] = []

    class _FakeWhatsApp:
        async def send_text_message(self, *, to: str, body: str, force: bool = False):  # type: ignore[no-untyped-def]
            sent.append((to, body))
            return {"messages": [{"id": "wamid.1"}]}

        async def send_template_message(self, **kwargs):  # type: ignore[no-untyped-def]
            return kwargs

    class _FakePhoneRepo:
        async def get_active_phones(self, hotel_id: int) -> list[str]:
            assert hotel_id == 21966
            return ["+905001112233", "+905001112233", "+905009998877"]

    monkeypatch.setattr(notification, "get_whatsapp_client", lambda: _FakeWhatsApp())

    delivered = await notification.send_admin_whatsapp_alerts(
        hotel_id=21966,
        message="Test alert",
        phone_repo=_FakePhoneRepo(),
    )

    assert delivered == ["+905001112233", "+905009998877"]
    assert sent == [
        ("+905001112233", "Test alert"),
        ("+905009998877", "Test alert"),
    ]
