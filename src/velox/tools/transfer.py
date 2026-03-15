"""Transfer information and hold management tools."""

from __future__ import annotations

import datetime as _dt
import re
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel

from velox.core.hotel_profile_loader import get_profile
from velox.db.database import execute, fetchrow
from velox.db.repositories.transfer import TransferRepository
from velox.models.transfer import TransferHold, TransferInfoRequest
from velox.tools.base import BaseTool

FLIGHT_DELAY_PATTERN = re.compile(
    r"(flight\s*delay|delayed|delay|gecik|r[oö]tar|late\s*flight)",
    flags=re.IGNORECASE,
)


class _TransferHoldUpdates(BaseModel):
    date: _dt.date | None = None
    time: _dt.time | None = None
    pax_count: int | None = None
    guest_name: str | None = None
    phone: str | None = None
    flight_no: str | None = None
    baby_seat: bool | None = None
    notes: str | None = None


class TransferGetInfoTool(BaseTool):
    """Read transfer route information from HOTEL_PROFILE."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "route", "pax_count"])
        request = TransferInfoRequest.model_validate(kwargs)
        profile = get_profile(request.hotel_id)
        if profile is None:
            return {"found": False, "error": "Hotel profile not found."}

        route_code = request.route.upper()
        for route in profile.transfer_routes:
            if route.route_code.upper() == route_code:
                if request.pax_count <= route.max_pax:
                    return {
                        "route": route.route_code,
                        "distance_km": None,
                        "duration_min": route.duration_min,
                        "price_eur": float(route.price_eur),
                        "vehicle_type": route.vehicle_type,
                        "max_pax": route.max_pax,
                        "baby_seat_available": route.baby_seat,
                        "notes": "",
                    }
                if route.oversize_vehicle:
                    return {
                        "route": route.route_code,
                        "distance_km": None,
                        "duration_min": route.duration_min,
                        "price_eur": float(route.oversize_vehicle.get("price_eur", route.price_eur)),
                        "vehicle_type": str(route.oversize_vehicle.get("type", "oversize")),
                        "max_pax": int(route.oversize_vehicle.get("max_pax", request.pax_count)),
                        "baby_seat_available": route.baby_seat,
                        "notes": "Oversize vehicle required.",
                    }
                return {"found": False, "error": "Pax count exceeds route capacity."}
        return {
            "found": False,
            "reason": "CUSTOM_ROUTE",
            "suggestion": "handoff_admin",
            "escalation": {
                "level": "L2",
                "route_to_role": "ADMIN",
            },
            "notes": "Custom or unknown route requires admin confirmation.",
        }


class TransferCreateHoldTool(BaseTool):
    """Create transfer hold in DB."""

    def __init__(self, transfer_repository: TransferRepository) -> None:
        self._transfer_repository = transfer_repository
        self._info_tool = TransferGetInfoTool()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "route", "date", "time", "pax_count", "guest_name", "phone"])
        hotel_id = int(kwargs["hotel_id"])
        info = await self._info_tool.execute(
            hotel_id=hotel_id,
            route=str(kwargs["route"]),
            pax_count=int(kwargs["pax_count"]),
        )
        if not info.get("price_eur"):
            response = {"error": info.get("error", "Transfer info not found.")}
            if "suggestion" in info:
                response["suggestion"] = info["suggestion"]
            if "escalation" in info:
                response["escalation"] = info["escalation"]
            if "reason" in info:
                response["reason"] = info["reason"]
            return response

        hold = TransferHold(
            hold_id="",
            hotel_id=hotel_id,
            conversation_id=kwargs.get("conversation_id"),
            route=str(kwargs["route"]),
            date=kwargs["date"],
            time=kwargs["time"],
            pax_count=int(kwargs["pax_count"]),
            guest_name=str(kwargs["guest_name"]),
            phone=str(kwargs["phone"]),
            flight_no=str(kwargs["flight_no"]) if kwargs.get("flight_no") else None,
            vehicle_type=str(info.get("vehicle_type", "")),
            baby_seat=bool(kwargs.get("baby_seat", False)),
            price_eur=Decimal(str(info["price_eur"])),
            notes=str(kwargs["notes"]) if kwargs.get("notes") else None,
        )
        created = await self._transfer_repository.create_hold(hold)
        result: dict[str, Any] = {
            "transfer_hold_id": created.hold_id,
            "status": created.status.value,
            "summary": (
                f"{created.route} {created.date} {created.time} "
                f"{created.pax_count} pax {created.price_eur} EUR"
            ),
        }

        escalation: dict[str, str] | None = _same_day_urgent_escalation(
            hold_date=created.date,
            hold_time=created.time,
            hotel_id=hotel_id,
        )
        if escalation is not None:
            result["escalation"] = escalation

        ops_notification: dict[str, str] | None = _flight_delay_notification(created.notes)
        if ops_notification is not None:
            result["ops_notification"] = ops_notification

        return result


class TransferConfirmTool(BaseTool):
    """Set transfer hold status to CONFIRMED."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "transfer_hold_id"])
        await execute(
            """
            UPDATE transfer_holds
            SET status = 'CONFIRMED', approved_at = now(), updated_at = now()
            WHERE hotel_id = $1 AND hold_id = $2
            """,
            int(kwargs["hotel_id"]),
            str(kwargs["transfer_hold_id"]),
        )
        return {"transfer_hold_id": str(kwargs["transfer_hold_id"]), "status": "CONFIRMED"}


class TransferModifyTool(BaseTool):
    """Update transfer hold fields."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "transfer_hold_id", "updates"])
        updates = _TransferHoldUpdates.model_validate(kwargs["updates"])
        if updates.model_dump(exclude_none=True) == {}:
            raise ValueError("No valid update field provided.")
        await execute(
            """
            UPDATE transfer_holds
            SET date = COALESCE($3, date),
                time = COALESCE($4, time),
                pax_count = COALESCE($5, pax_count),
                guest_name = COALESCE($6, guest_name),
                phone = COALESCE($7, phone),
                flight_no = COALESCE($8, flight_no),
                baby_seat = COALESCE($9, baby_seat),
                notes = COALESCE($10, notes),
                updated_at = now()
            WHERE hotel_id = $1 AND hold_id = $2
            """,
            int(kwargs["hotel_id"]),
            str(kwargs["transfer_hold_id"]),
            updates.date,
            updates.time,
            updates.pax_count,
            updates.guest_name,
            updates.phone,
            updates.flight_no,
            updates.baby_seat,
            updates.notes,
        )
        return {"transfer_hold_id": str(kwargs["transfer_hold_id"]), "status": "UPDATED"}


class TransferCancelTool(BaseTool):
    """Cancel transfer hold."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "transfer_hold_id"])
        row = await fetchrow(
            "SELECT hold_id FROM transfer_holds WHERE hotel_id = $1 AND hold_id = $2",
            int(kwargs["hotel_id"]),
            str(kwargs["transfer_hold_id"]),
        )
        if row is None:
            raise ValueError("transfer_hold_id not found")

        await execute(
            """
            UPDATE transfer_holds
            SET status = 'CANCELLED', rejected_reason = $3, updated_at = now()
            WHERE hotel_id = $1 AND hold_id = $2
            """,
            int(kwargs["hotel_id"]),
            str(kwargs["transfer_hold_id"]),
            str(kwargs.get("reason", "Cancelled by request")),
        )
        return {"transfer_hold_id": str(kwargs["transfer_hold_id"]), "status": "CANCELLED"}


def _same_day_urgent_escalation(hold_date: date, hold_time: time, hotel_id: int) -> dict[str, str] | None:
    """Return L2 OPS escalation for same-day transfers within next 3 hours."""
    profile = get_profile(hotel_id)
    timezone_name = profile.timezone if profile else "UTC"
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

    now = datetime.now(tz)
    hold_dt = datetime.combine(hold_date, hold_time, tzinfo=tz)
    if hold_dt.date() != now.date():
        return None
    time_to_transfer = hold_dt - now
    if 0 <= time_to_transfer.total_seconds() < 3 * 3600:
        return {
            "level": "L2",
            "route_to_role": "OPS",
            "reason": "SAME_DAY_URGENT",
        }
    return None


def _flight_delay_notification(notes: str | None) -> dict[str, str] | None:
    """Return L1 OPS notification hint when notes indicate flight delay."""
    if not notes:
        return None
    if not FLIGHT_DELAY_PATTERN.search(notes):
        return None
    return {
        "level": "L1",
        "to_role": "OPS",
        "reason": "FLIGHT_DELAY_REPORTED",
    }
