"""Payment request tool."""

from datetime import date
from typing import Any

from velox.db.repositories.hotel import NotificationRepository, PaymentRequestRepository
from velox.tools.base import BaseTool
from velox.tools.notification import NotifySendTool


class PaymentRequestPrepaymentTool(BaseTool):
    """Create prepayment request and notify SALES for manual handling."""

    def __init__(
        self,
        payment_repository: PaymentRequestRepository,
        notification_repository: NotificationRepository,
    ) -> None:
        self._payment_repository = payment_repository
        self._notify_tool = NotifySendTool(notification_repository)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "reference_id", "amount", "currency", "methods"])
        hotel_id = int(kwargs["hotel_id"])
        reference_id = str(kwargs["reference_id"])
        amount = float(kwargs["amount"])
        currency = str(kwargs["currency"])
        methods = [str(method) for method in kwargs["methods"]]
        due_mode_raw = kwargs.get("due_mode")
        if due_mode_raw:
            due_mode = str(due_mode_raw).upper()
        else:
            cancel_policy_type = str(kwargs.get("cancel_policy_type", "")).upper()
            due_mode = "NOW" if cancel_policy_type == "NON_REFUNDABLE" else "SCHEDULED"
        scheduled_date_raw = kwargs.get("scheduled_date")
        scheduled_date = date.fromisoformat(str(scheduled_date_raw)) if scheduled_date_raw else None

        if due_mode not in {"NOW", "SCHEDULED"}:
            raise ValueError("due_mode must be NOW or SCHEDULED")
        if due_mode == "SCHEDULED" and scheduled_date is None:
            raise ValueError("scheduled_date is required for SCHEDULED mode")

        result = await self._payment_repository.create(
            hotel_id=hotel_id,
            reference_id=reference_id,
            amount=amount,
            currency=currency,
            methods=methods,
            due_mode=due_mode,
            scheduled_date=scheduled_date,
        )
        await self._notify_tool.execute(
            hotel_id=hotel_id,
            to_role="SALES",
            channel="panel",
            message=f"Manual payment process required for {reference_id}.",
            metadata={
                "intent": "payment_request",
                "reference_id": reference_id,
                "amount": amount,
                "currency": currency,
                "due_mode": due_mode,
                "handled_by": "SALES",
            },
        )
        return result
