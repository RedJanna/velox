"""CRM logging tool."""

from typing import Any
from uuid import UUID

from velox.db.repositories.hotel import CrmLogRepository
from velox.tools.base import BaseTool
from velox.utils.privacy import hash_phone


class CRMLogTool(BaseTool):
    """Persist CRM log row with privacy-safe phone hash."""

    def __init__(self, crm_repository: CrmLogRepository) -> None:
        self._crm_repository = crm_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "intent", "entities", "actions", "outcome", "transcript_summary"])
        phone_hash = str(kwargs.get("user_phone_hash", "")).strip()
        raw_phone = str(kwargs.get("phone", "")).strip()
        if not phone_hash and raw_phone:
            phone_hash = hash_phone(raw_phone)
        if not phone_hash:
            phone_hash = hash_phone("unknown")

        conversation_id_raw = kwargs.get("conversation_id")
        conversation_id = UUID(str(conversation_id_raw)) if conversation_id_raw else None

        return await self._crm_repository.log(
            hotel_id=int(kwargs["hotel_id"]),
            conversation_id=conversation_id,
            user_phone_hash=phone_hash,
            intent=str(kwargs["intent"]),
            entities=dict(kwargs["entities"]),
            actions=[str(item) for item in kwargs["actions"]],
            outcome=str(kwargs["outcome"]),
            transcript_summary=str(kwargs["transcript_summary"]),
        )
