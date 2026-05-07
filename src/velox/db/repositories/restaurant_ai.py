"""Repository for Restaurant AI menu assistant admin data."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import orjson

from velox.core.restaurant_ai_menu import (
    DEFAULT_ALLERGY_WARNING_TEXT,
    DEFAULT_OFF_MENU_RESPONSE,
    DEFAULT_ORDER_CONFIRMATION_MESSAGE,
    DEFAULT_WHATSAPP_NOTIFICATION_TEMPLATE,
    normalize_text,
)
from velox.db.database import get_pool
from velox.models.restaurant_ai import (
    RestaurantAiManualMenuItemCreate,
    RestaurantAiMenuItem,
    RestaurantAiMenuItemStatusUpdate,
    RestaurantAiMessageSettingsUpdate,
    RestaurantAiOrderStatusUpdate,
    RestaurantAiWaiterCreate,
    RestaurantAiWaiterUpdate,
    RestaurantPublicOrderCreate,
    RestaurantPublicOrderItem,
    RestaurantOffMenuRequestCreate,
)
from velox.utils.json import decode_json_value

DB_TIMEOUT_SECONDS = 5


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    raise TypeError


def _json_dumps(value: object) -> str:
    return orjson.dumps(value, default=_json_default).decode("utf-8")


def _json_list(raw: object) -> list[Any]:
    decoded = decode_json_value(raw)
    return decoded if isinstance(decoded, list) else []


def _json_object(raw: object) -> dict[str, Any]:
    decoded = decode_json_value(raw)
    return decoded if isinstance(decoded, dict) else {}


def _mask_phone(value: str | None) -> str:
    phone = (value or "").strip()
    if not phone:
        return ""
    if len(phone) <= 6:
        return "***"
    return f"{phone[:3]}***{phone[-2:]}"


def _menu_item_id_from_manual(body: RestaurantAiManualMenuItemCreate) -> str:
    slug = normalize_text("_".join([body.venue, body.menu_type, body.category, body.name_en]))
    slug = "".join(char if char.isalnum() else "_" for char in slug)
    slug = "_".join(part for part in slug.split("_") if part)
    return f"manual_{slug[:120]}_{uuid4().hex[:8]}"


def _row_to_menu_item(row: asyncpg.Record) -> dict[str, Any]:
    data = dict(row)
    return {
        "id": str(data["id"]),
        "hotel_id": data["hotel_id"],
        "menu_item_id": data["menu_item_id"],
        "venue": data["venue"],
        "menu_type": data["menu_type"],
        "category": data["category"],
        "name_tr": data["name_tr"],
        "name_en": data["name_en"],
        "price_try": data["price_try"],
        "description_tr": data["description_tr"],
        "description_en": data["description_en"],
        "tags": _json_list(data["tags_json"]),
        "dietary_tags": _json_list(data["dietary_tags_json"]),
        "allergen_tags": _json_list(data["allergen_tags_json"]),
        "ingredients": _json_list(data["ingredients_json"]),
        "source_pdf": data["source_pdf"],
        "source_page": data["source_page"],
        "status": data["status"],
        "manual_status": data["manual_status"],
        "notes": data["notes"],
        "catalog_version": data["catalog_version"],
        "created_by": data["created_by"],
        "updated_by": data["updated_by"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
    }


def _row_to_waiter(row: asyncpg.Record) -> dict[str, Any]:
    data = dict(row)
    return {
        "id": str(data["id"]),
        "hotel_id": data["hotel_id"],
        "waiter_name": data["waiter_name"],
        "whatsapp_display": _mask_phone(data["whatsapp_number"]),
        "role": data["role"],
        "venue": data["venue"],
        "active": data["active"],
        "receives_order_notifications": data["receives_order_notifications"],
        "created_by": data["created_by"],
        "updated_by": data["updated_by"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
    }


def _row_to_order(row: asyncpg.Record) -> dict[str, Any]:
    data = dict(row)
    return {
        "id": str(data["id"]),
        "order_id": data["order_id"],
        "hotel_id": data["hotel_id"],
        "venue": data["venue"],
        "menu_type": data["menu_type"],
        "service_type": data.get("service_type"),
        "meal_period": data.get("meal_period"),
        "language_code": data.get("language_code"),
        "table_no": data.get("table_no"),
        "table_or_room": data["table_or_room"],
        "guest_name": None,
        "items": _json_list(data["items_json"]),
        "total_try": data["total_try"],
        "customer_note": data["customer_note"],
        "allergy_note": data["allergy_note"],
        "confirmation_status": data["confirmation_status"],
        "whatsapp_send_status": data["whatsapp_send_status"],
        "customer_confirmation_count": data.get("customer_confirmation_count") or 0,
        "customer_confirmed_at": data.get("customer_confirmed_at"),
        "staff_decision_by": data.get("staff_decision_by"),
        "staff_decision_at": data.get("staff_decision_at"),
        "selected_waiter_ids": [str(item) for item in data["selected_waiter_ids"]],
        "waiter_delivery": _json_list(data["waiter_delivery_json"]),
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
    }


def _row_to_off_menu(row: asyncpg.Record) -> dict[str, Any]:
    data = dict(row)
    return {
        "id": str(data["id"]),
        "hotel_id": data["hotel_id"],
        "requested_text": data["requested_text"],
        "normalized_request": data["normalized_request"],
        "detected_intent": data["detected_intent"],
        "venue": data["venue"],
        "guest_context": _json_object(data["guest_context_json"]),
        "added_to_catalog": data["added_to_catalog"],
        "created_at": data["created_at"],
    }


def _materialize_public_order_items(
    requested_items: list[RestaurantPublicOrderItem],
    *,
    catalog_items: list[dict[str, Any]],
    breakfast_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], Decimal | None]:
    by_id = {str(item.get("menu_item_id")): item for item in [*catalog_items, *breakfast_items]}
    materialized: list[dict[str, Any]] = []
    total = Decimal("0")
    has_price = False
    for requested in requested_items:
        item = by_id.get(requested.menu_item_id)
        if item is None:
            raise ValueError("Seçilen ürün artık menüde aktif görünmüyor.")
        price = item.get("price_try")
        line_total: Decimal | None = None
        if price is not None:
            price_decimal = Decimal(str(price))
            line_total = price_decimal * requested.quantity
            total += line_total
            has_price = True
        materialized.append(
            {
                "menu_item_id": requested.menu_item_id,
                "name_tr": item.get("name_tr"),
                "name_en": item.get("name_en"),
                "quantity": requested.quantity,
                "unit_price_try": str(price) if price is not None else None,
                "line_total_try": str(line_total) if line_total is not None else None,
                "note": requested.note,
            }
        )
    return materialized, total if has_price else None


class RestaurantAiRepository:
    """CRUD operations for Restaurant AI admin panel data."""

    async def count_catalog_items(self, hotel_id: int) -> int:
        pool = get_pool()
        value = await pool.fetchval(
            "SELECT COUNT(*) FROM restaurant_menu_catalog_items WHERE hotel_id = $1",
            hotel_id,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return int(value or 0)

    async def list_menu_catalog(
        self,
        hotel_id: int,
        *,
        search: str | None = None,
        category: str | None = None,
        venue: str | None = None,
        menu_type: str | None = None,
        status: str | None = None,
        limit: int = 700,
    ) -> list[dict[str, Any]]:
        pool = get_pool()
        rows = await pool.fetch(
            """
            SELECT *
            FROM restaurant_menu_catalog_items
            WHERE hotel_id = $1
              AND (
                    $2::text IS NULL
                    OR name_en ILIKE $2
                    OR COALESCE(name_tr, '') ILIKE $2
                    OR category ILIKE $2
                    OR venue ILIKE $2
                    OR menu_type ILIKE $2
              )
              AND ($3::text IS NULL OR category = $3)
              AND ($4::text IS NULL OR venue = $4)
              AND ($5::text IS NULL OR menu_type = $5)
              AND ($6::text IS NULL OR status = $6)
            ORDER BY venue, menu_type, category, name_en
            LIMIT $7
            """,
            hotel_id,
            f"%{search.strip()}%" if search else None,
            category.strip() if category else None,
            venue.strip() if venue else None,
            menu_type.strip() if menu_type else None,
            status.strip() if status else None,
            limit,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return [_row_to_menu_item(row) for row in rows]

    async def list_active_menu_items(self, hotel_id: int) -> list[RestaurantAiMenuItem]:
        rows = await self.list_menu_catalog(hotel_id, status="active", limit=1200)
        return [
            RestaurantAiMenuItem.model_validate(
                {
                    "menu_item_id": row["menu_item_id"],
                    "venue": row["venue"],
                    "menu_type": row["menu_type"],
                    "category": row["category"],
                    "name_tr": row["name_tr"],
                    "name_en": row["name_en"],
                    "price_try": row["price_try"],
                    "description_tr": row["description_tr"],
                    "description_en": row["description_en"],
                    "tags": row["tags"],
                    "dietary_tags": row["dietary_tags"],
                    "allergen_tags": row["allergen_tags"],
                    "ingredients": row["ingredients"],
                    "source_pdf": row["source_pdf"],
                    "source_page": row["source_page"],
                    "status": row["status"],
                    "manual_status": row["manual_status"],
                    "notes": row["notes"],
                }
            )
            for row in rows
        ]

    async def import_catalog(
        self,
        *,
        hotel_id: int,
        items: Sequence[RestaurantAiMenuItem],
        source_label: str,
        checksum: str,
        actor_username: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            next_version = await conn.fetchval(
                """
                SELECT COALESCE(MAX(version), 0) + 1
                FROM restaurant_menu_catalog_versions
                WHERE hotel_id = $1
                """,
                hotel_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            version = int(next_version or 1)
            await conn.execute(
                """
                INSERT INTO restaurant_menu_catalog_versions
                    (hotel_id, version, source_label, checksum, item_count, imported_by, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                hotel_id,
                version,
                source_label,
                checksum,
                len(items),
                actor_username,
                notes,
                timeout=DB_TIMEOUT_SECONDS,
            )
            for item in items:
                raw_json = item.raw_json or item.model_dump(mode="json")
                await conn.execute(
                    """
                    INSERT INTO restaurant_menu_catalog_items (
                        hotel_id, menu_item_id, venue, menu_type, category, name_tr, name_en, price_try,
                        description_tr, description_en, tags_json, dietary_tags_json, allergen_tags_json,
                        ingredients_json, source_pdf, source_page, status, manual_status, notes, raw_json,
                        catalog_version, created_by, updated_by, updated_at
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8,
                        $9, $10, $11::jsonb, $12::jsonb, $13::jsonb,
                        $14::jsonb, $15, $16, $17, $18, $19, $20::jsonb,
                        $21, $22, $22, now()
                    )
                    ON CONFLICT (hotel_id, menu_item_id)
                    DO UPDATE SET
                        venue = EXCLUDED.venue,
                        menu_type = EXCLUDED.menu_type,
                        category = EXCLUDED.category,
                        name_tr = EXCLUDED.name_tr,
                        name_en = EXCLUDED.name_en,
                        price_try = EXCLUDED.price_try,
                        description_tr = EXCLUDED.description_tr,
                        description_en = EXCLUDED.description_en,
                        tags_json = EXCLUDED.tags_json,
                        dietary_tags_json = EXCLUDED.dietary_tags_json,
                        allergen_tags_json = EXCLUDED.allergen_tags_json,
                        ingredients_json = EXCLUDED.ingredients_json,
                        source_pdf = EXCLUDED.source_pdf,
                        source_page = EXCLUDED.source_page,
                        status = EXCLUDED.status,
                        manual_status = 'catalog_verified',
                        notes = EXCLUDED.notes,
                        raw_json = EXCLUDED.raw_json,
                        catalog_version = EXCLUDED.catalog_version,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = now()
                    """,
                    hotel_id,
                    item.menu_item_id,
                    item.venue,
                    item.menu_type,
                    item.category,
                    item.name_tr,
                    item.name_en,
                    item.price_try,
                    item.description_tr,
                    item.description_en,
                    _json_dumps(item.tags),
                    _json_dumps(item.dietary_tags),
                    _json_dumps(item.allergen_tags),
                    _json_dumps(item.ingredients),
                    item.source_pdf,
                    item.source_page,
                    item.status,
                    item.manual_status,
                    item.notes,
                    _json_dumps(raw_json),
                    version,
                    actor_username,
                    timeout=DB_TIMEOUT_SECONDS,
                )
            await self._log_audit(
                conn,
                hotel_id=hotel_id,
                event_type="catalog_imported",
                reference_type="catalog_version",
                reference_id=str(version),
                actor_username=actor_username,
                payload={"source_label": source_label, "checksum": checksum, "item_count": len(items)},
            )
        return {"version": version, "item_count": len(items), "checksum": checksum}

    async def create_manual_menu_item(
        self,
        *,
        body: RestaurantAiManualMenuItemCreate,
        actor_username: str,
    ) -> dict[str, Any]:
        pool = get_pool()
        menu_item_id = _menu_item_id_from_manual(body)
        raw_json = body.model_dump(mode="json")
        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO restaurant_menu_catalog_items (
                    hotel_id, menu_item_id, venue, menu_type, category, name_tr, name_en, price_try,
                    description_tr, description_en, tags_json, dietary_tags_json, allergen_tags_json,
                    ingredients_json, status, manual_status, notes, raw_json, created_by, updated_by
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11::jsonb, '[]'::jsonb, '[]'::jsonb,
                    '[]'::jsonb, 'pending_approval', 'approval_required', $12, $13::jsonb, $14, $14
                )
                RETURNING *
                """,
                body.hotel_id,
                menu_item_id,
                body.venue,
                body.menu_type,
                body.category,
                body.name_tr,
                body.name_en,
                body.price_try,
                body.description_tr,
                body.description_en,
                _json_dumps(body.tags),
                body.notes,
                _json_dumps(raw_json),
                actor_username,
                timeout=DB_TIMEOUT_SECONDS,
            )
            await self._log_audit(
                conn,
                hotel_id=body.hotel_id,
                event_type="manual_item_requested",
                reference_type="menu_item",
                reference_id=menu_item_id,
                actor_username=actor_username,
                payload={"manual_status": "approval_required", "name_en": body.name_en},
            )
        if row is None:
            raise RuntimeError("manual_menu_item_create_failed")
        return _row_to_menu_item(row)

    async def update_menu_item_status(
        self,
        *,
        hotel_id: int,
        menu_item_id: str,
        body: RestaurantAiMenuItemStatusUpdate,
        actor_username: str,
    ) -> dict[str, Any] | None:
        """Update one catalog item status without changing catalog content."""
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE restaurant_menu_catalog_items
                SET status = $1,
                    updated_by = $2,
                    updated_at = now()
                WHERE hotel_id = $3 AND menu_item_id = $4
                RETURNING *
                """,
                body.status,
                actor_username,
                hotel_id,
                menu_item_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if row is None:
                return None
            await self._log_audit(
                conn,
                hotel_id=hotel_id,
                event_type="catalog_item_status_updated",
                reference_type="menu_item",
                reference_id=menu_item_id,
                actor_username=actor_username,
                payload={"status": body.status},
            )
        return _row_to_menu_item(row)

    async def list_waiters(self, hotel_id: int) -> list[dict[str, Any]]:
        pool = get_pool()
        rows = await pool.fetch(
            """
            SELECT *
            FROM restaurant_waiter_numbers
            WHERE hotel_id = $1
            ORDER BY active DESC, receives_order_notifications DESC, waiter_name
            """,
            hotel_id,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return [_row_to_waiter(row) for row in rows]

    async def list_order_notification_recipients(
        self,
        hotel_id: int,
        *,
        venue: str | None = None,
    ) -> list[dict[str, str]]:
        """Return raw waiter phones for internal delivery only."""
        rows = await get_pool().fetch(
            """
            SELECT id, waiter_name, whatsapp_number, role, venue
            FROM restaurant_waiter_numbers
            WHERE hotel_id = $1
              AND active = TRUE
              AND receives_order_notifications = TRUE
              AND ($2::text IS NULL OR venue IS NULL OR venue = $2)
            ORDER BY venue NULLS LAST, waiter_name
            """,
            hotel_id,
            venue,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return [
            {
                "id": str(row["id"]),
                "waiter_name": row["waiter_name"],
                "whatsapp_number": row["whatsapp_number"],
                "role": row["role"] or "",
                "venue": row["venue"] or "",
            }
            for row in rows
        ]

    async def create_waiter(self, *, body: RestaurantAiWaiterCreate, actor_username: str) -> dict[str, Any]:
        pool = get_pool()
        row = await pool.fetchrow(
            """
            INSERT INTO restaurant_waiter_numbers (
                hotel_id, waiter_name, whatsapp_number, role, venue, active,
                receives_order_notifications, created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
            RETURNING *
            """,
            body.hotel_id,
            body.waiter_name,
            body.whatsapp_number,
            body.role,
            body.venue,
            body.active,
            body.receives_order_notifications,
            actor_username,
            timeout=DB_TIMEOUT_SECONDS,
        )
        if row is None:
            raise RuntimeError("waiter_create_failed")
        return _row_to_waiter(row)

    async def update_waiter(
        self,
        *,
        hotel_id: int,
        waiter_id: UUID,
        body: RestaurantAiWaiterUpdate,
        actor_username: str,
    ) -> dict[str, Any] | None:
        update_fields = body.model_dump(exclude_none=True)
        if not update_fields:
            return None
        row = await get_pool().fetchrow(
            """
            UPDATE restaurant_waiter_numbers
            SET waiter_name = COALESCE($1::varchar, waiter_name),
                whatsapp_number = COALESCE($2::varchar, whatsapp_number),
                role = COALESCE($3::varchar, role),
                venue = COALESCE($4::varchar, venue),
                active = COALESCE($5::boolean, active),
                receives_order_notifications = COALESCE($6::boolean, receives_order_notifications),
                updated_by = $7,
                updated_at = now()
            WHERE hotel_id = $8 AND id = $9
            RETURNING *
            """,
            update_fields.get("waiter_name"),
            update_fields.get("whatsapp_number"),
            update_fields.get("role"),
            update_fields.get("venue"),
            update_fields.get("active"),
            update_fields.get("receives_order_notifications"),
            actor_username,
            hotel_id,
            waiter_id,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return _row_to_waiter(row) if row is not None else None

    async def list_orders(
        self,
        hotel_id: int,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        pool = get_pool()
        rows = await pool.fetch(
            """
            SELECT *
            FROM restaurant_ai_order_logs
            WHERE hotel_id = $1
              AND ($2::text IS NULL OR confirmation_status = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            hotel_id,
            status,
            limit,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return [_row_to_order(row) for row in rows]

    async def update_order_status(
        self,
        *,
        hotel_id: int,
        order_id: str,
        body: RestaurantAiOrderStatusUpdate,
        actor_username: str | None = None,
    ) -> dict[str, Any] | None:
        update_fields = body.model_dump(exclude_none=True)
        if not update_fields:
            return None
        status = update_fields.get("confirmation_status")
        actor = actor_username if status in {"accepted_by_staff", "rejected_by_staff", "preparing", "completed"} else None
        row = await get_pool().fetchrow(
            """
            UPDATE restaurant_ai_order_logs
            SET confirmation_status = COALESCE($1::varchar, confirmation_status),
                whatsapp_send_status = COALESCE($2::varchar, whatsapp_send_status),
                staff_decision_by = COALESCE($5::varchar, staff_decision_by),
                staff_decision_at = CASE WHEN $5::varchar IS NULL THEN staff_decision_at ELSE now() END,
                updated_at = now()
            WHERE hotel_id = $3 AND order_id = $4
            RETURNING *
            """,
            update_fields.get("confirmation_status"),
            update_fields.get("whatsapp_send_status"),
            hotel_id,
            order_id,
            actor,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return _row_to_order(row) if row is not None else None

    async def create_public_order(
        self,
        *,
        hotel_id: int,
        venue: str,
        table_no: str | None,
        body: RestaurantPublicOrderCreate,
        catalog_items: list[dict[str, Any]],
        breakfast_items: list[dict[str, Any]],
        whatsapp_send_status: str,
        waiter_delivery: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create a public order after the customer confirms it twice."""
        order_id = await self._next_public_order_id(hotel_id)
        items, total_try = _materialize_public_order_items(
            body.items,
            catalog_items=catalog_items,
            breakfast_items=breakfast_items,
        )
        service_label = f"Masa {table_no}" if body.service_type == "table_service" else "Oda servisi"
        row = await get_pool().fetchrow(
            """
            INSERT INTO restaurant_ai_order_logs (
                order_id, hotel_id, venue, menu_type, table_or_room, guest_name,
                items_json, total_try, customer_note, allergy_note,
                confirmation_status, whatsapp_send_status, selected_waiter_ids, waiter_delivery_json,
                service_type, meal_period, language_code, table_no,
                customer_confirmation_count, customer_confirmed_at
            )
            VALUES (
                $1, $2, $3, $4, $5, NULL,
                $6::jsonb, $7, $8, $9,
                'pending_staff_approval', $10, $11::uuid[], $12::jsonb,
                $13, $14, $15, $16,
                2, now()
            )
            RETURNING *
            """,
            order_id,
            hotel_id,
            venue,
            body.meal_period,
            service_label,
            _json_dumps(items),
            total_try,
            body.customer_note,
            body.allergy_note,
            whatsapp_send_status,
            [UUID(str(item["waiter_id"])) for item in waiter_delivery if item.get("waiter_id")],
            _json_dumps(waiter_delivery),
            body.service_type,
            body.meal_period,
            body.language_code,
            table_no if body.service_type == "table_service" else None,
            timeout=DB_TIMEOUT_SECONDS,
        )
        if row is None:
            raise RuntimeError("public_restaurant_order_create_failed")
        await self._log_public_order_event(
            hotel_id=hotel_id,
            order_id=order_id,
            event_type="public_order_created",
            payload={
                "service_type": body.service_type,
                "meal_period": body.meal_period,
                "customer_confirmation_count": 2,
                "item_count": len(items),
                "whatsapp_send_status": whatsapp_send_status,
            },
        )
        return _row_to_order(row)

    async def _next_public_order_id(self, hotel_id: int) -> str:
        """Return a compact public order id without PII."""
        return f"RO-{hotel_id}-{uuid4().hex[:8].upper()}"

    async def _log_public_order_event(
        self,
        *,
        hotel_id: int,
        order_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        await get_pool().execute(
            """
            INSERT INTO restaurant_public_order_audit_logs (hotel_id, order_id, event_type, payload_json)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            hotel_id,
            order_id,
            event_type,
            _json_dumps(payload),
            timeout=DB_TIMEOUT_SECONDS,
        )

    async def list_off_menu_requests(self, hotel_id: int, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = await get_pool().fetch(
            """
            SELECT *
            FROM restaurant_off_menu_request_logs
            WHERE hotel_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            hotel_id,
            limit,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return [_row_to_off_menu(row) for row in rows]

    async def create_off_menu_request(
        self,
        *,
        body: RestaurantOffMenuRequestCreate,
    ) -> dict[str, Any]:
        normalized = normalize_text(body.requested_text)
        row = await get_pool().fetchrow(
            """
            INSERT INTO restaurant_off_menu_request_logs (
                hotel_id, requested_text, normalized_request, detected_intent, venue, guest_context_json
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING *
            """,
            body.hotel_id,
            body.requested_text,
            normalized,
            body.detected_intent,
            body.venue,
            _json_dumps(body.guest_context),
            timeout=DB_TIMEOUT_SECONDS,
        )
        if row is None:
            raise RuntimeError("off_menu_request_create_failed")
        return _row_to_off_menu(row)

    async def get_settings(self, hotel_id: int) -> dict[str, Any]:
        pool = get_pool()
        await pool.execute(
            """
            INSERT INTO restaurant_ai_message_settings (
                hotel_id, off_menu_response, order_confirmation_message,
                whatsapp_notification_template, allergy_warning_text
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (hotel_id) DO NOTHING
            """,
            hotel_id,
            DEFAULT_OFF_MENU_RESPONSE,
            DEFAULT_ORDER_CONFIRMATION_MESSAGE,
            DEFAULT_WHATSAPP_NOTIFICATION_TEMPLATE,
            DEFAULT_ALLERGY_WARNING_TEXT,
            timeout=DB_TIMEOUT_SECONDS,
        )
        row = await pool.fetchrow(
            "SELECT * FROM restaurant_ai_message_settings WHERE hotel_id = $1",
            hotel_id,
            timeout=DB_TIMEOUT_SECONDS,
        )
        if row is None:
            raise RuntimeError("restaurant_ai_settings_missing")
        return dict(row)

    async def update_settings(
        self,
        *,
        hotel_id: int,
        body: RestaurantAiMessageSettingsUpdate,
        actor_username: str,
    ) -> dict[str, Any]:
        row = await get_pool().fetchrow(
            """
            INSERT INTO restaurant_ai_message_settings (
                hotel_id, off_menu_response, order_confirmation_message,
                whatsapp_notification_template, allergy_warning_text, updated_by, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, now())
            ON CONFLICT (hotel_id)
            DO UPDATE SET
                off_menu_response = EXCLUDED.off_menu_response,
                order_confirmation_message = EXCLUDED.order_confirmation_message,
                whatsapp_notification_template = EXCLUDED.whatsapp_notification_template,
                allergy_warning_text = EXCLUDED.allergy_warning_text,
                menu_out_of_scope_guard_enabled = true,
                updated_by = EXCLUDED.updated_by,
                updated_at = now()
            RETURNING *
            """,
            hotel_id,
            body.off_menu_response,
            body.order_confirmation_message,
            body.whatsapp_notification_template,
            body.allergy_warning_text,
            actor_username,
            timeout=DB_TIMEOUT_SECONDS,
        )
        if row is None:
            raise RuntimeError("restaurant_ai_settings_update_failed")
        return dict(row)

    async def latest_catalog_version(self, hotel_id: int) -> dict[str, Any] | None:
        row = await get_pool().fetchrow(
            """
            SELECT *
            FROM restaurant_menu_catalog_versions
            WHERE hotel_id = $1
            ORDER BY version DESC
            LIMIT 1
            """,
            hotel_id,
            timeout=DB_TIMEOUT_SECONDS,
        )
        return dict(row) if row is not None else None

    async def _log_audit(
        self,
        conn: asyncpg.Connection,
        *,
        hotel_id: int,
        event_type: str,
        reference_type: str,
        reference_id: str | None,
        actor_username: str,
        payload: dict[str, Any],
    ) -> None:
        await conn.execute(
            """
            INSERT INTO restaurant_menu_audit_logs (
                hotel_id, event_type, reference_type, reference_id, actor_username, payload_json
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            hotel_id,
            event_type,
            reference_type,
            reference_id,
            actor_username,
            _json_dumps(payload),
            timeout=DB_TIMEOUT_SECONDS,
        )
