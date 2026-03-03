"""Repository for restaurant holds and restaurant slots."""

from datetime import date, time

import asyncpg
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.restaurant import RestaurantHold, RestaurantSlot
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class RestaurantRepository:
    """CRUD operations for restaurant_holds and restaurant_slots tables."""

    async def create_hold(self, hold: RestaurantHold) -> RestaurantHold:
        """Insert a new restaurant hold."""
        hold.hold_id = await next_sequential_id("R_HOLD_", "restaurant_holds", "hold_id")

        row = await fetchrow(
            """
            INSERT INTO restaurant_holds
                (hold_id, hotel_id, conversation_id, slot_id, date, time, party_size,
                 guest_name, phone, area, notes, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id, created_at, updated_at
            """,
            hold.hold_id,
            hold.hotel_id,
            hold.conversation_id,
            hold.slot_id,
            hold.date,
            hold.time,
            hold.party_size,
            hold.guest_name,
            hold.phone,
            hold.area,
            hold.notes,
            hold.status.value,
        )
        if row is None:
            raise RuntimeError("Failed to create restaurant hold.")

        hold.id = row["id"]
        hold.created_at = row["created_at"]
        return hold

    async def get_by_hold_id(self, hold_id: str) -> RestaurantHold | None:
        """Fetch a restaurant hold by hold_id."""
        row = await fetchrow("SELECT * FROM restaurant_holds WHERE hold_id = $1", hold_id)
        if row is None:
            return None
        return self._row_to_hold(row)

    async def update_status(
        self,
        hold_id: str,
        status: str,
        approved_by: str | None = None,
        rejected_reason: str | None = None,
    ) -> None:
        """Update restaurant hold status."""
        await execute(
            """
            UPDATE restaurant_holds
            SET status = $2,
                approved_by = COALESCE($3, approved_by),
                approved_at = CASE WHEN $2 = 'APPROVED' OR $2 = 'CONFIRMED' THEN now() ELSE approved_at END,
                rejected_reason = COALESCE($4, rejected_reason),
                updated_at = now()
            WHERE hold_id = $1
            """,
            hold_id,
            status,
            approved_by,
            rejected_reason,
        )

    async def get_holds_by_date(self, hotel_id: int, target_date: date) -> list[RestaurantHold]:
        """Get all restaurant holds for a specific date."""
        rows = await fetch(
            "SELECT * FROM restaurant_holds WHERE hotel_id = $1 AND date = $2 ORDER BY time ASC",
            hotel_id,
            target_date,
        )
        return [self._row_to_hold(row) for row in rows]

    async def get_available_slots(
        self,
        hotel_id: int,
        target_date: date,
        target_time: time,
        party_size: int,
        area: str | None = None,
    ) -> list[RestaurantSlot]:
        """Find available slots that can accommodate the party size."""
        if area:
            rows = await fetch(
                """
                SELECT id AS slot_id, time, (total_capacity - booked_count) AS capacity_left
                FROM restaurant_slots
                WHERE hotel_id = $1 AND date = $2 AND is_active = true
                  AND (total_capacity - booked_count) >= $3
                  AND area = $4
                ORDER BY ABS(EXTRACT(EPOCH FROM (time - $5))) ASC
                """,
                hotel_id,
                target_date,
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
                  AND (total_capacity - booked_count) >= $3
                ORDER BY ABS(EXTRACT(EPOCH FROM (time - $4))) ASC
                """,
                hotel_id,
                target_date,
                party_size,
                target_time,
            )

        return [
            RestaurantSlot(slot_id=str(row["slot_id"]), time=row["time"], capacity_left=row["capacity_left"])
            for row in rows
        ]

    async def increment_booked_count(self, slot_id: int, increment: int = 1) -> None:
        """Increase booked count for a slot."""
        await execute(
            "UPDATE restaurant_slots SET booked_count = booked_count + $2 WHERE id = $1",
            slot_id,
            increment,
        )

    async def decrement_booked_count(self, slot_id: int, decrement: int = 1) -> None:
        """Decrease booked count for a slot."""
        await execute(
            "UPDATE restaurant_slots SET booked_count = GREATEST(0, booked_count - $2) WHERE id = $1",
            slot_id,
            decrement,
        )

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
