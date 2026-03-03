"""Handoff ticket creation tool with dedupe."""

from typing import Any
from uuid import UUID

from velox.db.repositories.hotel import NotificationRepository, TicketRepository
from velox.tools.base import BaseTool
from velox.tools.notification import NotifySendTool


class HandoffCreateTicketTool(BaseTool):
    """Create or dedupe handoff tickets and notify assigned role."""

    def __init__(
        self,
        ticket_repository: TicketRepository,
        notification_repository: NotificationRepository,
    ) -> None:
        self._ticket_repository = ticket_repository
        self._notify_tool = NotifySendTool(notification_repository)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "reason", "transcript_summary"])
        hotel_id = int(kwargs["hotel_id"])
        reason = str(kwargs["reason"])
        transcript_summary = str(kwargs["transcript_summary"])
        priority = str(kwargs.get("priority", "medium"))
        dedupe_key = str(kwargs["dedupe_key"]) if kwargs.get("dedupe_key") else None
        assigned_to_role = str(kwargs["assigned_to_role"]) if kwargs.get("assigned_to_role") else "OPS"
        conversation_id_raw = kwargs.get("conversation_id")
        conversation_id = UUID(str(conversation_id_raw)) if conversation_id_raw else None

        result = await self._ticket_repository.create(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            reason=reason,
            transcript_summary=transcript_summary,
            priority=priority,
            assigned_to_role=assigned_to_role,
            dedupe_key=dedupe_key,
        )

        await self._notify_tool.execute(
            hotel_id=hotel_id,
            to_role=assigned_to_role,
            channel="panel",
            message=f"Handoff ticket opened: {result['ticket_id']}",
            metadata={
                "format_standard": "A11.8",
                "level": kwargs.get("level", "L2"),
                "intent": kwargs.get("intent", "human_handoff"),
                "hotel_name": kwargs.get("hotel_name", "Unknown"),
                "guest_name": kwargs.get("guest_name", "Unknown"),
                "phone": kwargs.get("phone", "***"),
                "transcript_summary": transcript_summary,
                "requested_action": kwargs.get("requested_action", reason),
                "reference_id": result["ticket_id"],
                "risk_flags": kwargs.get("risk_flags", []),
                "priority": priority,
            },
        )
        return result
