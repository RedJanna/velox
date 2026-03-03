"""Repository for transfer holds."""

from datetime import date

import asyncpg
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.transfer import TransferHold
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class TransferRepository:
    """CRUD operations for transfer_holds table."""

    async def create_hold(self, hold: TransferHold) -> TransferHold:
        """Insert a new transfer hold."""
        hold.hold_id = await next_sequential_id("TR_HOLD_", "transfer_holds", "hold_id")

        row = await fetchrow(
            """
            INSERT INTO transfer_holds
                (hold_id, hotel_id, conversation_id, route, date, time, pax_count,
                 guest_name, phone, flight_no, vehicle_type, baby_seat, price_eur, notes, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
            RETURNING id, created_at, updated_at
            """,
            hold.hold_id,
            hold.hotel_id,
            hold.conversation_id,
            hold.route,
            hold.date,
            hold.time,
            hold.pax_count,
            hold.guest_name,
            hold.phone,
            hold.flight_no,
            hold.vehicle_type,
            hold.baby_seat,
            hold.price_eur,
            hold.notes,
            hold.status.value,
        )
        if row is None:
            raise RuntimeError("Failed to create transfer hold.")

        hold.id = row["id"]
        hold.created_at = row["created_at"]
        return hold

    async def get_by_hold_id(self, hold_id: str) -> TransferHold | None:
        """Fetch a transfer hold by hold_id."""
        row = await fetchrow("SELECT * FROM transfer_holds WHERE hold_id = $1", hold_id)
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
        """Update transfer hold status."""
        await execute(
            """
            UPDATE transfer_holds
            SET status = $2,
                approved_by = COALESCE($3, approved_by),
                approved_at = CASE WHEN $2 IN ('APPROVED','CONFIRMED') THEN now() ELSE approved_at END,
                rejected_reason = COALESCE($4, rejected_reason),
                updated_at = now()
            WHERE hold_id = $1
            """,
            hold_id,
            status,
            approved_by,
            rejected_reason,
        )

    async def get_holds_by_date(self, hotel_id: int, target_date: date) -> list[TransferHold]:
        """Get all transfer holds for a specific date."""
        rows = await fetch(
            "SELECT * FROM transfer_holds WHERE hotel_id = $1 AND date = $2 ORDER BY time ASC",
            hotel_id,
            target_date,
        )
        return [self._row_to_hold(row) for row in rows]

    @staticmethod
    def _row_to_hold(row: asyncpg.Record) -> TransferHold:
        """Map asyncpg row to TransferHold model."""
        return TransferHold(
            id=row["id"],
            hold_id=row["hold_id"],
            hotel_id=row["hotel_id"],
            conversation_id=row["conversation_id"],
            route=row["route"],
            date=row["date"],
            time=row["time"],
            pax_count=row["pax_count"],
            guest_name=row["guest_name"],
            phone=row["phone"],
            flight_no=row["flight_no"],
            vehicle_type=row["vehicle_type"],
            baby_seat=row["baby_seat"],
            price_eur=row["price_eur"],
            notes=row["notes"],
            status=row["status"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            rejected_reason=row["rejected_reason"],
            created_at=row["created_at"],
        )
