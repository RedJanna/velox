"""Repository for restaurant holds and restaurant slots."""

from datetime import date, datetime, time, timedelta
from typing import Any

import asyncpg

from velox.config.constants import HoldStatus, RestaurantReservationStatus, resolve_table_type
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
        """Query active slots matching the requested minute and window constraints.

        Area is intentionally ignored so restaurant capacity is treated as a single pool.
        """
        _ = area
        rows = await fetch(
            """
            SELECT
                rs.id AS slot_id,
                rs.time,
                GREATEST(0, LEAST(rcw.reservation_limit - rcw.booked_reservations, COALESCE(rcw.total_party_size_limit - rcw.booked_party_size, rcw.reservation_limit - rcw.booked_reservations))) AS capacity_left
            FROM restaurant_slots rs
            LEFT JOIN restaurant_capacity_windows rcw ON rcw.id = rs.capacity_window_id
            WHERE rs.hotel_id = $1
              AND rs.date = $2
              AND rs.time = $3
              AND rs.is_active = true
              AND (
                    rcw.id IS NULL
                    OR (
                        rcw.is_active = true
                        AND rs.date BETWEEN rcw.date_from AND rcw.date_to
                        AND rs.time BETWEEN rcw.start_time AND rcw.end_time
                        AND $4 BETWEEN rcw.min_party_size AND rcw.max_party_size
                        AND rcw.booked_reservations < rcw.reservation_limit
                        AND COALESCE(rcw.booked_party_size, 0) + $4 <= COALESCE(rcw.total_party_size_limit, 2147483647)
                    )
              )
            ORDER BY rs.time ASC, rs.id ASC
            """,
            hotel_id,
            target_date,
            target_time,
            party_size,
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
        """Insert restaurant hold and decrement slot capacity atomically.

        Automatically assigns table_type based on party_size and attempts
        to assign a physical table_id from the active floor plan.
        """
        if hold.slot_id is None:
            raise ValueError("slot_id_required")

        hold.hold_id = await next_sequential_id("R_HOLD_", "restaurant_holds", "hold_id")
        slot_id = int(hold.slot_id)

        # Resolve table type from party size
        hold.table_type = resolve_table_type(hold.party_size)

        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            slot = await conn.fetchrow(
                """
                    SELECT rs.id, rs.date, rs.time, rs.area, rs.total_capacity, rs.booked_count,
                           rs.capacity_window_id,
                           rcw.reservation_limit,
                           rcw.booked_reservations,
                           rcw.total_party_size_limit,
                           rcw.booked_party_size,
                           rcw.min_party_size,
                           rcw.max_party_size,
                           rcw.is_active AS window_is_active
                    FROM restaurant_slots rs
                    LEFT JOIN restaurant_capacity_windows rcw ON rcw.id = rs.capacity_window_id
                    WHERE rs.id = $1 AND rs.hotel_id = $2 AND rs.is_active = true
                    FOR UPDATE OF rs
                    """,
                slot_id,
                hold.hotel_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if slot is None:
                raise ValueError("slot_not_found")

            if slot["capacity_window_id"] is not None:
                if not bool(slot["window_is_active"]):
                    raise ValueError("slot_not_found")
                min_party_size = int(slot["min_party_size"] or 1)
                max_party_size = int(slot["max_party_size"] or 8)
                if hold.party_size < min_party_size or hold.party_size > max_party_size:
                    raise ValueError("party_size_out_of_range")
                reservation_left = int(slot["reservation_limit"] or 0) - int(slot["booked_reservations"] or 0)
                if reservation_left < 1:
                    raise ValueError("window_capacity_not_enough")
                total_party_limit = slot["total_party_size_limit"]
                if total_party_limit is not None:
                    party_left = int(total_party_limit) - int(slot["booked_party_size"] or 0)
                    if party_left < hold.party_size:
                        raise ValueError("window_party_size_limit_not_enough")
            else:
                capacity_left = int(slot["total_capacity"]) - int(slot["booked_count"])
                if capacity_left < hold.party_size:
                    raise ValueError("slot_capacity_not_enough")

            # Try to assign a physical table from the active floor plan
            table_row = await conn.fetchrow(
                """
                SELECT rt.table_id
                FROM restaurant_tables rt
                JOIN restaurant_floor_plans fp ON fp.id = rt.floor_plan_id
                WHERE rt.hotel_id = $1
                  AND fp.is_active = true
                  AND rt.table_type = $2
                  AND rt.is_active = true
                  AND rt.table_id NOT IN (
                      SELECT rh.table_id FROM restaurant_holds rh
                      WHERE rh.hotel_id = $1
                        AND rh.date = $3
                        AND rh.table_id IS NOT NULL
                        AND rh.status NOT IN ('IPTAL', 'GELMEDI')
                  )
                ORDER BY rt.table_id
                LIMIT 1
                """,
                hold.hotel_id,
                hold.table_type,
                slot["date"],
                timeout=DB_TIMEOUT_SECONDS,
            )
            hold.table_id = table_row["table_id"] if table_row else None

            status_value = hold.status if isinstance(hold.status, str) else hold.status.value

            row = await conn.fetchrow(
                """
                    INSERT INTO restaurant_holds
                        (hold_id, hotel_id, conversation_id, slot_id, date, time, party_size,
                         guest_name, phone, area, notes, status, table_type, table_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
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
                status_value,
                hold.table_type,
                hold.table_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if row is None:
                raise RuntimeError("restaurant_hold_create_failed")

            await conn.execute(
                """
                    UPDATE restaurant_slots
                    SET booked_count = booked_count + 1
                    WHERE id = $1
                    """,
                slot_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if slot["capacity_window_id"] is not None:
                await conn.execute(
                    """
                        UPDATE restaurant_capacity_windows
                        SET booked_reservations = booked_reservations + 1,
                            booked_party_size = booked_party_size + $2
                        WHERE id = $1
                        """,
                    int(slot["capacity_window_id"]),
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
        status_value = status.value if hasattr(status, "value") else str(status)
        await execute(
            """
            UPDATE restaurant_holds
            SET status = $2::varchar,
                approved_by = COALESCE($3::varchar, approved_by),
                approved_at = CASE WHEN $2::varchar IN ('APPROVED', 'CONFIRMED', 'ONAYLANDI') THEN now() ELSE approved_at END,
                rejected_reason = COALESCE($4::text, rejected_reason),
                updated_at = now()
            WHERE hold_id = $1
            """,
            hold_id,
            status_value,
            approved_by,
            rejected_reason,
        )

    async def cancel_hold(self, hold_id: str, reason: str) -> None:
        """Cancel hold and restore slot capacity atomically."""
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
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
                slot_row = await conn.fetchrow(
                    "SELECT capacity_window_id FROM restaurant_slots WHERE id = $1",
                    int(slot_id),
                    timeout=DB_TIMEOUT_SECONDS,
                )
                await conn.execute(
                    """
                        UPDATE restaurant_slots
                        SET booked_count = GREATEST(0, booked_count - 1)
                        WHERE id = $1
                        """,
                    int(slot_id),
                    timeout=DB_TIMEOUT_SECONDS,
                )
                if slot_row and slot_row["capacity_window_id"]:
                    await conn.execute(
                        """
                            UPDATE restaurant_capacity_windows
                            SET booked_reservations = GREATEST(0, booked_reservations - 1),
                                booked_party_size = GREATEST(0, booked_party_size - $2)
                            WHERE id = $1
                            """,
                        int(slot_row["capacity_window_id"]),
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
        """Create or upsert restaurant slots for date ranges and optional time ranges."""
        if not slots:
            return 0

        inserted = 0
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            for slot in slots:
                if slot.date_to < slot.date_from:
                    raise ValueError("invalid_date_range")

                start_time = slot.start_time or slot.time
                end_time = slot.end_time or slot.time or slot.start_time
                if start_time is None or end_time is None:
                    raise ValueError("slot_time_required")
                if end_time < start_time:
                    raise ValueError("invalid_time_range")

                if slot.max_party_size < slot.min_party_size:
                    raise ValueError("invalid_party_size_range")

                reservation_limit = int(slot.reservation_limit or slot.total_capacity)
                window_row = await conn.fetchrow(
                    """
                    INSERT INTO restaurant_capacity_windows
                        (hotel_id, date_from, date_to, start_time, end_time, area,
                         reservation_limit, total_party_size_limit, min_party_size, max_party_size, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id
                    """,
                    hotel_id,
                    slot.date_from,
                    slot.date_to,
                    start_time,
                    end_time,
                    slot.area,
                    reservation_limit,
                    slot.total_party_size_limit,
                    slot.min_party_size,
                    slot.max_party_size,
                    slot.is_active,
                    timeout=DB_TIMEOUT_SECONDS,
                )
                if window_row is None:
                    raise RuntimeError("restaurant_capacity_window_create_failed")
                capacity_window_id = int(window_row["id"])

                start_dt = datetime.combine(slot.date_from, start_time)
                end_dt = datetime.combine(slot.date_from, end_time)
                step = timedelta(minutes=1 if slot.start_time is not None and slot.end_time is not None else int(slot.interval_minutes or 60))
                slot_times: list[time] = []
                current_dt = start_dt
                while current_dt <= end_dt:
                    slot_times.append(current_dt.time())
                    current_dt += step

                current_date = slot.date_from
                while current_date <= slot.date_to:
                    for slot_time in slot_times:
                        await conn.execute(
                            """
                                INSERT INTO restaurant_slots
                                    (hotel_id, date, time, area, total_capacity, is_active, capacity_window_id)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                                ON CONFLICT (hotel_id, date, time, area)
                                DO UPDATE SET
                                    total_capacity = GREATEST(EXCLUDED.total_capacity, restaurant_slots.booked_count),
                                    is_active = EXCLUDED.is_active,
                                    capacity_window_id = EXCLUDED.capacity_window_id
                                """,
                            hotel_id,
                            current_date,
                            slot_time,
                            slot.area,
                            reservation_limit,
                            slot.is_active,
                            capacity_window_id,
                            timeout=DB_TIMEOUT_SECONDS,
                        )
                        inserted += 1
                    current_date += timedelta(days=1)
        return inserted

    async def get_slot_by_id(self, hotel_id: int, slot_id: int) -> dict[str, Any] | None:
        """Fetch one slot by id for validation and hold creation."""
        row = await fetchrow(
            """
            SELECT rs.id AS slot_id, rs.hotel_id, rs.date, rs.time, rs.area,
                   rs.total_capacity, rs.booked_count,
                   CASE
                     WHEN rcw.id IS NOT NULL THEN GREATEST(0, rcw.reservation_limit - rcw.booked_reservations)
                     ELSE (rs.total_capacity - rs.booked_count)
                   END AS capacity_left,
                   rs.is_active,
                   rcw.reservation_limit,
                   rcw.booked_reservations AS window_booked_reservations,
                   rcw.total_party_size_limit,
                   rcw.booked_party_size AS window_booked_party_size,
                   rcw.min_party_size,
                   rcw.max_party_size,
                   rcw.date_from AS window_date_from,
                   rcw.date_to AS window_date_to,
                   rcw.start_time AS window_start_time,
                   rcw.end_time AS window_end_time,
                   rs.capacity_window_id
            FROM restaurant_slots rs
            LEFT JOIN restaurant_capacity_windows rcw ON rcw.id = rs.capacity_window_id
            WHERE rs.hotel_id = $1 AND rs.id = $2
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
                rs.id AS slot_id,
                rs.hotel_id,
                rs.date,
                rs.time,
                rs.area,
                rs.total_capacity,
                rs.booked_count,
                CASE
                  WHEN rcw.id IS NOT NULL THEN GREATEST(0, LEAST(rcw.reservation_limit - rcw.booked_reservations, COALESCE(rcw.total_party_size_limit - rcw.booked_party_size, rcw.reservation_limit - rcw.booked_reservations)))
                  ELSE (rs.total_capacity - rs.booked_count)
                END AS capacity_left,
                rs.is_active,
                rcw.reservation_limit,
                rcw.booked_reservations AS window_booked_reservations,
                rcw.total_party_size_limit,
                rcw.booked_party_size AS window_booked_party_size,
                rcw.min_party_size,
                rcw.max_party_size,
                rcw.date_from AS window_date_from,
                rcw.date_to AS window_date_to,
                rcw.start_time AS window_start_time,
                rcw.end_time AS window_end_time
            FROM restaurant_slots rs
            LEFT JOIN restaurant_capacity_windows rcw ON rcw.id = rs.capacity_window_id
            WHERE rs.hotel_id = $1 AND rs.date BETWEEN $2 AND $3
            ORDER BY rs.date ASC, rs.time ASC
            """,
            hotel_id,
            date_from,
            date_to,
        )
        return [RestaurantSlotView.model_validate(dict(row)) for row in rows]

    async def delete_slots_in_range(
        self,
        hotel_id: int,
        *,
        date_from: date,
        date_to: date,
        start_time: time,
        end_time: time,
        weekdays: list[int] | None = None,
        area: str | None = None,
    ) -> dict[str, int]:
        """Delete slots in an inclusive date/time range, optionally filtered by weekday and area."""
        if date_to < date_from:
            raise ValueError("invalid_date_range")
        if end_time < start_time:
            raise ValueError("invalid_time_range")
        if weekdays is not None:
            invalid_days = [day for day in weekdays if day < 0 or day > 6]
            if invalid_days:
                raise ValueError("invalid_weekdays")

        params: list[Any] = [hotel_id, date_from, date_to, start_time, end_time]
        where_parts = [
            "hotel_id = $1",
            "date BETWEEN $2 AND $3",
            "time BETWEEN $4 AND $5",
        ]
        if weekdays:
            weekday_placeholders: list[str] = []
            for day in weekdays:
                params.append(int(day))
                weekday_placeholders.append(f"${len(params)}")
            where_parts.append(f"EXTRACT(ISODOW FROM date)::int - 1 IN ({', '.join(weekday_placeholders)})")
        if area:
            params.append(area)
            where_parts.append(f"area = ${len(params)}")

        where_sql = " AND ".join(where_parts)
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            deleted_rows = await conn.fetch(
                f"DELETE FROM restaurant_slots WHERE {where_sql} RETURNING capacity_window_id",
                *params,
                timeout=DB_TIMEOUT_SECONDS,
            )
            deleted_count = len(deleted_rows)
            if deleted_count:
                window_ids = sorted({int(row["capacity_window_id"]) for row in deleted_rows if row["capacity_window_id"] is not None})
                if window_ids:
                    await conn.execute(
                        """
                        DELETE FROM restaurant_capacity_windows rcw
                        WHERE rcw.id = ANY($1::int[])
                          AND NOT EXISTS (
                              SELECT 1 FROM restaurant_slots rs WHERE rs.capacity_window_id = rcw.id
                          )
                        """,
                        window_ids,
                        timeout=DB_TIMEOUT_SECONDS,
                    )
            return {"deleted_count": deleted_count}

    async def update_slot(self, hotel_id: int, slot_id: int, update: RestaurantSlotUpdate) -> dict[str, Any] | None:
        """Update slot/window capacity or active status and return row summary."""
        current = await fetchrow(
            "SELECT booked_count, capacity_window_id FROM restaurant_slots WHERE hotel_id = $1 AND id = $2",
            hotel_id,
            slot_id,
        )
        if current is None:
            return None
        if update.max_party_size is not None and update.min_party_size is not None and update.max_party_size < update.min_party_size:
            raise ValueError("invalid_party_size_range")
        if update.total_capacity is not None and int(update.total_capacity) < int(current["booked_count"]):
            raise ValueError("total_capacity_below_booked_count")

        if current["capacity_window_id"] is not None:
            window = await fetchrow(
                "SELECT booked_reservations, min_party_size, max_party_size FROM restaurant_capacity_windows WHERE id = $1",
                int(current["capacity_window_id"]),
            )
            if window is not None:
                next_min = update.min_party_size if update.min_party_size is not None else int(window["min_party_size"] or 1)
                next_max = update.max_party_size if update.max_party_size is not None else int(window["max_party_size"] or 8)
                if next_max < next_min:
                    raise ValueError("invalid_party_size_range")
                if update.reservation_limit is not None and int(update.reservation_limit) < int(window["booked_reservations"] or 0):
                    raise ValueError("reservation_limit_below_booked_count")
                if update.total_party_size_limit is not None:
                    booked_party_size = int((await fetchrow("SELECT booked_party_size FROM restaurant_capacity_windows WHERE id = $1", int(current["capacity_window_id"]))) ["booked_party_size"] or 0)
                    if int(update.total_party_size_limit) < booked_party_size:
                        raise ValueError("party_size_limit_below_booked_total")
                await execute(
                    """
                    UPDATE restaurant_capacity_windows
                    SET reservation_limit = COALESCE($2, reservation_limit),
                        total_party_size_limit = COALESCE($3, total_party_size_limit),
                        min_party_size = COALESCE($4, min_party_size),
                        max_party_size = COALESCE($5, max_party_size),
                        is_active = COALESCE($6, is_active)
                    WHERE id = $1
                    """,
                    int(current["capacity_window_id"]),
                    update.reservation_limit if update.reservation_limit is not None else update.total_capacity,
                    update.total_party_size_limit,
                    update.min_party_size,
                    update.max_party_size,
                    update.is_active,
                )

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
            update.total_capacity if update.total_capacity is not None else update.reservation_limit,
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
            table_id=row.get("table_id"),
            table_type=row.get("table_type"),
            arrived_at=row.get("arrived_at"),
            no_show_at=row.get("no_show_at"),
            extended_minutes=int(row.get("extended_minutes") or 0),
            created_at=row["created_at"],
        )
