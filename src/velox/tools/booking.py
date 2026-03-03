"""Booking-related tools (availability, quote, hold, reservation operations)."""

from decimal import Decimal
from typing import Any

from velox.adapters.elektraweb import (
    availability,
    cancel_reservation,
    create_reservation,
    get_reservation,
    modify_reservation,
    quote,
)
from velox.models.reservation import BookingAvailabilityRequest, BookingQuoteRequest, StayDraft, StayHold
from velox.db.repositories.reservation import ReservationRepository
from velox.tools.base import BaseTool

class BookingAvailabilityTool(BaseTool):
    """Tool for stay availability lookup via Elektraweb adapter."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "checkin_date", "checkout_date", "adults"])
        request = BookingAvailabilityRequest.model_validate(kwargs)
        response = await availability(
            hotel_id=request.hotel_id,
            checkin=request.checkin_date,
            checkout=request.checkout_date,
            adults=request.adults,
            chd_count=request.chd_count,
            chd_ages=request.chd_ages,
            currency=request.currency,
        )
        return response.model_dump(mode="json")


class BookingQuoteTool(BaseTool):
    """Tool for stay quote lookup via Elektraweb adapter."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "checkin_date", "checkout_date", "adults"])
        request = BookingQuoteRequest.model_validate(kwargs)
        response = await quote(
            hotel_id=request.hotel_id,
            checkin=request.checkin_date,
            checkout=request.checkout_date,
            adults=request.adults,
            chd_count=request.chd_count,
            chd_ages=request.chd_ages,
            currency=request.currency,
            language=request.language,
            nationality=request.nationality,
            only_best_offer=request.only_best_offer,
            cancel_policy_type=request.cancel_policy_type.value if request.cancel_policy_type else None,
        )
        return response.model_dump(mode="json")


class StayCreateHoldTool(BaseTool):
    """Tool for creating a stay hold in DB."""

    def __init__(self, reservation_repository: ReservationRepository) -> None:
        self._reservation_repository = reservation_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "draft"])

        draft = StayDraft.model_validate(kwargs["draft"])
        hold = StayHold(
            hold_id="",
            hotel_id=int(kwargs["hotel_id"]),
            conversation_id=kwargs.get("conversation_id"),
            draft_json=draft.model_dump(mode="json"),
        )
        created = await self._reservation_repository.create_hold(hold)
        return {
            "stay_hold_id": created.hold_id,
            "status": created.status.value,
            "summary": (
                f"{draft.checkin_date} - {draft.checkout_date}, "
                f"{draft.adults} adults, {Decimal(draft.total_price_eur)} EUR"
            ),
        }


class BookingCreateReservationTool(BaseTool):
    """Tool for creating stay reservation in PMS."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "draft"])
        hotel_id = int(kwargs["hotel_id"])
        response = await create_reservation(hotel_id=hotel_id, draft=dict(kwargs["draft"]))
        return response.model_dump(mode="json")


class BookingGetReservationTool(BaseTool):
    """Tool for fetching reservation from PMS."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id"])
        hotel_id = int(kwargs["hotel_id"])
        reservation_id = kwargs.get("reservation_id")
        voucher_no = kwargs.get("voucher_no")
        response = await get_reservation(
            hotel_id=hotel_id,
            reservation_id=str(reservation_id) if reservation_id else None,
            voucher_no=str(voucher_no) if voucher_no else None,
        )
        return response.model_dump(mode="json")


class BookingModifyTool(BaseTool):
    """Tool for updating a reservation in PMS."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "updates"])
        reservation_id = kwargs.get("reservation_id")
        if not reservation_id:
            raise ValueError("reservation_id is required")

        response = await modify_reservation(
            hotel_id=int(kwargs["hotel_id"]),
            reservation_id=str(reservation_id),
            updates=dict(kwargs["updates"]),
        )
        return {"success": True, "result": response}


class BookingCancelTool(BaseTool):
    """Tool for cancelling a reservation in PMS."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id"])
        reservation_id = kwargs.get("reservation_id")
        if not reservation_id:
            raise ValueError("reservation_id is required")

        response = await cancel_reservation(
            hotel_id=int(kwargs["hotel_id"]),
            reservation_id=str(reservation_id),
            reason=str(kwargs.get("reason", "Cancelled by request")),
        )
        return {"success": True, "result": response}
