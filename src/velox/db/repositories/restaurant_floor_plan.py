"""Repository for restaurant floor plans, tables, settings, and daily-view queries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import asyncpg
import structlog

from velox.config.constants import (
    RESTAURANT_STATUS_TRANSITIONS,
    RestaurantReservationMode,
    RestaurantReservationStatus,
)
from velox.db.database import execute, fetch, fetchrow, fetchval, get_pool
from velox.models.restaurant import (
    DailyTableView,
    FloorPlan,
    FloorPlanLayout,
    RestaurantSettings,
    RestaurantTable,
)

logger = structlog.get_logger(__name__)

DB_TIMEOUT_SECONDS = 5


def _safe_int(value: object) -> int:
    """Convert DB scalar values to int with tolerant fallbacks."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value) if value.strip() else 0
    if isinstance(value, (bytes, bytearray)):
        decoded = value.decode(errors="ignore").strip()
        return int(decoded) if decoded else 0
    return 0


class FloorPlanRepository:
    """CRUD for restaurant_floor_plans and restaurant_tables."""

    # ------------------------------------------------------------------
    # Floor plan CRUD
    # ------------------------------------------------------------------

    async def get_active_plan(self, hotel_id: int) -> FloorPlan | None:
        """Return the single active floor plan for a hotel."""
        row = await fetchrow(
            "SELECT * FROM restaurant_floor_plans WHERE hotel_id = $1 AND is_active = true",
            hotel_id,
        )
        if row is None:
            return None
        return self._row_to_plan(row)

    async def get_plan_by_id(self, hotel_id: int, plan_id: UUID) -> FloorPlan | None:
        """Fetch a specific floor plan."""
        row = await fetchrow(
            "SELECT * FROM restaurant_floor_plans WHERE hotel_id = $1 AND id = $2",
            hotel_id,
            plan_id,
        )
        if row is None:
            return None
        return self._row_to_plan(row)

    async def list_plans(self, hotel_id: int) -> list[FloorPlan]:
        """List all floor plans for a hotel (active first, newest first)."""
        rows = await fetch(
            """
            SELECT *
            FROM restaurant_floor_plans
            WHERE hotel_id = $1
            ORDER BY is_active DESC, updated_at DESC
            """,
            hotel_id,
        )
        return [self._row_to_plan(row) for row in rows]

    async def create_plan(self, hotel_id: int, plan: FloorPlan) -> FloorPlan:
        """Create a new floor plan and sync tables. Deactivates existing active plan."""
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            # Deactivate existing active plan
            await conn.execute(
                "UPDATE restaurant_floor_plans SET is_active = false, updated_at = now() "
                "WHERE hotel_id = $1 AND is_active = true",
                hotel_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            row = await conn.fetchrow(
                """
                INSERT INTO restaurant_floor_plans (hotel_id, name, layout_data, is_active, created_by)
                VALUES ($1, $2, $3, true, $4)
                RETURNING id, created_at, updated_at
                """,
                hotel_id,
                plan.name,
                plan.layout_data.model_dump_json(),
                plan.created_by,
                timeout=DB_TIMEOUT_SECONDS,
            )
            plan.id = row["id"]
            plan.hotel_id = hotel_id
            plan.is_active = True
            plan.created_at = row["created_at"]
            plan.updated_at = row["updated_at"]

            # Sync tables from layout
            await self._sync_tables(conn, hotel_id, plan.id, plan.layout_data)

        return plan

    async def update_plan(
        self,
        hotel_id: int,
        plan_id: UUID,
        name: str | None,
        layout_data: FloorPlanLayout | None,
    ) -> FloorPlan | None:
        """Update plan name and/or layout. Re-syncs tables on layout change."""
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE restaurant_floor_plans
                SET name = COALESCE($3, name),
                    layout_data = COALESCE($4::jsonb, layout_data),
                    updated_at = now()
                WHERE hotel_id = $1 AND id = $2
                RETURNING *
                """,
                hotel_id,
                plan_id,
                name,
                layout_data.model_dump_json() if layout_data else None,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if row is None:
                return None

            plan = self._row_to_plan(row)

            if layout_data:
                await self._sync_tables(conn, hotel_id, plan_id, layout_data)

        return plan

    async def delete_plan(self, hotel_id: int, plan_id: UUID) -> bool:
        """Delete a floor plan and its associated tables.

        Active plans cannot be deleted — deactivate or switch first.
        """
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            # Prevent deleting the active plan
            row = await conn.fetchrow(
                "SELECT is_active FROM restaurant_floor_plans WHERE hotel_id = $1 AND id = $2",
                hotel_id,
                plan_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if not row:
                return False
            if row["is_active"]:
                raise ValueError("Aktif plan silinemez. Once baska bir plani aktif yapin.")
            # Remove associated tables
            await conn.execute(
                "DELETE FROM restaurant_tables WHERE hotel_id = $1 AND floor_plan_id = $2",
                hotel_id,
                plan_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            result = await conn.execute(
                "DELETE FROM restaurant_floor_plans WHERE hotel_id = $1 AND id = $2",
                hotel_id,
                plan_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
        return str(result) == "DELETE 1"

    async def activate_plan(self, hotel_id: int, plan_id: UUID) -> bool:
        """Set a plan as active, deactivating others."""
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "UPDATE restaurant_floor_plans SET is_active = false, updated_at = now() "
                "WHERE hotel_id = $1 AND is_active = true",
                hotel_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            result = await conn.execute(
                "UPDATE restaurant_floor_plans SET is_active = true, updated_at = now() "
                "WHERE hotel_id = $1 AND id = $2",
                hotel_id,
                plan_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
        return str(result) == "UPDATE 1"

    # ------------------------------------------------------------------
    # Table sync
    # ------------------------------------------------------------------

    async def _sync_tables(
        self,
        conn: asyncpg.Connection,
        hotel_id: int,
        plan_id: UUID,
        layout: FloorPlanLayout,
    ) -> None:
        """Sync restaurant_tables from layout_data. Soft-delete removed tables."""
        layout_table_ids = {t.table_id for t in layout.tables}

        # Deactivate tables no longer in layout
        await conn.execute(
            """
            UPDATE restaurant_tables SET is_active = false
            WHERE hotel_id = $1 AND floor_plan_id = $2 AND table_id != ALL($3::text[])
            """,
            hotel_id,
            plan_id,
            list(layout_table_ids),
            timeout=DB_TIMEOUT_SECONDS,
        )

        # Clear table assignments for deactivated tables on future reservations
        await conn.execute(
            """
            UPDATE restaurant_holds
            SET table_id = NULL
            WHERE hotel_id = $1
              AND date >= CURRENT_DATE
              AND table_id IS NOT NULL
              AND table_id NOT IN (
                  SELECT table_id FROM restaurant_tables
                  WHERE hotel_id = $1 AND floor_plan_id = $2 AND is_active = true
              )
            """,
            hotel_id,
            plan_id,
            timeout=DB_TIMEOUT_SECONDS,
        )

        # Upsert tables from layout
        for t in layout.tables:
            await conn.execute(
                """
                INSERT INTO restaurant_tables (hotel_id, floor_plan_id, table_id, table_type, capacity, is_active)
                VALUES ($1, $2, $3, $4, $5, true)
                ON CONFLICT (hotel_id, table_id)
                DO UPDATE SET table_type = $4, capacity = $5, is_active = true, floor_plan_id = $2
                """,
                hotel_id,
                plan_id,
                t.table_id,
                t.type,
                t.capacity,
                timeout=DB_TIMEOUT_SECONDS,
            )

    async def list_tables(self, hotel_id: int) -> list[RestaurantTable]:
        """List all active tables for the active floor plan."""
        rows = await fetch(
            """
            SELECT rt.* FROM restaurant_tables rt
            JOIN restaurant_floor_plans fp ON fp.id = rt.floor_plan_id
            WHERE rt.hotel_id = $1 AND rt.is_active = true AND fp.is_active = true
            ORDER BY rt.table_id
            """,
            hotel_id,
        )
        return [
            RestaurantTable(
                id=r["id"],
                hotel_id=r["hotel_id"],
                floor_plan_id=r["floor_plan_id"],
                table_id=r["table_id"],
                table_type=r["table_type"],
                capacity=r["capacity"],
                is_active=r["is_active"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Daily view
    # ------------------------------------------------------------------

    async def get_daily_view(
        self, hotel_id: int, target_date: date
    ) -> list[DailyTableView]:
        """Get all tables with assigned reservations for a specific day."""
        plan = await self.get_active_plan(hotel_id)
        if plan is None:
            return []

        rows = await fetch(
            """
            SELECT
                rt.table_id, rt.table_type, rt.capacity,
                rh.hold_id, rh.guest_name, rh.party_size, rh.time AS reservation_time, rh.status
            FROM restaurant_tables rt
            LEFT JOIN restaurant_holds rh
                ON rh.hotel_id = rt.hotel_id
                AND rh.table_id = rt.table_id
                AND rh.date = $2
                AND rh.status NOT IN ('IPTAL', 'GELMEDI')
            WHERE rt.hotel_id = $1
              AND rt.floor_plan_id = $3
              AND rt.is_active = true
            ORDER BY rt.table_id
            """,
            hotel_id,
            target_date,
            plan.id,
        )

        # Build table position map from layout
        table_positions: dict[str, dict[str, float]] = {}
        for t in plan.layout_data.tables:
            table_positions[t.table_id] = {"x": t.x, "y": t.y, "rotation": t.rotation}

        result = []
        for r in rows:
            pos = table_positions.get(r["table_id"], {"x": 0, "y": 0, "rotation": 0})
            result.append(
                DailyTableView(
                    table_id=r["table_id"],
                    table_type=r["table_type"],
                    capacity=r["capacity"],
                    x=pos["x"],
                    y=pos["y"],
                    rotation=pos["rotation"],
                    hold_id=r["hold_id"],
                    guest_name=r["guest_name"],
                    party_size=r["party_size"],
                    reservation_time=r["reservation_time"],
                    status=r["status"],
                )
            )
        return result

    # ------------------------------------------------------------------
    # Table assignment
    # ------------------------------------------------------------------

    async def find_available_table(
        self,
        hotel_id: int,
        target_date: date,
        _target_time: time,
        table_type: str,
    ) -> str | None:
        """Find a free table of given type for a date+time slot."""
        plan = await self.get_active_plan(hotel_id)
        if plan is None:
            return None

        row = await fetchrow(
            """
            SELECT rt.table_id
            FROM restaurant_tables rt
            WHERE rt.hotel_id = $1
              AND rt.floor_plan_id = $2
              AND rt.table_type = $3
              AND rt.is_active = true
              AND rt.table_id NOT IN (
                  SELECT rh.table_id FROM restaurant_holds rh
                  WHERE rh.hotel_id = $1
                    AND rh.date = $4
                    AND rh.table_id IS NOT NULL
                    AND rh.status NOT IN ('IPTAL', 'GELMEDI')
              )
            ORDER BY rt.table_id
            LIMIT 1
            """,
            hotel_id,
            plan.id,
            table_type,
            target_date,
        )
        return row["table_id"] if row else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_plan(row: asyncpg.Record) -> FloorPlan:
        """Map DB row to FloorPlan model."""
        import orjson

        raw_layout = row["layout_data"]
        layout_dict = orjson.loads(raw_layout) if isinstance(raw_layout, str) else raw_layout

        return FloorPlan(
            id=row["id"],
            hotel_id=row["hotel_id"],
            name=row["name"],
            layout_data=FloorPlanLayout.model_validate(layout_dict),
            is_active=row["is_active"],
            created_by=row.get("created_by"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class RestaurantSettingsRepository:
    """CRUD for restaurant_settings table."""

    async def get(self, hotel_id: int) -> RestaurantSettings:
        """Get settings or return defaults."""
        row = await fetchrow(
            "SELECT * FROM restaurant_settings WHERE hotel_id = $1",
            hotel_id,
        )
        if row is None:
            return RestaurantSettings(hotel_id=hotel_id)
        return RestaurantSettings(
            hotel_id=row["hotel_id"],
            reservation_mode=RestaurantReservationMode(
                row.get("reservation_mode") or RestaurantReservationMode.AI_RESTAURAN.value
            ),
            daily_max_reservations_enabled=row["daily_max_reservations_enabled"],
            daily_max_reservations_count=row["daily_max_reservations_count"],
            daily_max_party_size_enabled=row.get("daily_max_party_size_enabled") or False,
            daily_max_party_size_count=row.get("daily_max_party_size_count") or 200,
            min_party_size=row.get("min_party_size") or 1,
            max_party_size=row.get("max_party_size") or 8,
            chef_phone=row.get("chef_phone"),
            service_mode_main_plan_id=row.get("service_mode_main_plan_id"),
            service_mode_pool_plan_id=row.get("service_mode_pool_plan_id"),
            updated_at=row["updated_at"],
        )

    async def upsert(self, hotel_id: int, settings: RestaurantSettings) -> RestaurantSettings:
        """Insert or update settings."""
        row = await fetchrow(
            """
            INSERT INTO restaurant_settings (
                hotel_id,
                reservation_mode,
                daily_max_reservations_enabled,
                daily_max_reservations_count,
                daily_max_party_size_enabled,
                daily_max_party_size_count,
                min_party_size,
                max_party_size,
                chef_phone,
                service_mode_main_plan_id,
                service_mode_pool_plan_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (hotel_id)
            DO UPDATE SET
                reservation_mode = $2,
                daily_max_reservations_enabled = $3,
                daily_max_reservations_count = $4,
                daily_max_party_size_enabled = $5,
                daily_max_party_size_count = $6,
                min_party_size = $7,
                max_party_size = $8,
                chef_phone = $9,
                service_mode_main_plan_id = $10,
                service_mode_pool_plan_id = $11,
                updated_at = now()
            RETURNING *
            """,
            hotel_id,
            settings.reservation_mode.value,
            settings.daily_max_reservations_enabled,
            settings.daily_max_reservations_count,
            settings.daily_max_party_size_enabled,
            settings.daily_max_party_size_count,
            settings.min_party_size,
            settings.max_party_size,
            settings.chef_phone,
            settings.service_mode_main_plan_id,
            settings.service_mode_pool_plan_id,
        )
        if row is None:
            raise RuntimeError("Failed to upsert restaurant settings.")
        return RestaurantSettings(
            hotel_id=row["hotel_id"],
            reservation_mode=RestaurantReservationMode(
                row.get("reservation_mode") or RestaurantReservationMode.AI_RESTAURAN.value
            ),
            daily_max_reservations_enabled=row["daily_max_reservations_enabled"],
            daily_max_reservations_count=row["daily_max_reservations_count"],
            daily_max_party_size_enabled=row.get("daily_max_party_size_enabled") or False,
            daily_max_party_size_count=row.get("daily_max_party_size_count") or 200,
            min_party_size=row.get("min_party_size") or 1,
            max_party_size=row.get("max_party_size") or 8,
            chef_phone=row.get("chef_phone"),
            service_mode_main_plan_id=row.get("service_mode_main_plan_id"),
            service_mode_pool_plan_id=row.get("service_mode_pool_plan_id"),
            updated_at=row["updated_at"],
        )

    async def check_daily_capacity(self, hotel_id: int, target_date: date, new_party_size: int = 0) -> dict[str, Any]:
        """Check if daily reservation-count and total-party-size limits allow a new reservation."""
        settings = await self.get(hotel_id)

        count = _safe_int(
            await fetchval(
                """
                SELECT COUNT(*) FROM restaurant_holds
                WHERE hotel_id = $1 AND date = $2
                  AND status NOT IN ('IPTAL', 'GELMEDI')
                """,
                hotel_id,
                target_date,
            )
        )
        total_party_size = _safe_int(
            await fetchval(
                """
                SELECT COALESCE(SUM(party_size), 0) FROM restaurant_holds
                WHERE hotel_id = $1 AND date = $2
                  AND status NOT IN ('IPTAL', 'GELMEDI')
                """,
                hotel_id,
                target_date,
            )
        )
        reservation_allowed = (not settings.daily_max_reservations_enabled) or (
            count < settings.daily_max_reservations_count
        )
        party_allowed = (not settings.daily_max_party_size_enabled) or (
            (total_party_size + max(0, new_party_size)) <= settings.daily_max_party_size_count
        )
        return {
            "allowed": reservation_allowed and party_allowed,
            "reservation_allowed": reservation_allowed,
            "party_allowed": party_allowed,
            "count": count,
            "max": settings.daily_max_reservations_count,
            "enabled": settings.daily_max_reservations_enabled,
            "party_size_total": total_party_size,
            "party_size_max": settings.daily_max_party_size_count,
            "party_size_enabled": settings.daily_max_party_size_enabled,
        }


class RestaurantStatusManager:
    """Handles restaurant reservation status transitions and no-show automation."""

    async def change_status(
        self,
        hold_id: str,
        new_status: str,
        actor: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Validate and apply a status transition."""
        row = await fetchrow(
            "SELECT hold_id, status, time, date, table_id, extended_minutes "
            "FROM restaurant_holds WHERE hold_id = $1",
            hold_id,
        )
        if row is None:
            raise ValueError("restaurant_hold_not_found")

        current_status = str(row["status"])
        allowed = RESTAURANT_STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"invalid_transition:{current_status}->{new_status}"
            )

        cancelled_statuses = (
            RestaurantReservationStatus.GELMEDI,
            RestaurantReservationStatus.IPTAL,
        )
        clear_table = new_status in cancelled_statuses
        rejected_reason_value = reason if new_status == RestaurantReservationStatus.IPTAL else None
        approved_by_value = actor if new_status == RestaurantReservationStatus.ONAYLANDI else None
        await execute(
            """
            UPDATE restaurant_holds
            SET
                status = $2,
                updated_at = now(),
                arrived_at = CASE
                    WHEN $2 = 'GELDI' THEN now()
                    ELSE arrived_at
                END,
                no_show_at = CASE
                    WHEN $2 = 'GELMEDI' THEN now()
                    ELSE no_show_at
                END,
                table_id = CASE
                    WHEN $3 THEN NULL
                    ELSE table_id
                END,
                approved_by = CASE
                    WHEN $2 = 'ONAYLANDI' THEN $4
                    ELSE approved_by
                END,
                approved_at = CASE
                    WHEN $2 = 'ONAYLANDI' THEN now()
                    ELSE approved_at
                END,
                rejected_reason = CASE
                    WHEN $2 IN ('GELDI', 'GELMEDI', 'ONAYLANDI') THEN NULL
                    WHEN $2 = 'IPTAL' THEN $5
                    ELSE rejected_reason
                END
            WHERE hold_id = $1
            """,
            hold_id,
            new_status,
            clear_table,
            approved_by_value,
            rejected_reason_value,
        )

        # Restore slot capacity on IPTAL or GELMEDI
        if new_status in (
            RestaurantReservationStatus.IPTAL,
            RestaurantReservationStatus.GELMEDI,
        ):
            await self._restore_slot_capacity(hold_id)

        return {"hold_id": hold_id, "previous_status": current_status, "new_status": new_status}

    async def extend_time(self, hold_id: str) -> dict[str, Any]:
        """+15 minute extension. Max 3 times (45 min total)."""
        from velox.config.constants import RESTAURANT_EXTEND_MINUTES, RESTAURANT_MAX_EXTEND_COUNT

        row = await fetchrow(
            "SELECT hold_id, status, time, date, extended_minutes "
            "FROM restaurant_holds WHERE hold_id = $1",
            hold_id,
        )
        if row is None:
            raise ValueError("restaurant_hold_not_found")

        if str(row["status"]) != RestaurantReservationStatus.ONAYLANDI:
            raise ValueError("extend_only_for_onaylandi")

        current_extends = int(row["extended_minutes"] or 0)
        extend_count = current_extends // RESTAURANT_EXTEND_MINUTES
        if extend_count >= RESTAURANT_MAX_EXTEND_COUNT:
            raise ValueError("max_extend_reached")

        # Calculate new time
        current_time = row["time"]
        current_date = row["date"]
        new_dt = datetime.combine(current_date, current_time) + timedelta(minutes=RESTAURANT_EXTEND_MINUTES)
        new_time = new_dt.time()

        await execute(
            """
            UPDATE restaurant_holds
            SET time = $2,
                extended_minutes = extended_minutes + $3,
                updated_at = now()
            WHERE hold_id = $1
            """,
            hold_id,
            new_time,
            RESTAURANT_EXTEND_MINUTES,
        )

        return {
            "hold_id": hold_id,
            "new_time": str(new_time),
            "total_extended_minutes": current_extends + RESTAURANT_EXTEND_MINUTES,
        }

    async def process_no_shows(self, hotel_id: int) -> int:
        """Find overdue ONAYLANDI reservations and mark as GELMEDI."""
        from velox.config.constants import RESTAURANT_LATE_TOLERANCE_MINUTES

        now = datetime.now()
        today = now.date()
        cutoff_time = (now - timedelta(minutes=RESTAURANT_LATE_TOLERANCE_MINUTES)).time()

        rows = await fetch(
            """
            SELECT hold_id, table_id, slot_id, party_size
            FROM restaurant_holds
            WHERE hotel_id = $1
              AND date = $2
              AND status = $3
              AND time < $4
            """,
            hotel_id,
            today,
            RestaurantReservationStatus.ONAYLANDI,
            cutoff_time,
        )

        count = 0
        for r in rows:
            await execute(
                """
                UPDATE restaurant_holds
                SET status = $2, no_show_at = now(), table_id = NULL, updated_at = now()
                WHERE hold_id = $1
                """,
                r["hold_id"],
                RestaurantReservationStatus.GELMEDI,
            )
            await self._restore_slot_capacity(r["hold_id"])
            count += 1
            logger.info(
                "restaurant_no_show",
                hold_id=r["hold_id"],
                hotel_id=hotel_id,
            )

        return count

    async def _restore_slot_capacity(self, hold_id: str) -> None:
        """Restore slot capacity when a reservation is cancelled or no-show."""
        row = await fetchrow(
            "SELECT slot_id, party_size, status FROM restaurant_holds WHERE hold_id = $1",
            hold_id,
        )
        if row and row["slot_id"]:
            slot = await fetchrow(
                "SELECT capacity_window_id FROM restaurant_slots WHERE id = $1",
                int(row["slot_id"]),
            )
            await execute(
                """
                UPDATE restaurant_slots
                SET booked_count = GREATEST(0, booked_count - 1)
                WHERE id = $1
                """,
                int(row["slot_id"]),
            )
            if slot and slot["capacity_window_id"]:
                await execute(
                    """
                    UPDATE restaurant_capacity_windows
                    SET booked_reservations = GREATEST(0, booked_reservations - 1),
                        booked_party_size = GREATEST(0, booked_party_size - $2)
                    WHERE id = $1
                    """,
                    int(slot["capacity_window_id"]),
                    int(row["party_size"] or 0),
                )
