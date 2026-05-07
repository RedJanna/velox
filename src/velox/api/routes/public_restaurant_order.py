"""Public QR-based restaurant ordering panel."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from velox.api.routes.public_restaurant_order_assets import (
    PUBLIC_RESTAURANT_ORDER_SCRIPT,
    PUBLIC_RESTAURANT_ORDER_STYLE,
)
from velox.core.restaurant_order_tokens import verify_table_order_token
from velox.core.restaurant_public_order_config import public_order_payload
from velox.core.restaurant_ai_menu import filter_catalog_items, load_default_menu_catalog
from velox.config.settings import settings
from velox.db.repositories.restaurant_ai import RestaurantAiRepository
from velox.models.restaurant_ai import RestaurantPublicOrderCreate
from velox.tools.notification import send_whatsapp_to_phone_with_result

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["public-restaurant-order"])
api_router = APIRouter(prefix="/api/v1/public/restaurant-order", tags=["public-restaurant-order-api"])

_ORDER_PAGE_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@router.get("/order", response_model=None)
async def public_order_page() -> HTMLResponse:
    """Render the public customer ordering panel."""
    return HTMLResponse(
        f"""\
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Kassandra Restaurant Sipariş</title>
  <style>{PUBLIC_RESTAURANT_ORDER_STYLE}</style>
</head>
<body>
  <main id="orderApp" class="order-shell" aria-live="polite"></main>
  <script>{PUBLIC_RESTAURANT_ORDER_SCRIPT}</script>
</body>
</html>""",
        headers=_ORDER_PAGE_CACHE_HEADERS,
    )


@api_router.get("/config")
async def public_order_config(token: str = Query(..., min_length=20)) -> dict[str, Any]:
    """Return customer-safe public ordering config for one signed table token."""
    table = verify_table_order_token(token)
    if table is None:
        raise HTTPException(status_code=404, detail="Sipariş bağlantısı geçersiz.")
    config = public_order_payload(table.hotel_id)
    if not config["enabled"]:
        raise HTTPException(status_code=503, detail="Sipariş ekranı geçici olarak kapalı.")

    repo = RestaurantAiRepository()
    catalog_rows = await _active_catalog_rows(repo=repo, hotel_id=table.hotel_id, venue=table.venue)
    return {
        "hotel_id": table.hotel_id,
        "venue": table.venue,
        "table_no": table.table_no,
        "service_modes": ["table_service", "room_service"],
        "catalog_items": [_customer_safe_catalog_item(row) for row in catalog_rows],
        **config,
    }


@api_router.post("/orders")
async def create_public_order(body: RestaurantPublicOrderCreate) -> dict[str, Any]:
    """Create a public customer order after the customer confirms twice."""
    table = verify_table_order_token(body.token)
    if table is None:
        raise HTTPException(status_code=404, detail="Sipariş bağlantısı geçersiz.")
    if body.service_type == "room_service" and not body.room_number:
        raise HTTPException(status_code=422, detail="Oda servisi için oda numarası gerekir.")

    config = public_order_payload(table.hotel_id)
    breakfast_items = list(config.get("breakfast_items") or [])
    repo = RestaurantAiRepository()
    catalog_rows = await _active_catalog_rows(repo=repo, hotel_id=table.hotel_id, venue=table.venue)
    _validate_public_order_items(body=body, catalog_rows=catalog_rows, breakfast_items=breakfast_items)

    try:
        order = await repo.create_public_order(
            hotel_id=table.hotel_id,
            venue=table.venue,
            table_no=table.table_no,
            body=body,
            catalog_items=catalog_rows,
            breakfast_items=breakfast_items,
            whatsapp_send_status="not_sent",
            waiter_delivery=[],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    recipients = await _order_notification_recipients(repo=repo, hotel_id=table.hotel_id, venue=table.venue)
    pending_message = _format_staff_pending_message(
        order_id=order["order_id"],
        venue=table.venue,
        table_no=table.table_no,
        body=body,
        catalog_rows=catalog_rows,
        breakfast_items=breakfast_items,
    )
    waiter_delivery = []
    for recipient in recipients:
        delivery = await send_whatsapp_to_phone_with_result(
            phone=recipient["whatsapp_number"],
            message=pending_message,
            hotel_id=table.hotel_id,
        )
        waiter_delivery.append(
            {
                "waiter_id": recipient["id"],
                "status": delivery["status"],
                "whatsapp_message_id": delivery.get("whatsapp_message_id"),
            }
        )

    whatsapp_status = _delivery_status(waiter_delivery)
    order = await repo.update_public_order_delivery(
        hotel_id=table.hotel_id,
        order_id=order["order_id"],
        whatsapp_send_status=whatsapp_status,
        waiter_delivery=waiter_delivery,
    ) or order
    logger.info(
        "public_restaurant_order_created",
        hotel_id=table.hotel_id,
        order_id=order["order_id"],
        service_type=body.service_type,
        meal_period=body.meal_period,
        recipient_count=len(recipients),
        whatsapp_send_status=whatsapp_status,
    )
    return {
        "status": "pending_staff_approval",
        "order_id": order["order_id"],
        "message": "Siparişiniz restorana iletildi, personel onayı bekleniyor.",
    }


async def _order_notification_recipients(
    *,
    repo: RestaurantAiRepository,
    hotel_id: int,
    venue: str,
) -> list[dict[str, str]]:
    recipients = await repo.list_order_notification_recipients(hotel_id, venue=venue)
    if recipients:
        return recipients
    fallback = await repo.list_order_notification_recipients(hotel_id, venue=None)
    if fallback:
        logger.warning(
            "public_restaurant_order_recipient_venue_fallback",
            hotel_id=hotel_id,
            venue=venue,
            recipient_count=len(fallback),
        )
    return fallback


def _customer_safe_catalog_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "menu_item_id": row["menu_item_id"],
        "venue": row["venue"],
        "menu_type": row["menu_type"],
        "category": row["category"],
        "name_tr": row["name_tr"],
        "name_en": row["name_en"],
        "price_try": str(row["price_try"]) if row["price_try"] is not None else None,
        "description_tr": row["description_tr"],
        "description_en": row["description_en"],
        "ingredients": row.get("ingredients") or [],
    }


async def _active_catalog_rows(
    *,
    repo: RestaurantAiRepository,
    hotel_id: int,
    venue: str,
) -> list[dict[str, Any]]:
    if await repo.count_catalog_items(hotel_id) > 0:
        return await repo.list_menu_catalog(hotel_id, venue=venue, status="active", limit=1200)
    payload = load_default_menu_catalog(hotel_id)
    if payload is None:
        return []
    return [item.model_dump(mode="json") for item in filter_catalog_items(payload.items, venue=venue, status="active")]


def _validate_public_order_items(
    *,
    body: RestaurantPublicOrderCreate,
    catalog_rows: list[dict[str, Any]],
    breakfast_items: list[dict[str, Any]],
) -> None:
    if body.meal_period == "breakfast":
        allowed = {str(item.get("menu_item_id")) for item in breakfast_items}
    else:
        allowed = {str(item.get("menu_item_id")) for item in catalog_rows}
    missing = [item.menu_item_id for item in body.items if item.menu_item_id not in allowed]
    if missing:
        raise HTTPException(status_code=422, detail="Seçilen ürünlerden biri aktif menüde görünmüyor.")


def _format_staff_pending_message(
    *,
    order_id: str,
    venue: str,
    table_no: str,
    body: RestaurantPublicOrderCreate,
    catalog_rows: list[dict[str, Any]],
    breakfast_items: list[dict[str, Any]],
) -> str:
    by_id = {str(item.get("menu_item_id")): item for item in [*catalog_rows, *breakfast_items]}
    lines = []
    for item in body.items:
        menu_item = by_id.get(item.menu_item_id, {})
        name = menu_item.get("name_tr") or menu_item.get("name_en") or item.menu_item_id
        lines.append(f"- {item.quantity}x {name}")
    place = f"Masa: {table_no}" if body.service_type == "table_service" else f"Oda: {body.room_number}"
    approval_url = f"{settings.admin_panel_url}#restaurantai"
    return (
        "[VELOX-L1] Restaurant order approval\n"
        f"Order: {order_id}\n"
        f"Venue: {venue}\n"
        f"{place}\n"
        f"Öğün: {body.meal_period}\n"
        "Sipariş:\n"
        + "\n".join(lines)
        + f"\nNot: {body.customer_note or '-'}\nAlerji: {body.allergy_note or '-'}\n"
        f"Onay: {approval_url}"
    )


def _delivery_status(delivery: list[dict[str, Any]]) -> str:
    if not delivery:
        return "not_sent"
    sent_count = sum(1 for item in delivery if item.get("status") == "sent")
    if sent_count == len(delivery):
        return "sent"
    return "partial" if sent_count else "failed"
