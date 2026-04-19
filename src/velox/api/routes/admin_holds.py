"""Type-specific hold listing, lookup and creation endpoints for the admin panel."""

from __future__ import annotations

import datetime as _dt
from datetime import date
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

from velox.adapters.elektraweb import endpoints as elektraweb
from velox.api.middleware.auth import TokenData, check_permission, get_current_user
from velox.config.constants import (
    HoldStatus,
    RestaurantReservationMode,
    RestaurantReservationStatus,
    Role,
    resolve_table_type,
)
from velox.core.hotel_profile_loader import get_profile
from velox.db.database import fetch, fetchrow, fetchval
from velox.db.repositories.hotel import NotificationPhoneRepository
from velox.db.repositories.reservation import ReservationRepository
from velox.db.repositories.restaurant import RestaurantRepository
from velox.db.repositories.restaurant_floor_plan import (
    FloorPlanRepository,
    RestaurantSettingsRepository,
    RestaurantStatusManager,
)
from velox.db.repositories.transfer import TransferRepository
from velox.models.reservation import StayDraft, StayHold
from velox.models.restaurant import (
    FloorPlanCreate,
    FloorPlanUpdate,
    RestaurantHold,
    RestaurantHoldStatusChange,
    RestaurantHoldUpdateRequest,
    RestaurantSettingsUpdate,
)
from velox.models.transfer import TransferHold
from velox.tools.notification import send_admin_whatsapp_alerts, send_whatsapp_to_phone
from velox.utils.customer_notes import format_customer_visible_note
from velox.utils.json import decode_json_object

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-holds"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _effective_hotel(user: TokenData, hotel_id: int | None) -> int | None:
    """Resolve the effective hotel_id respecting user scope."""
    if user.role == Role.ADMIN:
        return hotel_id
    return user.hotel_id


def _safe_int(value: object) -> int:
    """Convert SQL scalar values to int with safe fallbacks."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value) if value.strip() else 0
    if isinstance(value, (bytes, bytearray)):
        decoded = value.decode(errors="ignore").strip()
        return int(decoded) if decoded else 0
    return 0


# ---------------------------------------------------------------------------
# Stay holds
# ---------------------------------------------------------------------------


@router.get("/holds/stay")
async def list_stay_holds(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
    reservation_no: str | None = Query(None),
    archived: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    """List stay holds with optional filters."""
    check_permission(user, "holds:read")
    effective = _effective_hotel(user, hotel_id)
    offset = (page - 1) * per_page

    archived_clause = "sh.archived_at IS NOT NULL" if archived else "sh.archived_at IS NULL"

    # If searching by reservation_no, do a direct lookup.
    if reservation_no and reservation_no.strip():
        row = await fetchrow(
            f"""
            SELECT sh.*, ar.decided_at AS approval_decided_at
            FROM stay_holds sh
            LEFT JOIN LATERAL (
                SELECT decided_at FROM approval_requests
                WHERE hotel_id = sh.hotel_id AND reference_id = sh.hold_id AND approval_type = 'STAY'
                ORDER BY created_at DESC LIMIT 1
            ) ar ON true
            WHERE sh.reservation_no = $1
              AND {archived_clause}
            """,
            reservation_no.strip(),
        )
        if row is None:
            return {"items": [], "total": 0, "page": 1, "per_page": per_page}
        item = _stay_row_to_dict(dict(row))
        if effective and item["hotel_id"] != effective:
            return {"items": [], "total": 0, "page": 1, "per_page": per_page}
        return {"items": [item], "total": 1, "page": 1, "per_page": per_page}

    items_query = f"""
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
          AND {archived_clause}
        ORDER BY sh.created_at DESC
        LIMIT $3 OFFSET $4
    """
    count_query = f"""
        SELECT COUNT(*) FROM stay_holds sh
        WHERE ($1::int IS NULL OR hotel_id = $1)
          AND ($2::text IS NULL OR status = $2)
          AND {archived_clause}
    """
    rows = await fetch(items_query, effective, status, per_page, offset)
    total = _safe_int(await fetchval(count_query, effective, status))
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
    email: str = ""
    nationality: str = "TR"
    checkin_date: date
    checkout_date: date
    adults: int = 1
    chd_ages: list[int] = Field(default_factory=list)
    total_price_eur: Decimal
    room_type_id: int = 0
    board_type_id: int = 0
    rate_type_id: int = 0
    rate_code_id: int = 0
    price_agency_id: int | None = None
    cancel_policy_type: str = "FREE_CANCEL"
    notes: str = ""
    room_type_name: str = ""
    board_type_name: str = ""


@router.post("/holds/stay/create")
async def create_stay_hold_from_panel(
    body: StayHoldCreateRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a stay hold directly from the admin panel."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN and body.hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    formatted_notes = format_customer_visible_note(body.notes)
    draft = {
        "guest_name": body.guest_name,
        "phone": body.phone,
        "email": body.email,
        "nationality": body.nationality,
        "checkin_date": str(body.checkin_date),
        "checkout_date": str(body.checkout_date),
        "adults": body.adults,
        "chd_ages": body.chd_ages,
        "total_price_eur": float(body.total_price_eur),
        "room_type_id": body.room_type_id,
        "board_type_id": body.board_type_id,
        "rate_type_id": body.rate_type_id,
        "rate_code_id": body.rate_code_id,
        "price_agency_id": body.price_agency_id,
        "cancel_policy_type": body.cancel_policy_type,
        "room_type_name": body.room_type_name,
        "board_type_name": body.board_type_name,
        "notes": formatted_notes,
    }
    try:
        draft = StayDraft.model_validate(draft).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Canli fiyat teklifi grounding bilgileri eksik veya gecersiz; stay hold olusturulamadi.",
        ) from exc
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


@router.post("/holds/stay/{hold_id}/clone")
async def clone_stay_hold_from_panel(
    hold_id: str,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Clone a previous stay hold and issue a fresh reservation number."""
    check_permission(user, "holds:approve")
    repo = ReservationRepository()
    source_hold = await repo.get_by_hold_id(hold_id)
    if source_hold is None:
        raise HTTPException(status_code=404, detail="Kaynak rezervasyon bulunamadi.")
    if user.role != Role.ADMIN and source_hold.hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    cloned_draft = dict(source_hold.draft_json or {})
    # Must be regenerated from the new hold row to keep voucher sync consistent.
    cloned_draft.pop("reservation_no", None)
    cloned_draft["notes"] = format_customer_visible_note(cloned_draft.get("notes"))
    try:
        cloned_draft = StayDraft.model_validate(cloned_draft).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Kaynak stay hold canli fiyat grounding bilgileri icermedigi icin klonlanamadi.",
        ) from exc

    cloned_hold = StayHold(
        hold_id="",
        hotel_id=source_hold.hotel_id,
        conversation_id=None,
        draft_json=cloned_draft,
        status=HoldStatus.PENDING_APPROVAL,
    )
    created = await repo.create_hold(cloned_hold)
    return {
        "status": "created",
        "hold_id": created.hold_id,
        "reservation_no": created.reservation_no,
        "source_hold_id": source_hold.hold_id,
        "source_reservation_no": source_hold.reservation_no,
    }


# ---------------------------------------------------------------------------
# Elektraweb proxy endpoints (availability, quote, room types)
# ---------------------------------------------------------------------------


@router.get("/elektraweb/room-types")
async def get_room_types(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(...),
) -> dict[str, Any]:
    """Return room types from hotel profile for the wizard room selector."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    profile = get_profile(hotel_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Hotel profili bulunamadi.")
    room_types = [rt.model_dump() for rt in profile.room_types]
    return {"room_types": room_types}


@router.get("/elektraweb/availability")
async def check_availability(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: Annotated[int, Query(...)],
    checkin: Annotated[date, Query(...)],
    checkout: Annotated[date, Query(...)],
    adults: Annotated[int, Query(ge=1)] = 1,
    chd_ages: Annotated[str, Query()] = "",
) -> dict[str, Any]:
    """Proxy Elektraweb availability check for the admin wizard."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if checkout <= checkin:
        raise HTTPException(status_code=400, detail="Cikis tarihi giris tarihinden sonra olmali.")

    parsed_ages = [int(a.strip()) for a in chd_ages.split(",") if a.strip().isdigit()] if chd_ages.strip() else []
    chd_count = len(parsed_ages)
    try:
        result = await elektraweb.availability(
            hotel_id=hotel_id,
            checkin=checkin,
            checkout=checkout,
            adults=adults,
            chd_count=chd_count,
            chd_ages=parsed_ages or None,
        )
        return result.model_dump(mode="json")
    except Exception as exc:
        logger.error("admin_availability_error", hotel_id=hotel_id, error=str(exc))
        raise HTTPException(status_code=502, detail="Elektraweb musaitlik sorgusu basarisiz.") from exc


@router.get("/elektraweb/quote")
async def get_quote(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: Annotated[int, Query(...)],
    checkin: Annotated[date, Query(...)],
    checkout: Annotated[date, Query(...)],
    adults: Annotated[int, Query(ge=1)] = 1,
    chd_ages: Annotated[str, Query()] = "",
    nationality: str = Query("TR"),
) -> dict[str, Any]:
    """Proxy Elektraweb quote for the admin wizard."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and hotel_id != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if checkout <= checkin:
        raise HTTPException(status_code=400, detail="Cikis tarihi giris tarihinden sonra olmali.")

    parsed_ages = [int(a.strip()) for a in chd_ages.split(",") if a.strip().isdigit()] if chd_ages.strip() else []
    chd_count = len(parsed_ages)
    try:
        result = await elektraweb.quote(
            hotel_id=hotel_id,
            checkin=checkin,
            checkout=checkout,
            adults=adults,
            chd_count=chd_count,
            chd_ages=parsed_ages or None,
            nationality=nationality,
        )
        return result.model_dump(mode="json")
    except Exception as exc:
        logger.error("admin_quote_error", hotel_id=hotel_id, error=str(exc))
        raise HTTPException(status_code=502, detail="Elektraweb fiyat sorgusu basarisiz.") from exc


# ---------------------------------------------------------------------------
# Restaurant holds
# ---------------------------------------------------------------------------


@router.get("/holds/restaurant")
async def list_restaurant_holds(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    archived: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    """List restaurant holds."""
    check_permission(user, "holds:read")
    effective = _effective_hotel(user, hotel_id)
    offset = (page - 1) * per_page
    if date_from and date_to and date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to must be >= date_from")

    archived_clause = "archived_at IS NOT NULL" if archived else "archived_at IS NULL"

    items_query = f"""
        SELECT hold_id, hotel_id, conversation_id, slot_id, date, time,
               party_size, guest_name, phone, area, notes, status,
               approved_by, approved_at, rejected_reason,
               table_id, table_type,
               arrived_at, no_show_at, extended_minutes,
               created_at, archived_at, archived_by, archived_reason
        FROM restaurant_holds
        WHERE ($1::int IS NULL OR hotel_id = $1)
          AND ($2::text IS NULL OR status = $2)
          AND ($3::date IS NULL OR date >= $3)
          AND ($4::date IS NULL OR date <= $4)
          AND {archived_clause}
        ORDER BY date ASC, time ASC, created_at DESC
        LIMIT $5 OFFSET $6
    """
    count_query = f"""
        SELECT COUNT(*) FROM restaurant_holds
        WHERE ($1::int IS NULL OR hotel_id = $1)
          AND ($2::text IS NULL OR status = $2)
          AND ($3::date IS NULL OR date >= $3)
          AND ($4::date IS NULL OR date <= $4)
          AND {archived_clause}
    """
    rows = await fetch(items_query, effective, status, date_from, date_to, per_page, offset)
    total = _safe_int(await fetchval(count_query, effective, status, date_from, date_to))
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
    formatted_notes = format_customer_visible_note(body.notes)

    # Daily capacity check
    settings_repo = RestaurantSettingsRepository()
    settings = await settings_repo.get(body.hotel_id)
    if settings.reservation_mode == RestaurantReservationMode.MANUEL:
        raise HTTPException(
            status_code=409,
            detail=(
                "Manuel modda panelden rezervasyon olusturma kapali. "
                "Rezervasyonlar webhook/AI akisindan gelmelidir."
            ),
        )

    slot_data = await RestaurantRepository().get_slot_by_id(hotel_id=body.hotel_id, slot_id=body.slot_id)
    if slot_data is None:
        raise HTTPException(status_code=404, detail="Secilen restoran slotu bulunamadi.")
    if slot_data:
        cap = await settings_repo.check_daily_capacity(body.hotel_id, slot_data["date"])
        if cap["enabled"] and not cap["allowed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Bu tarih icin gunluk rezervasyon kapasitesi dolmustur ({cap['count']}/{cap['max']}).",
            )

    hold = RestaurantHold(
        hold_id="",
        hotel_id=body.hotel_id,
        conversation_id=None,
        slot_id=str(body.slot_id),
        date=slot_data["date"],
        time=slot_data["time"],
        party_size=body.party_size,
        guest_name=body.guest_name,
        phone=body.phone,
        area=body.area,
        notes=formatted_notes or None,
        status=RestaurantReservationStatus.BEKLEMEDE,
    )
    repo = RestaurantRepository()
    created = await repo.create_hold(hold)

    # Send notifications to admin + chef
    slot_info = slot_data or {}
    notif_msg = (
        f"🍽️ Yeni Restoran Rezervasyonu\n"
        f"ID: {created.hold_id}\n"
        f"Misafir: {body.guest_name}\n"
        f"Kisi: {body.party_size}\n"
        f"Tarih: {slot_info.get('date', '-')} {slot_info.get('time', '')}\n"
        f"Alan: {body.area or '-'}\n"
        f"Not: {formatted_notes or '-'}"
    )
    try:
        # Admin notification
        await send_admin_whatsapp_alerts(
            hotel_id=body.hotel_id,
            message=notif_msg,
            phone_repo=NotificationPhoneRepository(),
        )
        # Chef notification
        settings = await settings_repo.get(body.hotel_id)
        if settings.chef_phone:
            await send_whatsapp_to_phone(
                phone=settings.chef_phone,
                message=notif_msg,
                hotel_id=body.hotel_id,
            )
    except Exception:
        logger.warning("restaurant_hold_notification_failed", hold_id=created.hold_id)

    return {
        "status": "created",
        "hold_id": created.hold_id,
        "table_type": created.table_type,
        "table_id": created.table_id,
    }


# ---------------------------------------------------------------------------
# Transfer holds
# ---------------------------------------------------------------------------


@router.get("/holds/transfer")
async def list_transfer_holds(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
    archived: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    """List transfer holds."""
    check_permission(user, "holds:read")
    effective = _effective_hotel(user, hotel_id)
    offset = (page - 1) * per_page

    archived_clause = "archived_at IS NOT NULL" if archived else "archived_at IS NULL"

    items_query = f"""
        SELECT hold_id, hotel_id, conversation_id, route, date, time,
               pax_count, guest_name, phone, flight_no, vehicle_type,
               baby_seat, price_eur, notes, status,
               approved_by, approved_at, rejected_reason, created_at,
               archived_at, archived_by, archived_reason
        FROM transfer_holds
        WHERE ($1::int IS NULL OR hotel_id = $1)
          AND ($2::text IS NULL OR status = $2)
          AND {archived_clause}
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    count_query = f"""
        SELECT COUNT(*) FROM transfer_holds
        WHERE ($1::int IS NULL OR hotel_id = $1)
          AND ($2::text IS NULL OR status = $2)
          AND {archived_clause}
    """
    rows = await fetch(items_query, effective, status, per_page, offset)
    total = _safe_int(await fetchval(count_query, effective, status))
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
    formatted_notes = format_customer_visible_note(body.notes)

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
        notes=formatted_notes or None,
        status=HoldStatus.PENDING_APPROVAL,
    )
    repo = TransferRepository()
    created = await repo.create_hold(hold)
    return {"status": "created", "hold_id": created.hold_id}


# ---------------------------------------------------------------------------
# Restaurant floor plan endpoints
# ---------------------------------------------------------------------------


@router.get("/hotels/{hotel_id}/restaurant/floor-plans")
async def get_active_floor_plan(
    hotel_id: int,
    user: Annotated[TokenData, Depends(get_current_user)],
    include_all: bool = False,
) -> dict[str, Any]:
    """Get active floor plan and optionally list all saved plans for a hotel."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    repo = FloorPlanRepository()
    plan = await repo.get_active_plan(hotel_id)
    payload: dict[str, Any] = {"plan": plan.model_dump(mode="json") if plan else None}
    if include_all:
        plans = await repo.list_plans(hotel_id)
        payload["plans"] = [item.model_dump(mode="json") for item in plans]
    return payload


@router.post("/hotels/{hotel_id}/restaurant/floor-plans")
async def create_floor_plan(
    hotel_id: int,
    body: FloorPlanCreate,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a new floor plan (deactivates existing)."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

    from velox.models.restaurant import FloorPlan as FloorPlanModel

    plan = FloorPlanModel(
        hotel_id=hotel_id,
        name=body.name,
        layout_data=body.layout_data,
        created_by=user.username,
    )
    repo = FloorPlanRepository()
    created = await repo.create_plan(hotel_id, plan)
    return {"status": "created", "plan": created.model_dump(mode="json")}


@router.put("/hotels/{hotel_id}/restaurant/floor-plans/{plan_id}")
async def update_floor_plan(
    hotel_id: int,
    plan_id: UUID,
    body: FloorPlanUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update an existing floor plan layout or name."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

    repo = FloorPlanRepository()
    updated = await repo.update_plan(hotel_id, plan_id, body.name, body.layout_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Plan bulunamadi")
    return {"status": "updated", "plan": updated.model_dump(mode="json")}


@router.post("/hotels/{hotel_id}/restaurant/floor-plans/{plan_id}/activate")
async def activate_floor_plan(
    hotel_id: int,
    plan_id: UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Set a specific floor plan as the active one."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

    repo = FloorPlanRepository()
    ok = await repo.activate_plan(hotel_id, plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plan bulunamadi")
    return {"status": "activated"}


@router.delete("/hotels/{hotel_id}/restaurant/floor-plans/{plan_id}")
async def delete_floor_plan(
    hotel_id: int,
    plan_id: UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Delete a non-active floor plan permanently."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

    repo = FloorPlanRepository()
    try:
        ok = await repo.delete_plan(hotel_id, plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=404, detail="Plan bulunamadi")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Restaurant daily view
# ---------------------------------------------------------------------------


@router.get("/hotels/{hotel_id}/restaurant/tables/daily-view")
async def get_daily_table_view(
    hotel_id: int,
    target_date: date,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get all tables with assigned reservations for a day."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    repo = FloorPlanRepository()
    items = await repo.get_daily_view(hotel_id, target_date)
    return {"items": [item.model_dump(mode="json") for item in items], "total": len(items)}


# ---------------------------------------------------------------------------
# Restaurant settings (daily capacity)
# ---------------------------------------------------------------------------


@router.get("/hotels/{hotel_id}/restaurant/settings")
async def get_restaurant_settings(
    hotel_id: int,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get restaurant settings (daily capacity toggle)."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")

    repo = RestaurantSettingsRepository()
    s = await repo.get(hotel_id)
    return {"settings": s.model_dump(mode="json")}


@router.put("/hotels/{hotel_id}/restaurant/settings")
async def update_restaurant_settings(
    hotel_id: int,
    body: RestaurantSettingsUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update restaurant settings (daily capacity toggle)."""
    check_permission(user, "holds:approve")
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

    repo = RestaurantSettingsRepository()
    current = await repo.get(hotel_id)
    if body.reservation_mode is not None:
        current.reservation_mode = body.reservation_mode
    if body.daily_max_reservations_enabled is not None:
        current.daily_max_reservations_enabled = body.daily_max_reservations_enabled
    if body.daily_max_reservations_count is not None:
        current.daily_max_reservations_count = body.daily_max_reservations_count
    if body.daily_max_party_size_enabled is not None:
        current.daily_max_party_size_enabled = body.daily_max_party_size_enabled
    if body.daily_max_party_size_count is not None:
        current.daily_max_party_size_count = body.daily_max_party_size_count
    if body.min_party_size is not None:
        current.min_party_size = body.min_party_size
    if body.max_party_size is not None:
        current.max_party_size = body.max_party_size
    if current.max_party_size < current.min_party_size:
        raise HTTPException(status_code=400, detail="max_party_size must be >= min_party_size")
    if body.chef_phone is not None:
        chef_phone = body.chef_phone.strip()
        current.chef_phone = chef_phone or None
    if body.service_mode_main_plan_id is not None:
        current.service_mode_main_plan_id = body.service_mode_main_plan_id
    if body.service_mode_pool_plan_id is not None:
        current.service_mode_pool_plan_id = body.service_mode_pool_plan_id

    updated = await repo.upsert(hotel_id, current)
    return {"status": "updated", "settings": updated.model_dump(mode="json")}


# ---------------------------------------------------------------------------
# Restaurant hold: update, status change, extend
# ---------------------------------------------------------------------------


@router.put("/holds/restaurant/{hold_id}")
async def update_restaurant_hold(
    hold_id: str,
    body: RestaurantHoldUpdateRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update editable fields on a restaurant hold (from table detail modal)."""
    check_permission(user, "holds:approve")

    update_fields = body.model_dump(exclude_none=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="Guncellenecek alan bulunamadi")

    current_hold = await fetchrow(
        "SELECT hold_id, hotel_id, date, time, table_id, table_type FROM restaurant_holds WHERE hold_id = $1",
        hold_id,
    )
    if current_hold is None:
        raise HTTPException(status_code=404, detail="Rezervasyon bulunamadi")

    # If party_size changed, recalculate table_type unless request explicitly sets it.
    table_type_update = body.table_type
    if body.party_size is not None and not table_type_update:
        table_type_update = resolve_table_type(body.party_size)

    # Allow explicit clear of table assignment by sending empty string.
    clear_table_assignment = body.table_id is not None and not body.table_id.strip()
    table_id_update: str | None = body.table_id
    if table_id_update is not None:
        table_id_update = table_id_update.strip() or None

    target_time = body.time if body.time is not None else current_hold["time"]
    target_table_id = (
        None
        if clear_table_assignment
        else (table_id_update if body.table_id is not None else current_hold["table_id"])
    )

    if target_table_id:
        conflict = await fetchrow(
            """
            SELECT hold_id
            FROM restaurant_holds
            WHERE hotel_id = $1
              AND date = $2
              AND time = $3
              AND table_id = $4
              AND hold_id != $5
              AND status NOT IN ('IPTAL', 'GELMEDI')
            LIMIT 1
            """,
            current_hold["hotel_id"],
            current_hold["date"],
            target_time,
            target_table_id,
            hold_id,
        )
        if conflict is not None:
            raise HTTPException(status_code=409, detail="Ayni masa/saat icin baska rezervasyon var")

    normalized_notes = body.notes
    if body.notes is not None:
        normalized_notes = format_customer_visible_note(body.notes) or None

    await fetchrow(
        """
        UPDATE restaurant_holds
        SET guest_name = COALESCE($2, guest_name),
            party_size = COALESCE($3, party_size),
            time = COALESCE($4, time),
            area = COALESCE($5, area),
            notes = COALESCE($6, notes),
            table_type = COALESCE($7, table_type),
            table_id = CASE
                WHEN $9::boolean THEN NULL
                WHEN $8::text IS NULL THEN table_id
                ELSE $8::text
            END,
            updated_at = now()
        WHERE hold_id = $1
        RETURNING hold_id
        """,
        hold_id,
        body.guest_name,
        body.party_size,
        body.time,
        body.area,
        normalized_notes,
        table_type_update,
        table_id_update,
        clear_table_assignment,
    )
    return {"status": "updated", "hold_id": hold_id}


@router.put("/holds/restaurant/{hold_id}/status")
async def change_restaurant_hold_status(
    hold_id: str,
    body: RestaurantHoldStatusChange,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Change reservation status with transition validation."""
    check_permission(user, "holds:approve")

    manager = RestaurantStatusManager()
    try:
        result = await manager.change_status(
            hold_id=hold_id,
            new_status=body.status,
            actor=user.username,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/holds/restaurant/{hold_id}/extend")
async def extend_restaurant_hold(
    hold_id: str,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Apply +15 minute extension to a restaurant reservation."""
    check_permission(user, "holds:approve")

    manager = RestaurantStatusManager()
    try:
        result = await manager.extend_time(hold_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
