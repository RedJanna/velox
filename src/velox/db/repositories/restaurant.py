"""Repository for restaurant holds and restaurant slots."""

from datetime import date, datetime, timedelta, time
from typing import Any

import asyncpg

from velox.config.constants import HoldStatus
from velox.db.database import execute, fetch, fetchrow, get_pool
from velox.models.restaurant import (
    RestaurantHold,
    RestaurantSlot,
    RestaurantSlotCreate,
    RestaurantSlotUpdate,
    RestaurantSlotView,
)
from velox.utils.id_gen import next_sequential_id

DB_TIMEOUT_SECONDS = 5


class RestaurantRepository:
    """CRUD operations for restaurant_holds and restaurant_slots tables."""

    async def get_available_slots(
        self,
        hotel_id: int,
        target_date: date,
        target_time: time,
        party_size: int,
        area: str | None = None,
    ) -> list[RestaurantSlot]:
        """Query active slots within +/-1 hour and with enough capacity."""
        start_time = (datetime.combine(target_date, target_time) - timedelta(hours=1)).time()
        end_time = (datetime.combine(target_date, target_time) + timedelta(hours=1)).time()

        if area:
            rows = await fetch(
                """
                SELECT id AS slot_id, time, (total_capacity - booked_count) AS capacity_left
                FROM restaurant_slots
                WHERE hotel_id = $1 AND date = $2 AND is_active = true
                  AND time BETWEEN $3 AND $4
                  AND (total_capacity - booked_count) >= $5
                  AND area = $6
                ORDER BY ABS(EXTRACT(EPOCH FROM (time - $7))) ASC, time ASC
                """,
                hotel_id,
                target_date,
                start_time,
                end_time,
                party_size,
                area,
                target_time,
            )
        else:
            rows = await fetch(
                """
                SELECT id AS slot_id, time, (total_capacity - booked_count) AS capacity_left
                FROM restaurant_slots
                WHERE hotel_id = $1 AND date = $2 AND is_active = true
                  AND time BETWEEN $3 AND $4
                  AND (total_capacity - booked_count) >= $5
                ORDER BY ABS(EXTRACT(EPOCH FROM (time - $6))) ASC, time ASC
                """,
                hotel_id,
                target_date,
                start_time,
                end_time,
                party_size,
                target_time,
            )
        return [
            RestaurantSlot(
                slot_id=str(row["slot_id"]),
                time=row["time"],
                capacity_left=int(row["capacity_left"]),
            )
            for row in rows
        ]

    async def create_hold(self, hold: RestaurantHold) -> RestaurantHold:
        """Insert restaurant hold and decrement slot capacity atomically."""
        if hold.slot_id is None:
            raise ValueError("slot_id_required")

        hold.hold_id = await next_sequential_id("R_HOLD_", "restaurant_holds", "hold_id")
        slot_id = int(hold.slot_id)

        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                slot = await conn.fetchrow(
                    """
                    SELECT id, date, time, area, total_capacity, booked_count
                    FROM restaurant_slots
                    WHERE id = $1 AND hotel_id = $2 AND is_active = true
                    FOR UPDATE
                    """,
                    slot_id,
                    hold.hotel_id,
                    timeout=DB_TIMEOUT_SECONDS,
                )
                if slot is None:
                    raise ValueError("slot_not_found")

                capacity_left = int(slot["total_capacity"]) - int(slot["booked_count"])
                if capacity_left < hold.party_size:
                    raise ValueError("slot_capacity_not_enough")

                row = await conn.fetchrow(
                    """
                    INSERT INTO restaurant_holds
                        (hold_id, hotel_id, conversation_id, slot_id, date, time, party_size,
                         guest_name, phone, area, notes, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id, created_at
                    """,
                    hold.hold_id,
                    hold.hotel_id,
                    hold.conversation_id,
                    str(slot["id"]),
                    slot["date"],
                    slot["time"],
                    hold.party_size,
                    hold.guest_name,
                    hold.phone,
                    hold.area or slot["area"],
                    hold.notes,
                    hold.status.value,
                    timeout=DB_TIMEOUT_SECONDS,
                )
                if row is None:
                    raise RuntimeError("restaurant_hold_create_failed")

                await conn.execute(
                    """
                    UPDATE restaurant_slots
                    SET booked_count = booked_count + $2
                    WHERE id = $1
                    """,
                    slot_id,
                    hold.party_size,
                    timeout=DB_TIMEOUT_SECONDS,
                )

        hold.id = row["id"]
        hold.created_at = row["created_at"]
        hold.date = slot["date"]
        hold.time = slot["time"]
        hold.area = hold.area or slot["area"]
        return hold

    async def update_hold_status(
        self,
        hold_id: str,
        status: str,
        approved_by: str | None = None,
        rejected_reason: str | None = None,
    ) -> None:
        """Update hold status (CONFIRMED, CANCELLED, etc.)."""
        await execute(
            """
            UPDATE restaurant_holds
            SET status = $2,
                approved_by = COALESCE($3, approved_by),
                approved_at = CASE WHEN $2 IN ('APPROVED', 'CONFIRMED') THEN now() ELSE approved_at END,
                rejected_reason = COALESCE($4, rejected_reason),
                updated_at = now()
            WHERE hold_id = $1
            """,
            hold_id,
            status,
            approved_by,
            rejected_reason,
        )

    async def cancel_hold(self, hold_id: str, reason: str) -> None:
        """Cancel hold and restore slot capacity atomically."""
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT hold_id, slot_id, party_size, status
                    FROM restaurant_holds
                    WHERE hold_id = $1
                    FOR UPDATE
                    """,
                    hold_id,
                    timeout=DB_TIMEOUT_SECONDS,
                )
                if row is None:
                    raise ValueError("restaurant_hold_not_found")

                await conn.execute(
                    """
                    UPDATE restaurant_holds
                    SET status = $2, rejected_reason = $3, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                    HoldStatus.CANCELLED.value,
                    reason,
                    timeout=DB_TIMEOUT_SECONDS,
                )

                slot_id = row["slot_id"]
                if slot_id and str(row["status"]) != HoldStatus.CANCELLED.value:
                    await conn.execute(
                        """
                        UPDATE restaurant_slots
                        SET booked_count = GREATEST(0, booked_count - $2)
                        WHERE id = $1
                        """,
                        int(slot_id),
                        int(row["party_size"] or 0),
                        timeout=DB_TIMEOUT_SECONDS,
                    )

    async def get_hold(self, hold_id: str) -> RestaurantHold | None:
        """Fetch hold by ID."""
        row = await fetchrow("SELECT * FROM restaurant_holds WHERE hold_id = $1", hold_id)
        if row is None:
            return None
        return self._row_to_hold(row)

    async def get_by_hold_id(self, hold_id: str) -> RestaurantHold | None:
        """Backward-compatible alias for get_hold."""
        return await self.get_hold(hold_id)

    async def get_holds_by_date(self, hotel_id: int, target_date: date) -> list[RestaurantHold]:
        """Get all restaurant holds for a specific date."""
        rows = await fetch(
            """
            SELECT * FROM restaurant_holds
            WHERE hotel_id = $1 AND date = $2
            ORDER BY time ASC
            """,
            hotel_id,
            target_date,
        )
        return [self._row_to_hold(row) for row in rows]

    async def create_slots(self, hotel_id: int, slots: list[RestaurantSlotCreate]) -> int:
        """Create or upsert restaurant slots for date ranges."""
        if not slots:
            return 0

        inserted = 0
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for slot in slots:
                    if slot.date_to < slot.date_from:
                        raise ValueError("invalid_date_range")
                    current_date = slot.date_from
                    while current_date <= slot.date_to:
                        await conn.execute(
                            """
                            INSERT INTO restaurant_slots
                                (hotel_id, date, time, area, total_capacity, is_active)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (hotel_id, date, time, area)
                            DO UPDATE SET
                                total_capacity = GREATEST(EXCLUDED.total_capacity, restaurant_slots.booked_count),
                                is_active = EXCLUDED.is_active
                            """,
                            hotel_id,
                            current_date,
                            slot.time,
                            slot.area,
                            slot.total_capacity,
                            slot.is_active,
                            timeout=DB_TIMEOUT_SECONDS,
                        )
                        inserted += 1
                        current_date += timedelta(days=1)
        return inserted

    async def get_slot_by_id(self, hotel_id: int, slot_id: int) -> dict[str, Any] | None:
        """Fetch one slot by id for validation and hold creation."""
        row = await fetchrow(
            """
            SELECT id AS slot_id, hotel_id, date, time, area,
                   total_capacity, booked_count,
                   (total_capacity - booked_count) AS capacity_left,
                   is_active
            FROM restaurant_slots
            WHERE hotel_id = $1 AND id = $2
            """,
            hotel_id,
            slot_id,
        )
        return dict(row) if row else None

    async def list_slots(
        self,
        hotel_id: int,
        date_from: date,
        date_to: date,
    ) -> list[RestaurantSlotView]:
        """List restaurant slots and remaining capacity in date range."""
        rows = await fetch(
            """
            SELECT
                id AS slot_id,
                hotel_id,
                date,
                time,
                area,
                total_capacity,
                booked_count,
                (total_capacity - booked_count) AS capacity_left,
                is_active
            FROM restaurant_slots
            WHERE hotel_id = $1 AND date BETWEEN $2 AND $3
            ORDER BY date ASC, time ASC
            """,
            hotel_id,
            date_from,
            date_to,
        )
        return [RestaurantSlotView.model_validate(dict(row)) for row in rows]

    async def update_slot(self, hotel_id: int, slot_id: int, update: RestaurantSlotUpdate) -> dict[str, Any] | None:
        """Update slot capacity or active status and return row summary."""
        if update.total_capacity is not None:
            current = await fetchrow(
                "SELECT booked_count FROM restaurant_slots WHERE hotel_id = $1 AND id = $2",
                hotel_id,
                slot_id,
            )
            if current is None:
                return None
            if int(update.total_capacity) < int(current["booked_count"]):
                raise ValueError("total_capacity_below_booked_count")

        row = await fetchrow(
            """
            UPDATE restaurant_slots
            SET total_capacity = COALESCE($3, total_capacity),
                is_active = COALESCE($4, is_active)
            WHERE hotel_id = $1 AND id = $2
            RETURNING id AS slot_id, hotel_id, date, time, area,
                      total_capacity, booked_count,
                      (total_capacity - booked_count) AS capacity_left,
                      is_active
            """,
            hotel_id,
            slot_id,
            update.total_capacity,
            update.is_active,
        )
        return dict(row) if row else None

    async def update_status(
        self,
        hold_id: str,
        status: str,
        approved_by: str | None = None,
        rejected_reason: str | None = None,
    ) -> None:
        """Backward-compatible alias for update_hold_status."""
        await self.update_hold_status(hold_id, status, approved_by, rejected_reason)

    @staticmethod
    def _row_to_hold(row: asyncpg.Record) -> RestaurantHold:
        """Map asyncpg row to RestaurantHold model."""
        return RestaurantHold(
            id=row["id"],
            hold_id=row["hold_id"],
            hotel_id=row["hotel_id"],
            conversation_id=row["conversation_id"],
            slot_id=row["slot_id"],
            date=row["date"],
            time=row["time"],
            party_size=row["party_size"],
            guest_name=row["guest_name"],
            phone=row["phone"],
            area=row["area"],
            notes=row["notes"],
            status=row["status"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            rejected_reason=row["rejected_reason"],
            created_at=row["created_at"],
        )
