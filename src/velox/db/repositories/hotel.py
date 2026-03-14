"""Repository for hotel and operational entities."""

from datetime import date
from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class HotelRepository:
    """CRUD operations for hotels table."""

    async def get_by_hotel_id(self, hotel_id: int) -> asyncpg.Record | None:
        """Fetch a hotel by its PMS hotel_id."""
        return await fetchrow("SELECT * FROM hotels WHERE hotel_id = $1", hotel_id)

    async def upsert(
        self,
        hotel_id: int,
        name_tr: str,
        name_en: str,
        profile_json: dict,
        **kwargs: object,
    ) -> asyncpg.Record:
        """Insert or update a hotel row."""
        row = await fetchrow(
            """
            INSERT INTO hotels (
                hotel_id, name_tr, name_en, profile_json, hotel_type, timezone,
                currency_base, pms, whatsapp_number, season_open, season_close
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (hotel_id) DO UPDATE SET
                name_tr = EXCLUDED.name_tr,
                name_en = EXCLUDED.name_en,
                profile_json = EXCLUDED.profile_json,
                updated_at = now()
            RETURNING *
            """,
            hotel_id,
            name_tr,
            name_en,
            orjson.dumps(profile_json).decode(),
            kwargs.get("hotel_type", "boutique"),
            kwargs.get("timezone", "Europe/Istanbul"),
            kwargs.get("currency_base", "EUR"),
            kwargs.get("pms", "elektraweb"),
            kwargs.get("whatsapp_number"),
            kwargs.get("season_open"),
            kwargs.get("season_close"),
        )
        if row is None:
            raise RuntimeError("Failed to upsert hotel.")
        return row


class ApprovalRequestRepository:
    """CRUD operations for approval_requests table."""

    async def create(
        self,
        hotel_id: int,
        approval_type: str,
        reference_id: str,
        details_summary: str,
        required_roles: list[str],
        any_of: bool = False,
    ) -> dict[str, str]:
        """Create an approval request."""
        request_id = await next_sequential_id("APR_", "approval_requests", "request_id")
        row = await fetchrow(
            """
            INSERT INTO approval_requests (request_id, hotel_id, approval_type, reference_id,
                                           details_summary, required_roles, any_of)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING request_id, status, created_at
            """,
            request_id,
            hotel_id,
            approval_type,
            reference_id,
            details_summary,
            required_roles,
            any_of,
        )
        if row is None:
            raise RuntimeError("Failed to create approval request.")
        return {"approval_request_id": row["request_id"], "status": row["status"]}

    async def get_by_request_id(self, request_id: str) -> asyncpg.Record | None:
        """Fetch approval request by request_id."""
        return await fetchrow("SELECT * FROM approval_requests WHERE request_id = $1", request_id)

    async def update_decision(
        self,
        request_id: str,
        approved: bool,
        decided_by_role: str,
        decided_by_name: str,
    ) -> None:
        """Update approval request decision."""
        status = "APPROVED" if approved else "REJECTED"
        await execute(
            """
            UPDATE approval_requests
            SET status = $2, decided_by_role = $3, decided_by_name = $4, decided_at = now()
            WHERE request_id = $1
            """,
            request_id,
            status,
            decided_by_role,
            decided_by_name,
        )


class PaymentRequestRepository:
    """CRUD operations for payment_requests table."""

    async def create(
        self,
        hotel_id: int,
        reference_id: str,
        amount: float,
        currency: str,
        methods: list[str],
        due_mode: str,
        scheduled_date: date | None = None,
    ) -> dict[str, str]:
        """Create a payment request."""
        request_id = await next_sequential_id("PAY_", "payment_requests", "request_id")
        row = await fetchrow(
            """
            INSERT INTO payment_requests (request_id, hotel_id, reference_id, amount,
                                          currency, methods, due_mode, scheduled_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING request_id, status, handled_by, created_at
            """,
            request_id,
            hotel_id,
            reference_id,
            amount,
            currency,
            methods,
            due_mode,
            scheduled_date,
        )
        if row is None:
            raise RuntimeError("Failed to create payment request.")
        return {
            "payment_request_id": row["request_id"],
            "status": row["status"],
            "handled_by": row["handled_by"],
        }

    async def update_status(self, request_id: str, status: str) -> None:
        """Update payment request status."""
        await execute(
            """
            UPDATE payment_requests
            SET status = $2,
                paid_at = CASE WHEN $2 = 'PAID' THEN now() ELSE paid_at END
            WHERE request_id = $1
            """,
            request_id,
            status,
        )


class TicketRepository:
    """CRUD operations for tickets table."""

    async def create(
        self,
        hotel_id: int,
        conversation_id: UUID | None,
        reason: str,
        transcript_summary: str,
        priority: str = "medium",
        assigned_to_role: str | None = None,
        dedupe_key: str | None = None,
    ) -> dict[str, str | bool]:
        """Create a ticket, deduplicating open tickets with same dedupe key."""
        if dedupe_key:
            existing = await fetchrow(
                """
                SELECT ticket_id, status FROM tickets
                WHERE dedupe_key = $1 AND status NOT IN ('RESOLVED', 'CLOSED')
                """,
                dedupe_key,
            )
            if existing:
                return {"ticket_id": existing["ticket_id"], "status": existing["status"], "dedupe": True}

        ticket_id = await next_sequential_id("T_", "tickets", "ticket_id")
        row = await fetchrow(
            """
            INSERT INTO tickets (ticket_id, hotel_id, conversation_id, reason,
                                 transcript_summary, priority, assigned_to_role, dedupe_key)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING ticket_id, status, created_at
            """,
            ticket_id,
            hotel_id,
            conversation_id,
            reason,
            transcript_summary,
            priority,
            assigned_to_role,
            dedupe_key,
        )
        if row is None:
            raise RuntimeError("Failed to create ticket.")
        return {"ticket_id": row["ticket_id"], "status": row["status"]}

    async def update_status(self, ticket_id: str, status: str) -> None:
        """Update ticket status."""
        await execute(
            """
            UPDATE tickets
            SET status = $2,
                resolved_at = CASE WHEN $2 = 'RESOLVED' THEN now() ELSE resolved_at END,
                updated_at = now()
            WHERE ticket_id = $1
            """,
            ticket_id,
            status,
        )


class NotificationRepository:
    """CRUD operations for notifications table."""

    async def create(
        self,
        hotel_id: int,
        to_role: str,
        channel: str,
        message: str,
        metadata_json: dict | None = None,
    ) -> dict[str, str]:
        """Create a notification record."""
        notification_id = await next_sequential_id("N_", "notifications", "notification_id")
        row = await fetchrow(
            """
            INSERT INTO notifications (notification_id, hotel_id, to_role, channel, message, metadata_json)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING notification_id, status, created_at
            """,
            notification_id,
            hotel_id,
            to_role,
            channel,
            message,
            orjson.dumps(metadata_json).decode() if metadata_json else "{}",
        )
        if row is None:
            raise RuntimeError("Failed to create notification.")
        return {"notification_id": row["notification_id"], "status": row["status"]}


class NotificationPhoneRepository:
    """CRUD operations for notification_phones table."""

    DEFAULT_PHONE = "+905304498453"

    async def list_active(self, hotel_id: int) -> list[dict[str, object]]:
        """Return active notification phones for a hotel."""
        rows = await fetch(
            """
            SELECT id, hotel_id, phone, label, is_default, active, created_at
            FROM notification_phones
            WHERE hotel_id = $1 AND active = TRUE
            ORDER BY is_default DESC, created_at
            """,
            hotel_id,
        )
        return [dict(row) for row in rows]

    async def add(self, hotel_id: int, phone: str, label: str = "") -> dict[str, object]:
        """Add a notification phone. Returns existing row on conflict."""
        row = await fetchrow(
            """
            INSERT INTO notification_phones (hotel_id, phone, label)
            VALUES ($1, $2, $3)
            ON CONFLICT (hotel_id, phone) DO UPDATE SET
                active = TRUE, label = EXCLUDED.label, updated_at = now()
            RETURNING id, hotel_id, phone, label, is_default, active, created_at
            """,
            hotel_id,
            phone,
            label,
        )
        if row is None:
            raise RuntimeError("Failed to add notification phone.")
        return dict(row)

    async def remove(self, hotel_id: int, phone: str) -> bool:
        """Soft-delete a notification phone. Default phone cannot be removed."""
        if phone == self.DEFAULT_PHONE:
            raise ValueError("Varsayilan admin numarasi kaldirilAmaz.")
        result = await execute(
            """
            UPDATE notification_phones
            SET active = FALSE, updated_at = now()
            WHERE hotel_id = $1 AND phone = $2 AND is_default = FALSE
            """,
            hotel_id,
            phone,
        )
        return result != "UPDATE 0"

    async def get_active_phones(self, hotel_id: int) -> list[str]:
        """Return only phone strings for active notification recipients."""
        rows = await fetch(
            "SELECT phone FROM notification_phones WHERE hotel_id = $1 AND active = TRUE",
            hotel_id,
        )
        phones = [row["phone"] for row in rows]
        if self.DEFAULT_PHONE not in phones:
            phones.insert(0, self.DEFAULT_PHONE)
        return phones


class CrmLogRepository:
    """CRUD operations for crm_logs table."""

    async def log(
        self,
        hotel_id: int,
        conversation_id: UUID | None,
        user_phone_hash: str,
        intent: str,
        entities: dict,
        actions: list[str],
        outcome: str,
        transcript_summary: str,
    ) -> dict[str, bool]:
        """Create a CRM log entry."""
        await execute(
            """
            INSERT INTO crm_logs (hotel_id, conversation_id, user_phone_hash, intent,
                                  entities_json, actions, outcome, transcript_summary)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            hotel_id,
            conversation_id,
            user_phone_hash,
            intent,
            orjson.dumps(entities).decode(),
            actions,
            outcome,
            transcript_summary,
        )
        return {"ok": True}
