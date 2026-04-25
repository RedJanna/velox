"""Repository for stay holds and related reservation data."""

from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.reservation import ExternalReservationSnapshot, StayHold
from velox.utils.id_gen import next_reservation_no, next_sequential_id

logger = structlog.get_logger(__name__)


class ReservationRepository:
    """CRUD operations for stay_holds table."""

    async def upsert_external_snapshot(self, snapshot: ExternalReservationSnapshot) -> None:
        """Store a minimal PII-safe snapshot from an external PMS reservation lookup."""
        await execute(
            """
            INSERT INTO external_reservation_snapshots (
                hotel_id, lookup_key, pms_reservation_id, voucher_no, phone_hash,
                checkin_date, checkout_date, state, total_price, snapshot_json, source,
                first_seen_at, last_seen_at
            )
            VALUES ($1, $2, $3, $4, $5, $6::date, $7::date, $8, $9, $10::jsonb, $11, now(), now())
            ON CONFLICT (hotel_id, lookup_key)
            DO UPDATE SET
                pms_reservation_id = COALESCE(
                    EXCLUDED.pms_reservation_id,
                    external_reservation_snapshots.pms_reservation_id
                ),
                voucher_no = COALESCE(EXCLUDED.voucher_no, external_reservation_snapshots.voucher_no),
                phone_hash = COALESCE(EXCLUDED.phone_hash, external_reservation_snapshots.phone_hash),
                checkin_date = COALESCE(EXCLUDED.checkin_date, external_reservation_snapshots.checkin_date),
                checkout_date = COALESCE(EXCLUDED.checkout_date, external_reservation_snapshots.checkout_date),
                state = EXCLUDED.state,
                total_price = COALESCE(EXCLUDED.total_price, external_reservation_snapshots.total_price),
                snapshot_json = EXCLUDED.snapshot_json,
                source = EXCLUDED.source,
                last_seen_at = now()
            """,
            snapshot.hotel_id,
            snapshot.lookup_key,
            snapshot.pms_reservation_id,
            snapshot.voucher_no,
            snapshot.phone_hash,
            snapshot.checkin_date,
            snapshot.checkout_date,
            snapshot.state,
            snapshot.total_price,
            orjson.dumps(snapshot.snapshot_json).decode(),
            snapshot.source,
        )

    async def create_hold(self, hold: StayHold) -> StayHold:
        """Insert a new stay hold."""
        hold.hold_id = await next_sequential_id("S_HOLD_", "stay_holds", "hold_id")
        reservation_no: str | None = await next_reservation_no(hold.hotel_id)

        try:
            row = await fetchrow(
                """
                INSERT INTO stay_holds (
                    hold_id, hotel_id, conversation_id, draft_json, status, workflow_state, reservation_no
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, created_at, updated_at
                """,
                hold.hold_id,
                hold.hotel_id,
                hold.conversation_id,
                orjson.dumps(hold.draft_json).decode(),
                hold.status.value,
                hold.workflow_state or hold.status.value,
                reservation_no,
            )
        except asyncpg.UndefinedColumnError:
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
            reservation_no = None
        if row is None:
            raise RuntimeError("Failed to create stay hold.")

        hold.id = row["id"]
        hold.created_at = row["created_at"]
        hold.reservation_no = reservation_no
        return hold

    async def get_by_reservation_no(self, reservation_no: str) -> StayHold | None:
        """Fetch a stay hold by reservation number."""
        row = await fetchrow("SELECT * FROM stay_holds WHERE reservation_no = $1", reservation_no)
        if row is None:
            return None
        return self._row_to_hold(row)

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
        try:
            await execute(
                """
                UPDATE stay_holds
                SET status = $2,
                    workflow_state = $2,
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
        except asyncpg.UndefinedColumnError:
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

    async def update_workflow_metadata(
        self,
        hold_id: str,
        *,
        workflow_state: str | None = None,
        expires_at: str | None = None,
        pms_create_started: bool = False,
        pms_create_completed: bool = False,
        manual_review_reason: str | None = None,
        approval_idempotency_key: str | None = None,
        create_idempotency_key: str | None = None,
    ) -> None:
        """Persist workflow metadata fields on stay hold."""
        try:
            if workflow_state is not None:
                await execute(
                    """
                    UPDATE stay_holds
                    SET workflow_state = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                    workflow_state,
                )
            if expires_at is not None:
                await execute(
                    """
                    UPDATE stay_holds
                    SET expires_at = $2::timestamptz, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                    expires_at,
                )
            if pms_create_started:
                await execute(
                    """
                    UPDATE stay_holds
                    SET pms_create_started_at = now(), updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                )
            if pms_create_completed:
                await execute(
                    """
                    UPDATE stay_holds
                    SET pms_create_completed_at = now(), updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                )
            if manual_review_reason is not None:
                await execute(
                    """
                    UPDATE stay_holds
                    SET manual_review_reason = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                    manual_review_reason,
                )
            if approval_idempotency_key is not None:
                await execute(
                    """
                    UPDATE stay_holds
                    SET approval_idempotency_key = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                    approval_idempotency_key,
                )
            if create_idempotency_key is not None:
                await execute(
                    """
                    UPDATE stay_holds
                    SET create_idempotency_key = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    hold_id,
                    create_idempotency_key,
                )
        except asyncpg.UndefinedColumnError:
            logger.warning("stay_workflow_columns_missing", hold_id=hold_id)

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
            archived_at=row.get("archived_at", None),
            archived_by=row.get("archived_by", None),
            archived_reason=row.get("archived_reason", None),
            workflow_state=row.get("workflow_state", None),
            expires_at=row.get("expires_at", None),
            pms_create_started_at=row.get("pms_create_started_at", None),
            pms_create_completed_at=row.get("pms_create_completed_at", None),
            manual_review_reason=row.get("manual_review_reason", None),
            approval_idempotency_key=row.get("approval_idempotency_key", None),
            create_idempotency_key=row.get("create_idempotency_key", None),
            reservation_no=row.get("reservation_no", None),
            created_at=row["created_at"],
        )
