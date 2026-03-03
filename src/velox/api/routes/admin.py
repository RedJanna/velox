"""Admin panel REST API routes."""

from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from passlib.hash import bcrypt
from pydantic import BaseModel, Field

from velox.api.middleware.auth import (
    TokenData,
    TokenResponse,
    check_permission,
    create_access_token,
    get_current_user,
    require_role,
)
from velox.config.constants import HoldStatus, Role
from velox.config.settings import settings
from velox.core.hotel_profile_loader import reload_profiles
from velox.db.repositories.restaurant import RestaurantRepository
from velox.models.restaurant import RestaurantSlotCreate, RestaurantSlotUpdate
from velox.core.template_engine import reload_templates
from velox.escalation.matrix import reload_matrix

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_HOLD_TYPES = {"stay", "restaurant", "transfer"}
HOLD_TABLES = {
    "S_HOLD_": ("stay_holds", "stay"),
    "R_HOLD_": ("restaurant_holds", "restaurant"),
    "TR_HOLD_": ("transfer_holds", "transfer"),
}


class LoginRequest(BaseModel):
    username: str
    password: str


class HotelProfileUpdate(BaseModel):
    profile_json: dict[str, Any]


class ApproveRequest(BaseModel):
    notes: str | None = None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1)


class TicketUpdate(BaseModel):
    status: str | None = None
    assigned_to_role: str | None = None
    assigned_to_name: str | None = None


@router.post("/login", response_model=TokenResponse)
async def admin_login(body: LoginRequest, request: Request) -> TokenResponse:
    """Authenticate admin user and return JWT token."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, hotel_id, username, password_hash, role, display_name, is_active
            FROM admin_users WHERE username = $1
            """,
            body.username,
        )

    if not row or not bcrypt.verify(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Account disabled")

    token_data = TokenData(
        user_id=int(row["id"]),
        hotel_id=int(row["hotel_id"]),
        username=str(row["username"]),
        role=Role(row["role"]),
        display_name=row["display_name"],
    )
    access_token = create_access_token(token_data)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.admin_jwt_expire_minutes * 60,
        role=token_data.role.value,
        hotel_id=token_data.hotel_id,
    )


@router.post("/reload-config")
async def reload_config(user: Annotated[TokenData, Depends(require_role(Role.ADMIN))]) -> dict[str, object]:
    """Reload profile, escalation matrix, and templates from disk."""
    _ = user
    profiles = reload_profiles()
    matrix = reload_matrix()
    templates = reload_templates()
    return {
        "reloaded": True,
        "profiles_count": len(profiles),
        "matrix_entries_count": len(matrix),
        "templates_count": len(templates),
    }


@router.get("/hotels")
async def list_hotels(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    """List hotels; ADMIN sees all, others see own hotel."""
    check_permission(user, "hotels:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        if user.role == Role.ADMIN:
            rows = await conn.fetch(
                """
                SELECT id, hotel_id, name_tr, name_en, hotel_type, is_active, created_at
                FROM hotels ORDER BY id
                """
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, hotel_id, name_tr, name_en, hotel_type, is_active, created_at
                FROM hotels WHERE hotel_id = $1
                """,
                user.hotel_id,
            )
    return [dict(row) for row in rows]


@router.get("/hotels/{hotel_id}")
async def get_hotel(
    hotel_id: int,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return hotel detail with profile JSON."""
    check_permission(user, "hotels:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM hotels WHERE hotel_id = $1", hotel_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return dict(row)


@router.put("/hotels/{hotel_id}/profile")
async def update_hotel_profile(
    hotel_id: int,
    body: HotelProfileUpdate,
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Update hotel profile JSON; ADMIN only."""
    _ = user
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE hotels
            SET profile_json = $1, updated_at = now()
            WHERE hotel_id = $2
            """,
            body.profile_json,
            hotel_id,
        )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {"status": "updated", "hotel_id": hotel_id}


@router.post("/hotels/{hotel_id}/restaurant/slots")
async def create_restaurant_slots(
    hotel_id: int,
    slots: list[RestaurantSlotCreate],
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Create restaurant slots for one or more date ranges."""
    _ = user
    repository = RestaurantRepository()
    try:
        created_count = await repository.create_slots(hotel_id=hotel_id, slots=slots)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "created", "created_count": created_count}


@router.get("/hotels/{hotel_id}/restaurant/slots")
async def list_restaurant_slots(
    hotel_id: int,
    date_from: date,
    date_to: date,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """List restaurant slots with remaining capacity."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to must be >= date_from")

    repository = RestaurantRepository()
    slots = await repository.list_slots(hotel_id=hotel_id, date_from=date_from, date_to=date_to)
    return {"items": [slot.model_dump(mode="json") for slot in slots], "total": len(slots)}


@router.put("/hotels/{hotel_id}/restaurant/slots/{slot_id}")
async def update_restaurant_slot(
    hotel_id: int,
    slot_id: int,
    update: RestaurantSlotUpdate,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Update restaurant slot capacity or active flag."""
    _ = user
    if update.total_capacity is None and update.is_active is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    repository = RestaurantRepository()
    try:
        row = await repository.update_slot(hotel_id=hotel_id, slot_id=slot_id, update=update)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Slot not found")
    return {"status": "updated", "slot": row}


@router.get("/conversations")
async def list_conversations(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List conversations with filters and pagination."""
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool

    conditions: list[str] = []
    params: list[Any] = []
    param_idx = 1

    effective_hotel_id = hotel_id if user.role == Role.ADMIN and hotel_id else user.hotel_id
    conditions.append(f"c.hotel_id = ${param_idx}")
    params.append(effective_hotel_id)
    param_idx += 1

    if status_filter:
        conditions.append(f"c.current_state = ${param_idx}")
        params.append(status_filter)
        param_idx += 1
    if date_from:
        conditions.append(f"c.created_at >= ${param_idx}")
        params.append(date_from)
        param_idx += 1
    if date_to:
        conditions.append(f"c.created_at <= ${param_idx}")
        params.append(date_to)
        param_idx += 1

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * per_page
    query = f"""
        SELECT c.id, c.hotel_id, c.phone_display, c.language, c.current_state,
               c.current_intent, c.risk_flags, c.is_active, c.last_message_at, c.created_at,
               (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
        FROM conversations c
        WHERE {where_clause}
        ORDER BY c.last_message_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([per_page, offset])

    async with db.acquire() as conn:
        rows = await conn.fetch(query, *params)
        count_query = f"SELECT COUNT(*) FROM conversations c WHERE {where_clause}"
        total = int(await conn.fetchval(count_query, *params[: param_idx - 1]) or 0)

    return {"items": [dict(row) for row in rows], "total": total, "page": page, "per_page": per_page}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return conversation with full message history."""
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        conv = await conn.fetchrow("SELECT * FROM conversations WHERE id = $1", conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if user.role != Role.ADMIN and int(conv["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")
        messages = await conn.fetch(
            """
            SELECT id, role, content, internal_json, tool_calls, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            """,
            conversation_id,
        )
    return {"conversation": dict(conv), "messages": [dict(row) for row in messages]}


@router.get("/holds")
async def list_holds(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hold_type: str | None = Query(None, description="stay, restaurant, or transfer"),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List holds in unified view, filterable by type and status."""
    check_permission(user, "holds:read")
    if hold_type and hold_type not in ALLOWED_HOLD_TYPES:
        raise HTTPException(status_code=400, detail="hold_type must be one of: stay, restaurant, transfer")
    if status_filter and status_filter not in {status.value for status in HoldStatus}:
        raise HTTPException(status_code=400, detail="Invalid hold status")

    db = request.app.state.db_pool
    results: list[dict[str, Any]] = []

    async with db.acquire() as conn:
        if hold_type in (None, "stay"):
            query = """
                SELECT hold_id, 'stay' AS type, hotel_id, status, draft_json,
                       approved_by, created_at, conversation_id
                FROM stay_holds
                WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
            """
            rows = await conn.fetch(
                query,
                None if user.role == Role.ADMIN else user.hotel_id,
                status_filter,
            )
            results.extend(dict(row) for row in rows)

        if hold_type in (None, "restaurant"):
            query = """
                SELECT hold_id, 'restaurant' AS type, hotel_id, status,
                       json_build_object(
                           'date', date,
                           'time', time,
                           'party_size', party_size,
                           'guest_name', guest_name,
                           'area', area
                       ) AS draft_json,
                       approved_by, created_at, conversation_id
                FROM restaurant_holds
                WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
            """
            rows = await conn.fetch(
                query,
                None if user.role == Role.ADMIN else user.hotel_id,
                status_filter,
            )
            results.extend(dict(row) for row in rows)

        if hold_type in (None, "transfer"):
            query = """
                SELECT hold_id, 'transfer' AS type, hotel_id, status,
                       json_build_object(
                           'route', route,
                           'date', date,
                           'time', time,
                           'pax_count', pax_count,
                           'guest_name', guest_name,
                           'price_eur', price_eur
                       ) AS draft_json,
                       approved_by, created_at, conversation_id
                FROM transfer_holds
                WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
            """
            rows = await conn.fetch(
                query,
                None if user.role == Role.ADMIN else user.hotel_id,
                status_filter,
            )
            results.extend(dict(row) for row in rows)

    results.sort(key=lambda row: row["created_at"], reverse=True)
    total = len(results)
    offset = (page - 1) * per_page
    paged_items = results[offset : offset + per_page]
    return {"items": paged_items, "total": total, "page": page, "per_page": per_page}


def _resolve_hold_target(hold_id: str) -> tuple[str, str]:
    """Resolve table/type by hold id prefix."""
    for prefix, target in HOLD_TABLES.items():
        if hold_id.startswith(prefix):
            return target
    raise HTTPException(status_code=400, detail="Unknown hold_id prefix")


@router.post("/holds/{hold_id}/approve")
async def approve_hold(
    hold_id: str,
    body: ApproveRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Approve hold and update related approval request."""
    _ = body
    check_permission(user, "holds:approve")
    table, hold_type = _resolve_hold_target(hold_id)
    db = request.app.state.db_pool

    async with db.acquire() as conn:
        row = await conn.fetchrow(f"SELECT * FROM {table} WHERE hold_id = $1", hold_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Hold not found")
        if row["status"] != HoldStatus.PENDING_APPROVAL:
            raise HTTPException(status_code=409, detail=f"Hold is not pending approval (current: {row['status']})")
        if user.role != Role.ADMIN and int(row["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")

        await conn.execute(
            f"""
            UPDATE {table}
            SET status = $1, approved_by = $2, approved_at = now(), updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.APPROVED.value,
            user.username,
            hold_id,
        )
        await conn.execute(
            """
            UPDATE approval_requests
            SET status = 'APPROVED', decided_by_role = $1, decided_by_name = $2, decided_at = now()
            WHERE reference_id = $3 AND status = 'REQUESTED'
            """,
            user.role.value,
            user.username,
            hold_id,
        )
    return {"status": "approved", "hold_id": hold_id, "hold_type": hold_type}


@router.post("/holds/{hold_id}/reject")
async def reject_hold(
    hold_id: str,
    body: RejectRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Reject hold and store reason."""
    check_permission(user, "holds:reject")
    table, _ = _resolve_hold_target(hold_id)
    db = request.app.state.db_pool

    async with db.acquire() as conn:
        row = await conn.fetchrow(f"SELECT * FROM {table} WHERE hold_id = $1", hold_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Hold not found")
        if row["status"] != HoldStatus.PENDING_APPROVAL:
            raise HTTPException(status_code=409, detail=f"Hold is not pending approval (current: {row['status']})")
        if user.role != Role.ADMIN and int(row["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")

        await conn.execute(
            f"""
            UPDATE {table}
            SET status = $1, rejected_reason = $2, updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.REJECTED.value,
            body.reason,
            hold_id,
        )
        await conn.execute(
            """
            UPDATE approval_requests
            SET status = 'REJECTED', decided_by_role = $1, decided_by_name = $2, decided_at = now()
            WHERE reference_id = $3 AND status = 'REQUESTED'
            """,
            user.role.value,
            user.username,
            hold_id,
        )
    return {"status": "rejected", "hold_id": hold_id, "reason": body.reason}


@router.get("/tickets")
async def list_tickets(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List tickets with role-based visibility and filters."""
    check_permission(user, "tickets:read")
    db = request.app.state.db_pool

    conditions: list[str] = []
    params: list[Any] = []
    param_idx = 1

    effective_hotel_id = hotel_id if user.role == Role.ADMIN and hotel_id else user.hotel_id
    conditions.append(f"hotel_id = ${param_idx}")
    params.append(effective_hotel_id)
    param_idx += 1

    if user.role != Role.ADMIN:
        conditions.append(f"assigned_to_role = ${param_idx}")
        params.append(user.role.value)
        param_idx += 1
    if status_filter:
        conditions.append(f"status = ${param_idx}")
        params.append(status_filter)
        param_idx += 1
    if priority:
        conditions.append(f"priority = ${param_idx}")
        params.append(priority)
        param_idx += 1

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * per_page
    query = f"""
        SELECT ticket_id, hotel_id, conversation_id, reason, transcript_summary,
               priority, dedupe_key, status, assigned_to_role, assigned_to_name,
               resolved_at, created_at
        FROM tickets
        WHERE {where_clause}
        ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, created_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([per_page, offset])

    async with db.acquire() as conn:
        rows = await conn.fetch(query, *params)
        count_query = f"SELECT COUNT(*) FROM tickets WHERE {where_clause}"
        total = int(await conn.fetchval(count_query, *params[: param_idx - 1]) or 0)
    return {"items": [dict(row) for row in rows], "total": total, "page": page, "per_page": per_page}


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update ticket status and assignment."""
    check_permission(user, "tickets:write")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_id = $1", ticket_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if user.role != Role.ADMIN:
            if int(row["hotel_id"]) != user.hotel_id:
                raise HTTPException(status_code=403, detail="Access denied")
            if row["assigned_to_role"] != user.role.value:
                raise HTTPException(status_code=403, detail="Ticket not assigned to your role")

        updates = ["updated_at = now()"]
        params: list[Any] = []
        param_idx = 1

        if body.status:
            updates.append(f"status = ${param_idx}")
            params.append(body.status)
            param_idx += 1
            if body.status in {"RESOLVED", "CLOSED"}:
                updates.append("resolved_at = now()")
        if body.assigned_to_role:
            updates.append(f"assigned_to_role = ${param_idx}")
            params.append(body.assigned_to_role)
            param_idx += 1
        if body.assigned_to_name:
            updates.append(f"assigned_to_name = ${param_idx}")
            params.append(body.assigned_to_name)
            param_idx += 1
        if not params:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(updates)
        params.append(ticket_id)
        query = f"UPDATE tickets SET {set_clause} WHERE ticket_id = ${param_idx}"
        await conn.execute(query, *params)
    return {"status": "updated", "ticket_id": ticket_id}
