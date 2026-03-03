"""Restaurant availability and hold management tools."""

from datetime import date, time
from typing import Any

import structlog
from pydantic import BaseModel

from velox.db.database import execute, fetchrow
from velox.db.repositories.restaurant import RestaurantRepository
from velox.models.restaurant import RestaurantAvailabilityRequest, RestaurantHold
from velox.tools.base import BaseTool

logger = structlog.get_logger(__name__)


class _RestaurantHoldUpdates(BaseModel):
    date: date | None = None
    time: time | None = None
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

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "date", "time", "party_size"])
        request = RestaurantAvailabilityRequest.model_validate(kwargs)
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
    """Create restaurant hold and reserve slot capacity."""

    def __init__(self, restaurant_repository: RestaurantRepository) -> None:
        self._restaurant_repository = restaurant_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "slot_id", "guest_name", "phone", "party_size"])
        slot = await fetchrow(
            "SELECT * FROM restaurant_slots WHERE id = $1 AND hotel_id = $2 AND is_active = true",
            int(kwargs["slot_id"]),
            int(kwargs["hotel_id"]),
        )
        if slot is None:
            raise ValueError("slot_id not found")

        capacity_left = int(slot["total_capacity"]) - int(slot["booked_count"])
        if capacity_left < int(kwargs["party_size"]):
            return {"available": False, "error": "Slot capacity is not enough."}

        hold = RestaurantHold(
            hold_id="",
            hotel_id=int(kwargs["hotel_id"]),
            conversation_id=kwargs.get("conversation_id"),
            slot_id=str(kwargs["slot_id"]),
            date=slot["date"],
            time=slot["time"],
            party_size=int(kwargs["party_size"]),
            guest_name=str(kwargs["guest_name"]),
            phone=str(kwargs["phone"]),
            area=str(kwargs["area"]) if kwargs.get("area") else None,
            notes=str(kwargs["notes"]) if kwargs.get("notes") else None,
        )
        created = await self._restaurant_repository.create_hold(hold)
        await self._restaurant_repository.increment_booked_count(int(kwargs["slot_id"]), increment=hold.party_size)
        return {
            "restaurant_hold_id": created.hold_id,
            "status": created.status.value,
            "summary": f"{created.date} {created.time} for {created.party_size} guests",
        }


class RestaurantConfirmTool(BaseTool):
    """Set restaurant hold status to CONFIRMED."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "restaurant_hold_id"])
        await execute(
            """
            UPDATE restaurant_holds
            SET status = 'CONFIRMED', approved_at = now(), updated_at = now()
            WHERE hotel_id = $1 AND hold_id = $2
            """,
            int(kwargs["hotel_id"]),
            str(kwargs["restaurant_hold_id"]),
        )
        return {"restaurant_hold_id": str(kwargs["restaurant_hold_id"]), "status": "CONFIRMED"}


class RestaurantModifyTool(BaseTool):
    """Update restaurant hold fields."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "restaurant_hold_id", "updates"])
        updates = _RestaurantHoldUpdates.model_validate(kwargs["updates"])
        if updates.model_dump(exclude_none=True) == {}:
            raise ValueError("No valid update field provided.")
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
        )
        return {"restaurant_hold_id": str(kwargs["restaurant_hold_id"]), "status": "UPDATED"}


class RestaurantCancelTool(BaseTool):
    """Cancel restaurant hold and restore capacity."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "restaurant_hold_id"])
        row = await fetchrow(
            "SELECT slot_id, party_size FROM restaurant_holds WHERE hotel_id = $1 AND hold_id = $2",
            int(kwargs["hotel_id"]),
            str(kwargs["restaurant_hold_id"]),
        )
        if row is None:
            raise ValueError("restaurant_hold_id not found")

        await execute(
            """
            UPDATE restaurant_holds
            SET status = 'CANCELLED', rejected_reason = $3, updated_at = now()
            WHERE hotel_id = $1 AND hold_id = $2
            """,
            int(kwargs["hotel_id"]),
            str(kwargs["restaurant_hold_id"]),
            str(kwargs.get("reason", "Cancelled by request")),
        )
        if row["slot_id"]:
            await execute(
                "UPDATE restaurant_slots SET booked_count = GREATEST(0, booked_count - $2) WHERE id = $1",
                int(row["slot_id"]),
                int(row["party_size"] or 0),
            )
        return {"restaurant_hold_id": str(kwargs["restaurant_hold_id"]), "status": "CANCELLED"}
