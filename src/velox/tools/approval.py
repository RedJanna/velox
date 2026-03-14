"""Approval request tool."""

import asyncio
from typing import Any

import structlog

from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.db.database import execute
from velox.db.repositories.hotel import (
    ApprovalRequestRepository,
    NotificationPhoneRepository,
    NotificationRepository,
)
from velox.tools.base import BaseTool
from velox.tools.notification import NotifySendTool

logger = structlog.get_logger(__name__)

DEFAULT_APPROVAL_RULES: dict[str, tuple[list[str], bool]] = {
    "STAY": (["ADMIN"], False),
    "RESTAURANT": (["ADMIN", "CHEF"], True),
    "TRANSFER": (["ADMIN"], False),
}

_WHATSAPP_SEND_TIMEOUT = 10.0


class ApprovalRequestTool(BaseTool):
    """Create approval request and notify required roles."""

    def __init__(
        self,
        approval_repository: ApprovalRequestRepository,
        notification_repository: NotificationRepository,
        notification_phone_repository: NotificationPhoneRepository | None = None,
    ) -> None:
        self._approval_repository = approval_repository
        self._notify_tool = NotifySendTool(notification_repository)
        self._phone_repo = notification_phone_repository or NotificationPhoneRepository()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "approval_type", "reference_id", "details_summary"])
        hotel_id = int(kwargs["hotel_id"])
        approval_type = str(kwargs["approval_type"]).upper()
        reference_id = str(kwargs["reference_id"])
        details_summary = str(kwargs["details_summary"])

        default_roles, default_any_of = DEFAULT_APPROVAL_RULES.get(approval_type, (["ADMIN"], False))
        required_roles = list(kwargs.get("required_roles") or default_roles)
        any_of = bool(kwargs.get("any_of", default_any_of))

        result = await self._approval_repository.create(
            hotel_id=hotel_id,
            approval_type=approval_type,
            reference_id=reference_id,
            details_summary=details_summary,
            required_roles=required_roles,
            any_of=any_of,
        )
        await self._sync_reference_status(hotel_id=hotel_id, reference_id=reference_id)

        for role in required_roles:
            await self._notify_tool.execute(
                hotel_id=hotel_id,
                to_role=role,
                channel="panel",
                message=f"Approval requested for {approval_type}: {reference_id}",
                metadata={
                    "intent": "approval_request",
                    "reference_id": reference_id,
                    "approval_type": approval_type,
                    "any_of": any_of,
                },
            )

        await self._send_admin_whatsapp_alerts(
            hotel_id=hotel_id,
            approval_type=approval_type,
            reference_id=reference_id,
            details_summary=details_summary,
        )

        return result

    async def _send_admin_whatsapp_alerts(
        self,
        *,
        hotel_id: int,
        approval_type: str,
        reference_id: str,
        details_summary: str,
    ) -> None:
        """Send WhatsApp notification to all active admin phones."""
        try:
            phones = await self._phone_repo.get_active_phones(hotel_id)
        except Exception:
            logger.warning("approval_whatsapp_phone_list_failed", hotel_id=hotel_id)
            phones = [NotificationPhoneRepository.DEFAULT_PHONE]

        message = (
            f"Yeni onay talebi ({approval_type})\n"
            f"Ref: {reference_id}\n"
            f"{details_summary}\n\n"
            f"Admin panelden onaylayabilir veya reddedebilirsiniz."
        )

        whatsapp = get_whatsapp_client()
        for phone in phones:
            try:
                await asyncio.wait_for(
                    whatsapp.send_text_message(to=phone, body=message),
                    timeout=_WHATSAPP_SEND_TIMEOUT,
                )
                logger.info("approval_whatsapp_sent", phone=phone[:5] + "***")
            except Exception:
                logger.warning("approval_whatsapp_failed", phone=phone[:5] + "***")

    @staticmethod
    async def _sync_reference_status(hotel_id: int, reference_id: str) -> None:
        """Set referenced hold status to PENDING_APPROVAL if exists."""
        if reference_id.startswith("S_HOLD_"):
            await execute(
                """
                UPDATE stay_holds
                SET status = 'PENDING_APPROVAL', updated_at = now()
                WHERE hotel_id = $1 AND hold_id = $2
                """,
                hotel_id,
                reference_id,
            )
        elif reference_id.startswith("R_HOLD_"):
            await execute(
                """
                UPDATE restaurant_holds
                SET status = 'PENDING_APPROVAL', updated_at = now()
                WHERE hotel_id = $1 AND hold_id = $2
                """,
                hotel_id,
                reference_id,
            )
        elif reference_id.startswith("TR_HOLD_"):
            await execute(
                """
                UPDATE transfer_holds
                SET status = 'PENDING_APPROVAL', updated_at = now()
                WHERE hotel_id = $1 AND hold_id = $2
                """,
                hotel_id,
                reference_id,
            )
