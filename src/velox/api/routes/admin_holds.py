"""Type-specific hold listing, lookup and creation endpoints for the admin panel."""

from __future__ import annotations

import datetime as _dt
from datetime import date
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

import asyncpg
import orjson
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from velox.api.middleware.auth import TokenData, check_permission, get_current_user
from velox.config.constants import HoldStatus, Role
from velox.db.database import fetch, fetchrow, fetchval
from velox.db.repositories.reservation import ReservationRepository
from velox.db.repositories.restaurant import RestaurantRepository
from velox.db.repositories.transfer import TransferRepository
from velox.models.reservation import StayDraft, StayHold
from velox.models.restaurant import RestaurantHold
from velox.models.transfer import TransferHold
from velox.utils.json import decode_json_object

router = APIRouter(prefix="/admin", tags=["admin-holds"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _effective_hotel(user: TokenData, hotel_id: int | None) -> int | None:
    """Resolve the effective hotel_id respecting user scope."""
    if user.role == Role.ADMIN:
        return hotel_id
    return user.hotel_id


# ---------------------------------------------------------------------------
# Stay holds
# ---------------------------------------------------------------------------


@router.get("/holds/stay")
async def list_stay_holds(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
    reservation_no: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    """List stay holds with optional filters."""
    check_permission(user, "holds:read")
    effective = _effective_hotel(user, hotel_id)
    offset = (page - 1) * per_page

    # If searching by reservation_no, do a direct lookup.
    if reservation_no and reservation_no.strip():
        row = await fetchrow(
            """
            SELECT sh.*, ar.decided_at AS approval_decided_at
            FROM stay_holds sh
            LEFT JOIN LATERAL (
                SELECT decided_at FROM approval_requests
                WHERE hotel_id = sh.hotel_id AND reference_id = sh.hold_id AND approval_type = 'STAY'
                ORDER BY created_at DESC LIMIT 1
            ) ar ON true
            WHERE sh.reservation_no = $1
            """,
            reservation_no.strip(),
        )
        if row is None:
            return {"items": [], "total": 0, "page": 1, "per_page": per_page}
        item = _stay_row_to_dict(dict(row))
        if effective and item["hotel_id"] != effective:
            return {"items": [], "total": 0, "page": 1, "per_page": per_page}
        return {"items": [item], "total": 1, "page": 1, "per_page": per_page}

    items_query = """
        SELECT sh.*,
            ar.decided_at AS approval_decided_at,
            pr.created_at AS payment_requested_at
        FROM stay_holds sh
        LEFT JOIN LATERAL (
            SELECT decided_at FROM approval_requests
            WHERE hotel_id = sh.hotel_id AND reference_id = sh.hold_id AND approval_type = 'STAY'
            ORDER BY created_at DESC LIMIT 1
        ) ar ON true
        LEFT JOIN LATERAL (
            SELECT created_at FROM payment_requests
            WHERE hotel_id = sh.hotel_id
              AND (reference_id = sh.pms_reservation_id OR reference_id = sh.hold_id)
            ORDER BY created_at DESC LIMIT 1
        ) pr ON true
        WHERE ($1::int IS NULL OR sh.hotel_id = $1)
          AND ($2::text IS NULL OR sh.status = $2)
        ORDER BY sh.created_at DESC
        LIMIT $3 OFFSET $4
    """
    count_query = """
        SELECT COUNT(*) FROM stay_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
    """
    rows = await fetch(items_query, effective, status, per_page, offset)
    total = int(await fetchval(count_query, effective, status) or 0)
    return {
        "items": [_stay_row_to_dict(dict(r)) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def _stay_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a stay_holds row for frontend consumption."""
    row["type"] = "stay"
    row["draft_json"] = decode_json_object(row.get("draft_json"))
    # Remove internal UUID (not JSON-serializable by default)
    if "id" in row and isinstance(row["id"], UUID):
        row["id"] = str(row["id"])
    if "conversation_id" in row and isinstance(row["conversation_id"], UUID):
        row["conversation_id"] = str(row["conversation_id"])
    return row


@router.get("/holds/stay/by-reservation-no/{reservation_no}")
async def get_stay_hold_by_reservation_no(
    reservation_no: str,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Lookup a stay hold by reservation number."""
    check_permission(user, "holds:read")
    repo = ReservationRepository()
    hold = await repo.get_by_reservation_no(reservation_no)
    if hold is None:
        raise HTTPException(status_code=404, detail="Bu rezervasyon numarasiyla kayit bulunamadi.")
    if user.role != Role.ADMIN and hold.hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    result = hold.model_dump(mode="json")
    result["type"] = "stay"
    return result


class StayHoldCreateRequest(BaseModel):
    """Admin panel stay hold creation payload."""
    hotel_id: int
    guest_name: str
    phone: str
    checkin_date: date
    checkout_date: date
    adults: int = 1
    chd_ages: list[int] = Field(default_factory=list)
    total_price_eur: Decimal
    room_type_id: int = 0
    board_type_id: int = 0
    rate_type_id: int = 0
    rate_code_id: int = 0
    cancel_policy_type: str = "FREE_CANCEL"
    notes: str = ""


@router.post("/holds/stay/create")
async def create_stay_hold_from_panel(
    body: StayHoldCreateRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a stay hold directly from the admin panel."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN and body.hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    draft = {
        "guest_name": body.guest_name,
        "phone": body.phone,
        "checkin_date": str(body.checkin_date),
        "checkout_date": str(body.checkout_date),
        "adults": body.adults,
        "chd_ages": body.chd_ages,
        "total_price_eur": float(body.total_price_eur),
        "room_type_id": body.room_type_id,
        "board_type_id": body.board_type_id,
        "rate_type_id": body.rate_type_id,
        "rate_code_id": body.rate_code_id,
        "cancel_policy_type": body.cancel_policy_type,
        "notes": body.notes,
    }
    hold = StayHold(
        hold_id="",
        hotel_id=body.hotel_id,
        conversation_id=None,
        draft_json=draft,
        status=HoldStatus.PENDING_APPROVAL,
    )
    repo = ReservationRepository()
    created = await repo.create_hold(hold)
    return {
        "status": "created",
        "hold_id": created.hold_id,
        "reservation_no": created.reservation_no,
    }


# ---------------------------------------------------------------------------
# Restaurant holds
# ---------------------------------------------------------------------------


@router.get("/holds/restaurant")
async def list_restaurant_holds(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    """List restaurant holds."""
    check_permission(user, "holds:read")
    effective = _effective_hotel(user, hotel_id)
    offset = (page - 1) * per_page

    items_query = """
        SELECT hold_id, hotel_id, conversation_id, slot_id, date, time,
               party_size, guest_name, phone, area, notes, status,
               approved_by, approved_at, rejected_reason, created_at
        FROM restaurant_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    count_query = """
        SELECT COUNT(*) FROM restaurant_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
    """
    rows = await fetch(items_query, effective, status, per_page, offset)
    total = int(await fetchval(count_query, effective, status) or 0)
    items = []
    for r in rows:
        d = dict(r)
        d["type"] = "restaurant"
        if "conversation_id" in d and isinstance(d["conversation_id"], UUID):
            d["conversation_id"] = str(d["conversation_id"])
        items.append(d)
    return {"items": items, "total": total, "page": page, "per_page": per_page}


class RestaurantHoldCreateRequest(BaseModel):
    """Admin panel restaurant hold creation payload."""
    hotel_id: int
    slot_id: int
    party_size: int
    guest_name: str
    phone: str = ""
    area: str = ""
    notes: str = ""


@router.post("/holds/restaurant/create")
async def create_restaurant_hold_from_panel(
    body: RestaurantHoldCreateRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a restaurant hold from the admin panel."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN and body.hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    hold = RestaurantHold(
        hold_id="",
        hotel_id=body.hotel_id,
        conversation_id=None,
        slot_id=str(body.slot_id),
        party_size=body.party_size,
        guest_name=body.guest_name,
        phone=body.phone,
        area=body.area,
        notes=body.notes,
        status=HoldStatus.PENDING_APPROVAL,
    )
    repo = RestaurantRepository()
    created = await repo.create_hold(hold)
    return {"status": "created", "hold_id": created.hold_id}


# ---------------------------------------------------------------------------
# Transfer holds
# ---------------------------------------------------------------------------


@router.get("/holds/transfer")
async def list_transfer_holds(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    """List transfer holds."""
    check_permission(user, "holds:read")
    effective = _effective_hotel(user, hotel_id)
    offset = (page - 1) * per_page

    items_query = """
        SELECT hold_id, hotel_id, conversation_id, route, date, time,
               pax_count, guest_name, phone, flight_no, vehicle_type,
               baby_seat, price_eur, notes, status,
               approved_by, approved_at, rejected_reason, created_at
        FROM transfer_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    count_query = """
        SELECT COUNT(*) FROM transfer_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
    """
    rows = await fetch(items_query, effective, status, per_page, offset)
    total = int(await fetchval(count_query, effective, status) or 0)
    items = []
    for r in rows:
        d = dict(r)
        d["type"] = "transfer"
        if "conversation_id" in d and isinstance(d["conversation_id"], UUID):
            d["conversation_id"] = str(d["conversation_id"])
        items.append(d)
    return {"items": items, "total": total, "page": page, "per_page": per_page}


class TransferHoldCreateRequest(BaseModel):
    """Admin panel transfer hold creation payload."""
    hotel_id: int
    route: str
    date: date
    time: _dt.time | None = None
    pax_count: int = 1
    guest_name: str
    phone: str = ""
    flight_no: str | None = None
    vehicle_type: str | None = None
    baby_seat: bool = False
    price_eur: Decimal | None = None
    notes: str = ""


@router.post("/holds/transfer/create")
async def create_transfer_hold_from_panel(
    body: TransferHoldCreateRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a transfer hold from the admin panel."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN and body.hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    hold = TransferHold(
        hold_id="",
        hotel_id=body.hotel_id,
        conversation_id=None,
        route=body.route,
        date=body.date,
        time=body.time,
        pax_count=body.pax_count,
        guest_name=body.guest_name,
        phone=body.phone,
        flight_no=body.flight_no,
        vehicle_type=body.vehicle_type,
        baby_seat=body.baby_seat,
        price_eur=body.price_eur,
        notes=body.notes,
        status=HoldStatus.PENDING_APPROVAL,
    )
    repo = TransferRepository()
    created = await repo.create_hold(hold)
    return {"status": "created", "hold_id": created.hold_id}
