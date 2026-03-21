"""Restaurant availability and hold management tools."""

from __future__ import annotations

import datetime as _dt
import re
from datetime import time
from typing import Any

import structlog
from pydantic import BaseModel

from velox.config.constants import (
    HoldStatus,
    RestaurantReservationStatus,
    RiskFlag,
    resolve_table_type,
)
from velox.core.hotel_profile_loader import get_profile
from velox.db.database import execute, fetchrow
from velox.db.repositories.hotel import ApprovalRequestRepository, NotificationRepository
from velox.db.repositories.restaurant import RestaurantRepository
from velox.db.repositories.restaurant_floor_plan import RestaurantSettingsRepository
from velox.models.restaurant import RestaurantAvailabilityRequest, RestaurantHold
from velox.tools.approval import ApprovalRequestTool
from velox.tools.base import BaseTool
from velox.tools.notification import NotifySendTool

logger = structlog.get_logger(__name__)

ALLERGY_PATTERN = re.compile(
    r"(allerg|alergy|allergy|gluten|lactose|laktoz|peanut|nut|fistik|alerji|vegan|vegetarian)",
    flags=re.IGNORECASE,
)


class _RestaurantHoldUpdates(BaseModel):
    date: _dt.date | None = None
    time: _dt.time | None = None
    party_size: int | None = None
    guest_name: str | None = None
    phone: str | None = None
    area: str | None = None
    notes: str | None = None
    slot_id: str | None = None


class RestaurantAvailabilityTool(BaseTool):
    """Check restaurant slots from DB capacity table."""

    def __init__(self, restaurant_repository: RestaurantRepository) -> None:
        self._restaurant_repository = restaurant_repository
        self._settings_repository = RestaurantSettingsRepository()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Run availability query with profile-based business checks."""
        self.validate_required(kwargs, ["hotel_id", "date", "time", "party_size"])
        request = RestaurantAvailabilityRequest.model_validate(kwargs)
        profile = get_profile(request.hotel_id)

        settings = await self._settings_repository.get(request.hotel_id)
        if request.party_size < settings.min_party_size or request.party_size > settings.max_party_size:
            return {
                "available": False,
                "reason": "PARTY_SIZE_OUT_OF_RANGE",
                "suggestion": "request_valid_party_size",
                "accepted_party_size_range": {
                    "min": settings.min_party_size,
                    "max": settings.max_party_size,
                },
            }

        if not _is_within_restaurant_hours(profile, request.time):
            return {
                "available": False,
                "reason": "OUTSIDE_RESTAURANT_HOURS",
                "suggestion": "request_valid_time",
            }

        # Daily capacity check — must match create_hold to prevent
        # availability/create discrepancy
        cap = await self._settings_repository.check_daily_capacity(
            request.hotel_id, request.date, request.party_size,
        )
        if not cap["allowed"]:
            return {
                "available": False,
                "reason": "DAILY_CAPACITY_FULL",
                "suggestion": "handoff",
                "handoff_required": True,
                "count": cap["count"],
                "max": cap["max"],
                "party_size_total": cap.get("party_size_total"),
                "party_size_max": cap.get("party_size_max"),
            }

        slots = await self._restaurant_repository.get_available_slots(
            hotel_id=request.hotel_id,
            target_date=request.date,
            target_time=request.time,
            party_size=request.party_size,
            area=request.area,
        )
        return {
            "available": len(slots) > 0,
            "options": [slot.model_dump(mode="json") for slot in slots[:5]],
            "notes": "" if slots else "No available slot found for given criteria.",
        }


class RestaurantCreateHoldTool(BaseTool):
    """Create restaurant hold, reserve capacity, and trigger approval request."""

    def __init__(
        self,
        restaurant_repository: RestaurantRepository,
        approval_repository: ApprovalRequestRepository,
        notification_repository: NotificationRepository,
    ) -> None:
        self._restaurant_repository = restaurant_repository
        self._approval_tool = ApprovalRequestTool(approval_repository, notification_repository)
        self._notify_tool = NotifySendTool(notification_repository)
        self._settings_repository = RestaurantSettingsRepository()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Create hold with race-safe capacity checks and approval flow."""
        self.validate_required(kwargs, ["hotel_id", "slot_id", "guest_name", "phone", "party_size"])
        hotel_id = int(kwargs["hotel_id"])
        party_size = int(kwargs["party_size"])
        profile = get_profile(hotel_id)

        settings = await self._settings_repository.get(hotel_id)
        if party_size < settings.min_party_size or party_size > settings.max_party_size:
            return {
                "available": False,
                "reason": "PARTY_SIZE_OUT_OF_RANGE",
                "suggestion": "request_valid_party_size",
                "accepted_party_size_range": {
                    "min": settings.min_party_size,
                    "max": settings.max_party_size,
                },
            }

        # Daily capacity check
        slot_id = int(kwargs["slot_id"])
        slot_data = await self._restaurant_repository.get_slot_by_id(hotel_id=hotel_id, slot_id=slot_id)
        if slot_data:
            cap = await self._settings_repository.check_daily_capacity(hotel_id, slot_data["date"], party_size)
            if not cap["allowed"]:
                return {
                    "available": False,
                    "reason": "DAILY_CAPACITY_FULL",
                    "suggestion": "handoff",
                    "handoff_required": True,
                    "count": cap["count"],
                    "max": cap["max"],
                    "party_size_total": cap.get("party_size_total"),
                    "party_size_max": cap.get("party_size_max"),
                    "collected_reservation_context": {
                        "date": str(slot_data["date"]),
                        "time": slot_data["time"].isoformat(),
                        "party_size": party_size,
                        "guest_name": str(kwargs["guest_name"]),
                        "phone": str(kwargs["phone"]),
                        "area": str(kwargs["area"]) if kwargs.get("area") else slot_data.get("area"),
                        "notes": str(kwargs["notes"]) if kwargs.get("notes") else None,
                    },
                }

        if slot_data is None or not bool(slot_data["is_active"]):
            return {
                "available": False,
                "reason": "SLOT_NOT_AVAILABLE",
                "suggestion": "alternative_slot",
            }

        slot_matches = await self._restaurant_repository.get_available_slots(
            hotel_id=hotel_id,
            target_date=slot_data["date"],
            target_time=slot_data["time"],
            party_size=party_size,
            area=str(kwargs["area"]) if kwargs.get("area") else None,
        )
        if not slot_matches:
            return {
                "available": False,
                "reason": "NO_CAPACITY",
                "suggestion": "alternative_slot",
            }

        selected_slot_id = str(slot_id)
        if all(slot.slot_id != selected_slot_id for slot in slot_matches):
            return {
                "available": False,
                "reason": "SLOT_NOT_AVAILABLE",
                "suggestion": "alternative_slot",
            }
        if not _is_within_restaurant_hours(profile, slot_data["time"]):
            return {
                "available": False,
                "reason": "OUTSIDE_RESTAURANT_HOURS",
                "suggestion": "request_valid_time",
            }

        existing = await _find_recent_duplicate_hold(
            hotel_id=hotel_id,
            conversation_id=kwargs.get("conversation_id"),
            hold_date=slot_data["date"],
            hold_time=slot_data["time"],
            party_size=party_size,
            guest_name=str(kwargs["guest_name"]),
            phone=str(kwargs["phone"]),
        )
        if existing is not None:
            created = existing
        else:
            hold = RestaurantHold(
                hold_id="",
                hotel_id=hotel_id,
                conversation_id=kwargs.get("conversation_id"),
                slot_id=selected_slot_id,
                date=slot_data["date"],
                time=slot_data["time"],
                party_size=party_size,
                guest_name=str(kwargs["guest_name"]),
                phone=str(kwargs["phone"]),
                area=str(kwargs["area"]) if kwargs.get("area") else None,
                notes=str(kwargs["notes"]) if kwargs.get("notes") else None,
                status=RestaurantReservationStatus.BEKLEMEDE,
            )
            created = await self._restaurant_repository.create_hold(hold)

        # Approval flow / auto-confirm mode
        approval_request_id: str | None = None
        if settings.reservation_mode.value == "AI_RESTAURAN":
            await self._restaurant_repository.update_hold_status(
                hold_id=created.hold_id,
                status=RestaurantReservationStatus.ONAYLANDI,
                approved_by="AI_RESTAURAN",
            )
            created.status = RestaurantReservationStatus.ONAYLANDI
        else:
            try:
                approval_result = await self._approval_tool.execute(
                    hotel_id=hotel_id,
                    approval_type="RESTAURANT",
                    reference_id=created.hold_id,
                    details_summary=(
                        f"{created.date} {created.time}, {created.party_size} guests, "
                        f"{created.guest_name or 'Guest'}"
                    ),
                    required_roles=["ADMIN", "CHEF"],
                    any_of=True,
                )
                approval_request_id = approval_result.get("approval_request_id")
            except Exception:
                logger.error(
                    "restaurant_hold_approval_failed",
                    hold_id=created.hold_id,
                    hotel_id=hotel_id,
                )

        risk_flags: list[str] = []
        if _contains_allergy_notes(created.notes):
            risk_flags.append(RiskFlag.ALLERGY_ALERT.value)
            try:
                await self._notify_tool.execute(
                    hotel_id=hotel_id,
                    to_role="CHEF",
                    channel="panel",
                    message=f"Allergy/special diet note for restaurant hold {created.hold_id}.",
                    metadata={
                        "restaurant_hold_id": created.hold_id,
                        "risk_flag": RiskFlag.ALLERGY_ALERT.value,
                    },
                )
            except Exception:
                logger.warning(
                    "restaurant_hold_allergy_notify_failed",
                    hold_id=created.hold_id,
                )

        return {
            "restaurant_hold_id": created.hold_id,
            "status": created.status,
            "summary": f"{created.date} {created.time} for {created.party_size} guests",
            "approval_request_id": approval_request_id,
            "risk_flags": risk_flags,
        }


class RestaurantConfirmTool(BaseTool):
    """Set restaurant hold status to CONFIRMED."""

    def __init__(self, restaurant_repository: RestaurantRepository) -> None:
        self._restaurant_repository = restaurant_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Confirm hold by ID."""
        self.validate_required(kwargs, ["hotel_id", "restaurant_hold_id"])
        _ = int(kwargs["hotel_id"])
        hold_id = str(kwargs["restaurant_hold_id"])
        await self._restaurant_repository.update_hold_status(
            hold_id=hold_id,
            status=RestaurantReservationStatus.ONAYLANDI,
        )
        return {"restaurant_hold_id": hold_id, "status": RestaurantReservationStatus.ONAYLANDI}


class RestaurantModifyTool(BaseTool):
    """Update restaurant hold fields."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Modify mutable fields on restaurant hold."""
        self.validate_required(kwargs, ["hotel_id", "restaurant_hold_id", "updates"])
        updates = _RestaurantHoldUpdates.model_validate(kwargs["updates"])
        if updates.model_dump(exclude_none=True) == {}:
            raise ValueError("no_valid_update_field")

        # Recalculate table_type if party_size changed
        new_table_type = resolve_table_type(updates.party_size) if updates.party_size else None

        await execute(
            """
            UPDATE restaurant_holds
            SET date = COALESCE($3, date),
                time = COALESCE($4, time),
                party_size = COALESCE($5, party_size),
                guest_name = COALESCE($6, guest_name),
                phone = COALESCE($7, phone),
                area = COALESCE($8, area),
                notes = COALESCE($9, notes),
                slot_id = COALESCE($10, slot_id),
                table_type = COALESCE($11, table_type),
                updated_at = now()
            WHERE hotel_id = $1 AND hold_id = $2
            """,
            int(kwargs["hotel_id"]),
            str(kwargs["restaurant_hold_id"]),
            updates.date,
            updates.time,
            updates.party_size,
            updates.guest_name,
            updates.phone,
            updates.area,
            updates.notes,
            updates.slot_id,
            new_table_type,
        )
        return {"restaurant_hold_id": str(kwargs["restaurant_hold_id"]), "status": "UPDATED"}


class RestaurantCancelTool(BaseTool):
    """Cancel restaurant hold and restore capacity."""

    def __init__(self, restaurant_repository: RestaurantRepository) -> None:
        self._restaurant_repository = restaurant_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Cancel hold and release slot capacity."""
        self.validate_required(kwargs, ["hotel_id", "restaurant_hold_id"])
        _ = int(kwargs["hotel_id"])
        hold_id = str(kwargs["restaurant_hold_id"])
        await self._restaurant_repository.cancel_hold(
            hold_id=hold_id,
            reason=str(kwargs.get("reason", "Cancelled by request")),
        )
        return {"restaurant_hold_id": hold_id, "status": RestaurantReservationStatus.IPTAL}


def _is_within_restaurant_hours(profile: Any, target_time: time) -> bool:
    """Check whether target time is inside any configured meal window."""
    if profile is None or profile.restaurant is None:
        return True
    for interval in profile.restaurant.hours.values():
        if not isinstance(interval, str) or "-" not in interval:
            continue
        start_text, end_text = interval.split("-", 1)
        start = time.fromisoformat(start_text.strip())
        end = time.fromisoformat(end_text.strip())
        if start <= target_time <= end:
            return True
    return False


async def _find_recent_duplicate_hold(
    *,
    hotel_id: int,
    conversation_id: Any,
    hold_date: _dt.date,
    hold_time: _dt.time,
    party_size: int,
    guest_name: str,
    phone: str,
) -> RestaurantHold | None:
    """Return a recent duplicate hold to make create_hold idempotent across retries."""
    if conversation_id is None:
        return None
    row = await fetchrow(
        """
        SELECT *
        FROM restaurant_holds
        WHERE hotel_id = $1
          AND conversation_id = $2
          AND date = $3
          AND time = $4
          AND party_size = $5
          AND guest_name = $6
          AND phone = $7
          AND created_at >= now() - interval '10 minutes'
          AND status IN ('BEKLEMEDE', 'ONAYLANDI', 'DEGISIKLIK_UYGULA', 'PENDING_APPROVAL')
        ORDER BY created_at DESC
        LIMIT 1
        """,
        hotel_id,
        conversation_id,
        hold_date,
        hold_time,
        party_size,
        guest_name,
        phone,
    )
    if row is None:
        return None
    return RestaurantHold(
        id=row.get("id"),
        hold_id=row["hold_id"],
        hotel_id=row["hotel_id"],
        conversation_id=row.get("conversation_id"),
        slot_id=str(row["slot_id"]),
        date=row["date"],
        time=row["time"],
        party_size=row["party_size"],
        guest_name=row["guest_name"],
        phone=row["phone"],
        area=row.get("area"),
        notes=row.get("notes"),
        status=row["status"],
        table_type=row.get("table_type"),
        table_id=row.get("table_id"),
        approved_by=row.get("approved_by"),
        approved_at=row.get("approved_at"),
        rejected_reason=row.get("rejected_reason"),
        created_at=row.get("created_at"),
    )


def _contains_allergy_notes(notes: str | None) -> bool:
    """Detect allergy or special diet indications in user notes."""
    if not notes:
        return False
    return bool(ALLERGY_PATTERN.search(notes))
