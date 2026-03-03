"""Repository for stay holds and related reservation data."""

from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.reservation import StayHold
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class ReservationRepository:
    """CRUD operations for stay_holds table."""

    async def create_hold(self, hold: StayHold) -> StayHold:
        """Insert a new stay hold."""
        hold.hold_id = await next_sequential_id("S_HOLD_", "stay_holds", "hold_id")

        row = await fetchrow(
            """
            INSERT INTO stay_holds (hold_id, hotel_id, conversation_id, draft_json, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at, updated_at
            """,
            hold.hold_id,
            hold.hotel_id,
            hold.conversation_id,
            orjson.dumps(hold.draft_json).decode(),
            hold.status.value,
        )
        if row is None:
            raise RuntimeError("Failed to create stay hold.")

        hold.id = row["id"]
        hold.created_at = row["created_at"]
        return hold

    async def get_by_hold_id(self, hold_id: str) -> StayHold | None:
        """Fetch a stay hold by hold_id."""
        row = await fetchrow("SELECT * FROM stay_holds WHERE hold_id = $1", hold_id)
        if row is None:
            return None
        return self._row_to_hold(row)

    async def get_by_id(self, hold_uuid: UUID) -> StayHold | None:
        """Fetch a stay hold by UUID."""
        row = await fetchrow("SELECT * FROM stay_holds WHERE id = $1", hold_uuid)
        if row is None:
            return None
        return self._row_to_hold(row)

    async def get_by_hotel_and_status(self, hotel_id: int, status: str) -> list[StayHold]:
        """Get stay holds for a hotel by status."""
        rows = await fetch(
            "SELECT * FROM stay_holds WHERE hotel_id = $1 AND status = $2 ORDER BY created_at DESC",
            hotel_id,
            status,
        )
        return [self._row_to_hold(row) for row in rows]

    async def update_status(
        self,
        hold_id: str,
        status: str,
        approved_by: str | None = None,
        pms_reservation_id: str | None = None,
        voucher_no: str | None = None,
        rejected_reason: str | None = None,
    ) -> None:
        """Update stay hold status and related approval/booking fields."""
        await execute(
            """
            UPDATE stay_holds
            SET status = $2,
                approved_by = COALESCE($3, approved_by),
                approved_at = CASE WHEN $2 = 'APPROVED' THEN now() ELSE approved_at END,
                pms_reservation_id = COALESCE($4, pms_reservation_id),
                voucher_no = COALESCE($5, voucher_no),
                rejected_reason = COALESCE($6, rejected_reason),
                updated_at = now()
            WHERE hold_id = $1
            """,
            hold_id,
            status,
            approved_by,
            pms_reservation_id,
            voucher_no,
            rejected_reason,
        )

    @staticmethod
    def _row_to_hold(row: asyncpg.Record) -> StayHold:
        """Map asyncpg row to StayHold model."""
        return StayHold(
            id=row["id"],
            hold_id=row["hold_id"],
            hotel_id=row["hotel_id"],
            conversation_id=row["conversation_id"],
            draft_json=orjson.loads(row["draft_json"]) if row["draft_json"] else {},
            status=row["status"],
            pms_reservation_id=row["pms_reservation_id"],
            voucher_no=row["voucher_no"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            rejected_reason=row["rejected_reason"],
            created_at=row["created_at"],
        )
