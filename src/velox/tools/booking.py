"""Booking-related tools (availability, quote, hold, reservation operations)."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import structlog

from velox.adapters.elektraweb import (
    availability,
    cancel_reservation,
    create_reservation,
    get_reservation,
    modify_reservation,
    quote,
)
from velox.core.hotel_profile_loader import get_profile
from velox.db.repositories.reservation import ReservationRepository
from velox.models.reservation import (
    BookingAvailabilityRequest,
    BookingQuoteRequest,
    ExternalReservationSnapshot,
    StayDraft,
    StayHold,
)
from velox.tools.approval import ApprovalRequestTool
from velox.tools.base import BaseTool
from velox.tools.season import are_dates_within_hotel_season, out_of_season_response
from velox.utils.customer_notes import format_customer_visible_note

logger = structlog.get_logger(__name__)


def _hotel_today(profile: Any | None) -> date:
    """Return current date in the hotel's configured timezone."""
    timezone_name = str(getattr(profile, "timezone", "") or "Europe/Istanbul").strip()
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logger.warning("hotel_timezone_invalid_for_booking_date_guard", timezone=timezone_name)
        timezone = UTC
    return datetime.now(timezone).date()


def _invalid_stay_date_response(
    *,
    checkin_date: date,
    checkout_date: date,
    current_date: date,
    reason: str,
    required_question: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "available": False,
        "reason": reason,
        "suggestion": "request_valid_date",
        "checkin_date": checkin_date.isoformat(),
        "checkout_date": checkout_date.isoformat(),
        "current_date": current_date.isoformat(),
        "required_questions": [required_question],
        "next_step": next_step,
    }


def _stay_date_guard_response(
    *,
    hotel_id: int,
    checkin_date: date,
    checkout_date: date,
    profile: Any | None,
) -> dict[str, Any] | None:
    """Reject invalid stay date ranges before any PMS call."""
    current_date = _hotel_today(profile)
    if checkout_date <= checkin_date:
        logger.info(
            "stay_date_guard_rejected",
            hotel_id=hotel_id,
            reason="CHECKOUT_DATE_NOT_AFTER_CHECKIN",
            checkin_date=checkin_date.isoformat(),
            checkout_date=checkout_date.isoformat(),
        )
        return _invalid_stay_date_response(
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            current_date=current_date,
            reason="CHECKOUT_DATE_NOT_AFTER_CHECKIN",
            required_question="checkout_date",
            next_step="collect_valid_checkout_date",
        )
    if checkin_date < current_date:
        logger.info(
            "stay_date_guard_rejected",
            hotel_id=hotel_id,
            reason="CHECKIN_DATE_IN_PAST",
            checkin_date=checkin_date.isoformat(),
            current_date=current_date.isoformat(),
        )
        return _invalid_stay_date_response(
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            current_date=current_date,
            reason="CHECKIN_DATE_IN_PAST",
            required_question="checkin_date",
            next_step="collect_future_checkin_date",
        )
    return None


def _availability_unverified(payload: dict[str, Any]) -> bool:
    """Return True when PMS availability cannot safely prove sold-out status."""
    derived = payload.get("derived")
    if not isinstance(derived, dict):
        return False
    return str(derived.get("availability_status") or "").strip() == "unverified"


class BookingAvailabilityTool(BaseTool):
    """Tool for stay availability lookup via Elektraweb adapter."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "checkin_date", "checkout_date", "adults"])
        request = BookingAvailabilityRequest.model_validate(kwargs)
        profile = get_profile(request.hotel_id)
        date_guard = _stay_date_guard_response(
            hotel_id=request.hotel_id,
            checkin_date=request.checkin_date,
            checkout_date=request.checkout_date,
            profile=profile,
        )
        if date_guard is not None:
            return date_guard
        if profile is not None and not are_dates_within_hotel_season(
            profile,
            (request.checkin_date, request.checkout_date),
            invalid_event="booking_season_config_invalid",
        ):
            return out_of_season_response(profile)
        response = await availability(
            hotel_id=request.hotel_id,
            checkin=request.checkin_date,
            checkout=request.checkout_date,
            adults=request.adults,
            chd_count=request.chd_count,
            chd_ages=request.chd_ages,
            currency=request.currency,
        )
        payload = response.model_dump(mode="json")
        if _availability_unverified(payload):
            payload.update(
                {
                    "error": "LIVE_AVAILABILITY_UNVERIFIED",
                    "handoff_required": True,
                    "reason": "AVAILABILITY_EMPTY_PRICE_FALLBACK_FAILED",
                    "next_step": "handoff_to_live_availability_team",
                }
            )
        return payload


class BookingQuoteTool(BaseTool):
    """Tool for stay quote lookup via Elektraweb adapter."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "checkin_date", "checkout_date", "adults"])
        request = BookingQuoteRequest.model_validate(kwargs)
        profile = get_profile(request.hotel_id)
        date_guard = _stay_date_guard_response(
            hotel_id=request.hotel_id,
            checkin_date=request.checkin_date,
            checkout_date=request.checkout_date,
            profile=profile,
        )
        if date_guard is not None:
            return date_guard
        if profile is not None and not are_dates_within_hotel_season(
            profile,
            (request.checkin_date, request.checkout_date),
            invalid_event="booking_season_config_invalid",
        ):
            return out_of_season_response(profile)
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

    def __init__(
        self,
        reservation_repository: ReservationRepository,
        approval_tool: ApprovalRequestTool | None = None,
    ) -> None:
        self._reservation_repository = reservation_repository
        self._approval_tool = approval_tool

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "draft"])

        draft = StayDraft.model_validate(kwargs["draft"])
        draft.notes = format_customer_visible_note(draft.notes)
        hotel_id = int(kwargs["hotel_id"])

        # Validate and resolve room_type_id against hotel profile
        room_name = ""
        profile = get_profile(hotel_id)
        date_guard = _stay_date_guard_response(
            hotel_id=hotel_id,
            checkin_date=draft.checkin_date,
            checkout_date=draft.checkout_date,
            profile=profile,
        )
        if date_guard is not None:
            return date_guard
        if profile is not None and not are_dates_within_hotel_season(
            profile,
            (draft.checkin_date, draft.checkout_date),
            invalid_event="booking_season_config_invalid",
        ):
            return out_of_season_response(profile)
        if profile and profile.room_types:
            valid_pms_ids = {rt.pms_room_type_id for rt in profile.room_types}
            internal_id_map = {rt.id: rt for rt in profile.room_types}

            if draft.room_type_id not in valid_pms_ids:
                if draft.room_type_id in internal_id_map:
                    resolved_rt = internal_id_map[draft.room_type_id]
                    logger.warning(
                        "stay_hold_internal_id_resolved_to_pms",
                        internal_id=draft.room_type_id,
                        pms_room_type_id=resolved_rt.pms_room_type_id,
                        room_name=resolved_rt.name.tr,
                    )
                    draft.room_type_id = resolved_rt.pms_room_type_id
                else:
                    raise ValueError(
                        f"Invalid room_type_id: {draft.room_type_id}. "
                        f"Valid PMS IDs: {sorted(valid_pms_ids)}"
                    )

            for rt in profile.room_types:
                if rt.pms_room_type_id == draft.room_type_id:
                    room_name = rt.name.tr
                    break

        hold = StayHold(
            hold_id="",
            hotel_id=hotel_id,
            conversation_id=kwargs.get("conversation_id"),
            draft_json=draft.model_dump(mode="json"),
        )
        created = await self._reservation_repository.create_hold(hold)

        chd_info = ""
        if draft.chd_ages:
            chd_info = f", {len(draft.chd_ages)} cocuk (yas: {', '.join(str(a) for a in draft.chd_ages)})"

        cancel_label = "Ucretsiz iptal" if draft.cancel_policy_type.value == "FREE_CANCEL" else "Iptal edilemez"
        notes_line = f"\nNot: {draft.notes}" if draft.notes else ""
        room_line = f"Oda: {room_name} (ID: {draft.room_type_id})\n" if room_name else ""

        details_summary = (
            f"Konaklama talebi\n"
            f"{room_line}"
            f"Tarih: {draft.checkin_date} - {draft.checkout_date}\n"
            f"Kisi: {draft.adults} yetiskin{chd_info}\n"
            f"Misafir: {draft.guest_name}\n"
            f"Telefon: {draft.phone}\n"
            f"Toplam: {Decimal(draft.total_price_eur)} EUR\n"
            f"Iptal: {cancel_label}"
            f"{notes_line}"
        )

        approval_result: dict[str, Any] = {"approval_request_id": None, "status": "REQUESTED"}
        if self._approval_tool is not None:
            approval_result = await self._approval_tool.execute(
                hotel_id=int(kwargs["hotel_id"]),
                approval_type="STAY",
                reference_id=created.hold_id,
                details_summary=details_summary,
                required_roles=["ADMIN"],
                any_of=False,
            )
        return {
            "stay_hold_id": created.hold_id,
            "status": created.status.value,
            "approval_request_id": approval_result.get("approval_request_id"),
            "approval_status": approval_result.get("status"),
            "summary": (
                f"{draft.checkin_date} - {draft.checkout_date}, "
                f"{draft.adults} yetiskin{chd_info}, {Decimal(draft.total_price_eur)} EUR, "
                f"{cancel_label}"
            ),
        }


class BookingCreateReservationTool(BaseTool):
    """Tool for creating stay reservation in PMS."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "draft"])
        approval_context = str(kwargs.get("approval_context", "")).upper()
        admin_approved = bool(kwargs.get("admin_approved"))
        if approval_context != "ADMIN_APPROVED" and not admin_approved:
            raise ValueError(
                "booking_create_reservation is admin-only. Use stay_create_hold + approval_request from guest flow."
            )

        hotel_id = int(kwargs["hotel_id"])
        response = await create_reservation(hotel_id=hotel_id, draft=dict(kwargs["draft"]))
        return response.model_dump(mode="json")


class BookingGetReservationTool(BaseTool):
    """Tool for fetching reservation from PMS."""

    def __init__(self, reservation_repository: ReservationRepository | None = None) -> None:
        self._reservation_repository = reservation_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id"])
        hotel_id = int(kwargs["hotel_id"])
        reservation_id = kwargs.get("reservation_id")
        voucher_no = kwargs.get("voucher_no")
        contact_phone = kwargs.get("contact_phone")
        checkin_date = kwargs.get("checkin_date")
        checkout_date = kwargs.get("checkout_date")
        response = await get_reservation(
            hotel_id=hotel_id,
            reservation_id=str(reservation_id) if reservation_id else None,
            voucher_no=str(voucher_no) if voucher_no else None,
            contact_phone=str(contact_phone) if contact_phone else None,
            checkin_date=str(checkin_date) if checkin_date else None,
            checkout_date=str(checkout_date) if checkout_date else None,
        )
        if response.success and self._reservation_repository is not None:
            detail = response.model_dump(mode="json")
            if detail.get("reservation_id") or detail.get("voucher_no"):
                snapshot = ExternalReservationSnapshot.from_lookup(
                    hotel_id=hotel_id,
                    lookup_phone=str(contact_phone) if contact_phone else None,
                    detail=detail,
                )
                await self._reservation_repository.upsert_external_snapshot(snapshot)
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
