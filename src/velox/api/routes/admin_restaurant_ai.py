"""Admin API for Restaurant AI / Menu Assistant."""

from __future__ import annotations

from typing import Annotated, Any
from urllib.parse import quote
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from velox.api.middleware.auth import (
    TokenData,
    check_permission,
    ensure_hotel_access,
    get_current_user,
    resolve_hotel_scope,
)
from velox.core.restaurant_ai_menu import (
    build_price_conflicts,
    categories_for_catalog,
    filter_catalog_items,
    load_default_menu_catalog,
    menu_types_for_catalog,
    run_test_console,
    venues_for_catalog,
)
from velox.config.settings import settings
from velox.core.restaurant_order_tokens import create_table_order_token
from velox.db.repositories.restaurant_ai import RestaurantAiRepository
from velox.models.restaurant_ai import (
    RestaurantAiManualMenuItemCreate,
    RestaurantAiMenuItemContentUpdate,
    RestaurantAiMenuItemStatusUpdate,
    RestaurantAiMenuItem,
    RestaurantAiMessageSettingsUpdate,
    RestaurantAiOrderStatusUpdate,
    RestaurantAiTableLinkRequest,
    RestaurantAiTestConsoleRequest,
    RestaurantAiWaiterCreate,
    RestaurantAiWaiterUpdate,
    RestaurantOffMenuRequestCreate,
)

router = APIRouter(prefix="/admin/restaurant-ai", tags=["admin-restaurant-ai"])


def _effective_hotel(user: TokenData, hotel_id: int | None) -> int:
    return resolve_hotel_scope(user, hotel_id)


def _username(user: TokenData) -> str:
    return (user.username or "system").strip() or "system"


async def _catalog_items_for_hotel(
    repo: RestaurantAiRepository,
    hotel_id: int,
) -> tuple[str, list[RestaurantAiMenuItem]]:
    if await repo.count_catalog_items(hotel_id) > 0:
        return "database", await repo.list_active_menu_items(hotel_id)
    payload = load_default_menu_catalog(hotel_id)
    if payload is None:
        return "missing", []
    return "menu_catalog.json", payload.items


@router.get("/catalog")
async def list_catalog(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    search: str | None = Query(None),
    category: str | None = Query(None),
    venue: str | None = Query(None),
    menu_type: str | None = Query(None),
    status: str | None = Query(None),
) -> dict[str, Any]:
    """List Restaurant AI menu catalog rows for the panel."""
    check_permission(user, "restaurant_ai:read")
    effective = _effective_hotel(user, hotel_id)
    repo = RestaurantAiRepository()
    db_count = await repo.count_catalog_items(effective)
    latest_version = await repo.latest_catalog_version(effective)

    if db_count > 0:
        rows = await repo.list_menu_catalog(
            effective,
            search=search,
            category=category,
            venue=venue,
            menu_type=menu_type,
            status=status,
        )
        all_active = await repo.list_active_menu_items(effective)
        return {
            "source": "database",
            "items": rows,
            "total": len(rows),
            "catalog_item_count": db_count,
            "categories": categories_for_catalog(all_active),
            "venues": venues_for_catalog(all_active),
            "menu_types": menu_types_for_catalog(all_active),
            "latest_version": latest_version,
            "safe_save_mode": "versioned_database",
        }

    payload = load_default_menu_catalog(effective)
    if payload is None:
        return {
            "source": "missing",
            "items": [],
            "total": 0,
            "catalog_item_count": 0,
            "categories": [],
            "venues": [],
            "menu_types": [],
            "latest_version": latest_version,
            "safe_save_mode": "read_only_missing_json",
        }
    items = filter_catalog_items(
        payload.items,
        search=search,
        category=category,
        venue=venue,
        menu_type=menu_type,
        status=status,
    )
    return {
        "source": "menu_catalog.json",
        "source_path": str(payload.source_path),
        "items": [item.model_dump(mode="json") for item in items],
        "total": len(items),
        "catalog_item_count": 0,
        "categories": categories_for_catalog(payload.items),
        "venues": venues_for_catalog(payload.items),
        "menu_types": menu_types_for_catalog(payload.items),
        "latest_version": latest_version,
        "safe_save_mode": "read_only_json_until_import",
    }


@router.post("/catalog/import-default")
async def import_default_catalog(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    """Import menu_catalog.json into versioned DB rows."""
    check_permission(user, "restaurant_ai:write")
    effective = ensure_hotel_access(user, hotel_id)
    payload = load_default_menu_catalog(effective)
    if payload is None:
        raise HTTPException(status_code=404, detail="menu_catalog.json bulunamadı.")
    repo = RestaurantAiRepository()
    result = await repo.import_catalog(
        hotel_id=effective,
        items=payload.items,
        source_label=payload.source_label,
        checksum=payload.checksum,
        actor_username=_username(user),
        notes="Panel import-default işlemi",
    )
    return {"status": "imported", **result}


@router.get("/catalog/conflicts")
async def list_catalog_conflicts(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
) -> dict[str, Any]:
    """Show price conflicts grouped by venue + menu_type."""
    check_permission(user, "restaurant_ai:read")
    effective = _effective_hotel(user, hotel_id)
    repo = RestaurantAiRepository()
    source, items = await _catalog_items_for_hotel(repo, effective)
    conflicts = build_price_conflicts(items)
    return {"source": source, "items": conflicts, "total": len(conflicts)}


@router.post("/catalog/manual-items")
async def create_manual_catalog_item(
    body: RestaurantAiManualMenuItemCreate,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create an approval-required manual menu item proposal."""
    check_permission(user, "restaurant_ai:write")
    ensure_hotel_access(user, body.hotel_id)
    repo = RestaurantAiRepository()
    try:
        item = await repo.create_manual_menu_item(body=body, actor_username=_username(user))
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(status_code=409, detail="Bu manuel ürün kaydı zaten mevcut.") from exc
    return {"status": "approval_required", "item": item}


@router.patch("/catalog/items/{menu_item_id}/status")
async def update_catalog_item_status(
    menu_item_id: str,
    body: RestaurantAiMenuItemStatusUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    """Update one catalog item active/passive state from the panel."""
    check_permission(user, "restaurant_ai:write")
    effective = ensure_hotel_access(user, hotel_id)
    item = await RestaurantAiRepository().update_menu_item_status(
        hotel_id=effective,
        menu_item_id=menu_item_id,
        body=body,
        actor_username=_username(user),
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Menü ürünü bulunamadı.")
    return {"status": "updated", "item": item}


@router.patch("/catalog/items/{menu_item_id}/content")
async def update_catalog_item_content(
    menu_item_id: str,
    body: RestaurantAiMenuItemContentUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    """Update customer-facing ingredients/description for one catalog item."""
    check_permission(user, "restaurant_ai:write")
    effective = ensure_hotel_access(user, hotel_id)
    item = await RestaurantAiRepository().update_menu_item_content(
        hotel_id=effective,
        menu_item_id=menu_item_id,
        body=body,
        actor_username=_username(user),
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Menü ürünü bulunamadı.")
    return {"status": "updated", "item": item}


@router.get("/waiters")
async def list_waiters(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
) -> dict[str, Any]:
    """List waiter WhatsApp routing numbers with masked phone display."""
    check_permission(user, "restaurant_ai:read")
    effective = _effective_hotel(user, hotel_id)
    items = await RestaurantAiRepository().list_waiters(effective)
    return {"items": items, "total": len(items)}


@router.post("/waiters")
async def create_waiter(
    body: RestaurantAiWaiterCreate,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a waiter WhatsApp routing number."""
    check_permission(user, "restaurant_ai:write")
    ensure_hotel_access(user, body.hotel_id)
    try:
        item = await RestaurantAiRepository().create_waiter(body=body, actor_username=_username(user))
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(status_code=409, detail="Bu venue için aynı WhatsApp numarası zaten kayıtlı.") from exc
    return {"status": "created", "item": item}


@router.patch("/waiters/{waiter_id}")
async def update_waiter(
    waiter_id: UUID,
    body: RestaurantAiWaiterUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    """Update waiter routing state."""
    check_permission(user, "restaurant_ai:write")
    effective = ensure_hotel_access(user, hotel_id)
    item = await RestaurantAiRepository().update_waiter(
        hotel_id=effective,
        waiter_id=waiter_id,
        body=body,
        actor_username=_username(user),
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Garson kaydı bulunamadı veya güncellenecek alan yok.")
    return {"status": "updated", "item": item}


@router.get("/orders")
async def list_orders(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status: str | None = Query(None),
) -> dict[str, Any]:
    """List Restaurant AI order logs."""
    check_permission(user, "restaurant_ai:read")
    effective = _effective_hotel(user, hotel_id)
    items = await RestaurantAiRepository().list_orders(effective, status=status)
    return {"items": items, "total": len(items)}


@router.patch("/orders/{order_id}")
async def update_order_status(
    order_id: str,
    body: RestaurantAiOrderStatusUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    """Update order status fields from the panel."""
    check_permission(user, "restaurant_ai:write")
    effective = ensure_hotel_access(user, hotel_id)
    item = await RestaurantAiRepository().update_order_status(
        hotel_id=effective,
        order_id=order_id,
        body=body,
        actor_username=_username(user),
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Sipariş kaydı bulunamadı veya güncellenecek alan yok.")
    return {"status": "updated", "item": item}


@router.post("/table-order-link")
async def create_table_order_link(
    body: RestaurantAiTableLinkRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, str]:
    """Create one signed public /order link for a restaurant table QR."""
    check_permission(user, "restaurant_ai:write")
    ensure_hotel_access(user, body.hotel_id)
    token = create_table_order_token(
        hotel_id=body.hotel_id,
        venue=body.venue,
        table_no=body.table_no,
    )
    order_url = f"{settings.public_base_url.rstrip('/')}/order?t={quote(token)}"
    return {"token": token, "order_url": order_url}


@router.get("/off-menu-requests")
async def list_off_menu_requests(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
) -> dict[str, Any]:
    """List logged off-menu customer requests."""
    check_permission(user, "restaurant_ai:read")
    effective = _effective_hotel(user, hotel_id)
    items = await RestaurantAiRepository().list_off_menu_requests(effective)
    return {"items": items, "total": len(items), "auto_added_to_catalog": False}


@router.post("/off-menu-requests")
async def create_off_menu_request(
    body: RestaurantOffMenuRequestCreate,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create an off-menu request log without adding it to the assistant catalog."""
    check_permission(user, "restaurant_ai:write")
    ensure_hotel_access(user, body.hotel_id)
    item = await RestaurantAiRepository().create_off_menu_request(body=body)
    return {"status": "logged", "item": item, "auto_added_to_catalog": False}


@router.post("/test-console")
async def run_restaurant_ai_test_console(
    body: RestaurantAiTestConsoleRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Run deterministic menu-bound validation for one sample customer question."""
    check_permission(user, "restaurant_ai:read")
    ensure_hotel_access(user, body.hotel_id)
    repo = RestaurantAiRepository()
    source, items = await _catalog_items_for_hotel(repo, body.hotel_id)
    settings = await repo.get_settings(body.hotel_id)
    result = run_test_console(
        question=body.question,
        catalog_items=items,
        settings=settings,
        venue=body.venue,
        menu_type=body.menu_type,
    )
    return {"source": source, **result}


@router.get("/settings")
async def get_message_settings(
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
) -> dict[str, Any]:
    """Return Restaurant AI message settings."""
    check_permission(user, "restaurant_ai:read")
    effective = _effective_hotel(user, hotel_id)
    settings = await RestaurantAiRepository().get_settings(effective)
    settings["menu_out_of_scope_guard_enabled"] = True
    return {"settings": settings}


@router.put("/settings")
async def update_message_settings(
    body: RestaurantAiMessageSettingsUpdate,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    """Update editable Restaurant AI message templates; guard remains always on."""
    check_permission(user, "restaurant_ai:write")
    effective = ensure_hotel_access(user, hotel_id)
    settings = await RestaurantAiRepository().update_settings(
        hotel_id=effective,
        body=body,
        actor_username=_username(user),
    )
    settings["menu_out_of_scope_guard_enabled"] = True
    return {"status": "updated", "settings": settings}
