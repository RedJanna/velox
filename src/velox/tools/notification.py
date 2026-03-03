"""Notification tool implementation."""

from typing import Any

from velox.db.repositories.hotel import NotificationRepository
from velox.tools.base import BaseTool


def _mask_phone(phone: str) -> str:
    """Mask phone for internal notifications."""
    value = phone.strip()
    if len(value) < 4:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def format_notification_message(
    *,
    level: str,
    role: str,
    intent: str,
    hotel_name: str,
    hotel_id: int,
    guest_name: str,
    phone: str,
    transcript_summary: str,
    requested_action: str,
    reference_id: str,
    risk_flags: list[str],
    priority: str,
) -> str:
    """Format notification according to A11.8 internal template."""
    return (
        f"[VELOX-{level}] {role} | {intent}\n"
        f"Hotel: {hotel_name} (#{hotel_id})\n"
        f"Misafir: {guest_name} | {_mask_phone(phone)}\n"
        f"Ozet: {transcript_summary}\n"
        f"Aksiyon: {requested_action}\n"
        f"Ref: {reference_id}\n"
        f"Risk: {risk_flags}\n"
        f"Oncelik: {priority}"
    )


class NotifySendTool(BaseTool):
    """Create notifications across panel and optional channels."""

    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "to_role", "channel", "message"])
        hotel_id = int(kwargs["hotel_id"])
        to_role = str(kwargs["to_role"])
        channel = str(kwargs["channel"]).lower()
        metadata = dict(kwargs.get("metadata") or {})
        message = str(kwargs["message"])

        if metadata.get("format_standard") == "A11.8":
            message = format_notification_message(
                level=str(metadata.get("level", "L1")),
                role=to_role,
                intent=str(metadata.get("intent", "other")),
                hotel_name=str(metadata.get("hotel_name", "Unknown")),
                hotel_id=hotel_id,
                guest_name=str(metadata.get("guest_name", "Unknown")),
                phone=str(metadata.get("phone", "***")),
                transcript_summary=str(metadata.get("transcript_summary", "")),
                requested_action=str(metadata.get("requested_action", "")),
                reference_id=str(metadata.get("reference_id", "")),
                risk_flags=list(metadata.get("risk_flags", [])),
                priority=str(metadata.get("priority", "medium")),
            )

        panel_entry = await self._notification_repository.create(
            hotel_id=hotel_id,
            to_role=to_role,
            channel="panel",
            message=message,
            metadata_json=metadata,
        )
        created_entries = [panel_entry]

        if channel in {"whatsapp", "email"}:
            created_entries.append(
                await self._notification_repository.create(
                    hotel_id=hotel_id,
                    to_role=to_role,
                    channel=channel,
                    message=message,
                    metadata_json=metadata,
                )
            )

        return {
            "notification_id": panel_entry["notification_id"],
            "status": panel_entry["status"],
            "channels_created": [entry["notification_id"] for entry in created_entries],
        }
