"""Repository for restaurant floor plans, tables, settings, and daily-view queries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import asyncpg
import structlog

from velox.config.constants import (
    RESTAURANT_STATUS_TRANSITIONS,
    RestaurantReservationStatus,
    resolve_table_type,
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
        return result == "UPDATE 1"

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
        target_time: time,
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
        if isinstance(raw_layout, str):
            layout_dict = orjson.loads(raw_layout)
        else:
            layout_dict = raw_layout

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
            daily_max_reservations_enabled=row["daily_max_reservations_enabled"],
            daily_max_reservations_count=row["daily_max_reservations_count"],
            chef_phone=row.get("chef_phone"),
            updated_at=row["updated_at"],
        )

    async def upsert(self, hotel_id: int, settings: RestaurantSettings) -> RestaurantSettings:
        """Insert or update settings."""
        row = await fetchrow(
            """
            INSERT INTO restaurant_settings (
                hotel_id,
                daily_max_reservations_enabled,
                daily_max_reservations_count,
                chef_phone
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (hotel_id)
            DO UPDATE SET
                daily_max_reservations_enabled = $2,
                daily_max_reservations_count = $3,
                chef_phone = $4,
                updated_at = now()
            RETURNING *
            """,
            hotel_id,
            settings.daily_max_reservations_enabled,
            settings.daily_max_reservations_count,
            settings.chef_phone,
        )
        return RestaurantSettings(
            hotel_id=row["hotel_id"],
            daily_max_reservations_enabled=row["daily_max_reservations_enabled"],
            daily_max_reservations_count=row["daily_max_reservations_count"],
            chef_phone=row.get("chef_phone"),
            updated_at=row["updated_at"],
        )

    async def check_daily_capacity(self, hotel_id: int, target_date: date) -> dict[str, Any]:
        """Check if daily capacity allows a new reservation."""
        settings = await self.get(hotel_id)
        if not settings.daily_max_reservations_enabled:
            return {"allowed": True, "count": 0, "max": 0, "enabled": False}

        count = int(
            await fetchval(
                """
                SELECT COUNT(*) FROM restaurant_holds
                WHERE hotel_id = $1 AND date = $2
                  AND status NOT IN ('IPTAL', 'GELMEDI')
                """,
                hotel_id,
                target_date,
            )
            or 0
        )
        return {
            "allowed": count < settings.daily_max_reservations_count,
            "count": count,
            "max": settings.daily_max_reservations_count,
            "enabled": True,
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

        update_parts = ["status = $2", "updated_at = now()"]
        params: list[Any] = [hold_id, new_status]

        if new_status == RestaurantReservationStatus.GELDI:
            update_parts.append(f"arrived_at = now()")
        elif new_status == RestaurantReservationStatus.GELMEDI:
            update_parts.append(f"no_show_at = now()")
            update_parts.append(f"table_id = NULL")
        elif new_status == RestaurantReservationStatus.IPTAL:
            update_parts.append(f"table_id = NULL")
            if reason:
                update_parts.append(f"rejected_reason = ${len(params) + 1}")
                params.append(reason)
        elif new_status == RestaurantReservationStatus.ONAYLANDI:
            update_parts.append(f"approved_by = ${len(params) + 1}")
            update_parts.append(f"approved_at = now()")
            params.append(actor)

        set_clause = ", ".join(update_parts)
        await execute(
            f"UPDATE restaurant_holds SET {set_clause} WHERE hold_id = $1",
            *params,
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
            await execute(
                """
                UPDATE restaurant_slots
                SET booked_count = GREATEST(0, booked_count - $2)
                WHERE id = $1
                """,
                int(row["slot_id"]),
                int(row["party_size"] or 0),
            )
