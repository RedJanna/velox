# Task 02: Database Models & Repository Layer

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/security_privacy.md`

## Objective
Implement the AsyncPG database connection pool, create the repository layer with CRUD methods for all domain entities, and ensure the migration runs automatically on `docker-compose up`.

## Prerequisites
- Task 01 completed (project setup, dependencies installed)
- PostgreSQL running (via docker-compose or locally on port 5432)
- Redis running (via docker-compose or locally on port 6379)

---

## Step 1: Review the Database Schema

Read and understand the existing migration file at `src/velox/db/migrations/001_initial.sql`. It defines 12 tables:

| Table | Purpose | ID Pattern |
|-------|---------|------------|
| `hotels` | Hotel configuration | SERIAL (auto-increment) |
| `conversations` | WhatsApp conversation sessions | UUID |
| `messages` | Individual messages in conversations | UUID |
| `stay_holds` | Pre-approval stay booking drafts | UUID + `S_HOLD_xxxx` |
| `restaurant_holds` | Pre-approval restaurant booking holds | UUID + `R_HOLD_xxxx` |
| `transfer_holds` | Pre-approval transfer booking holds | UUID + `TR_HOLD_xxxx` |
| `approval_requests` | Approval workflow records | UUID + `APR_xxxx` |
| `payment_requests` | Payment tracking records | UUID + `PAY_xxxx` |
| `tickets` | Human handoff tickets | UUID + `T_xxxx` |
| `notifications` | Notification records | UUID + `N_xxxx` |
| `crm_logs` | CRM event logging | UUID |
| `restaurant_slots` | Restaurant capacity management | SERIAL |
| `admin_users` | Admin panel users | SERIAL |

**Source file**: `src/velox/db/migrations/001_initial.sql`

---

## Step 2: Implement Database Connection Pool

Create `src/velox/db/database.py`:

```python
"""AsyncPG database connection pool manager."""

import asyncpg
import structlog
from velox.config.settings import settings

logger = structlog.get_logger(__name__)

# Module-level pool reference
_pool: asyncpg.Pool | None = None


async def init_db_pool() -> asyncpg.Pool:
    """Initialize the asyncpg connection pool. Call once at app startup."""
    global _pool
    if _pool is not None:
        return _pool

    logger.info(
        "Initializing database pool",
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
    )

    _pool = await asyncpg.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        command_timeout=30,
    )
    logger.info("Database pool initialized")
    return _pool


async def close_db_pool() -> None:
    """Close the asyncpg connection pool. Call once at app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


def get_pool() -> asyncpg.Pool:
    """Get the current connection pool. Raises RuntimeError if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _pool


async def execute(query: str, *args: object) -> str:
    """Execute a query that does not return rows (INSERT/UPDATE/DELETE)."""
    pool = get_pool()
    return await pool.execute(query, *args)


async def fetch(query: str, *args: object) -> list[asyncpg.Record]:
    """Execute a query and return all result rows."""
    pool = get_pool()
    return await pool.fetch(query, *args)


async def fetchrow(query: str, *args: object) -> asyncpg.Record | None:
    """Execute a query and return a single row or None."""
    pool = get_pool()
    return await pool.fetchrow(query, *args)


async def fetchval(query: str, *args: object) -> object:
    """Execute a query and return a single value."""
    pool = get_pool()
    return await pool.fetchval(query, *args)
```

**File to create**: `src/velox/db/database.py`

---

## Step 3: Implement ID Generation Utility

Create `src/velox/utils/id_gen.py`:

```python
"""Sequential and unique ID generation for domain entities."""

from velox.db.database import fetchval


async def next_sequential_id(prefix: str, table: str, column: str) -> str:
    """
    Generate the next sequential ID with the given prefix.

    Examples:
        next_sequential_id("S_HOLD_", "stay_holds", "hold_id") -> "S_HOLD_001"
        next_sequential_id("R_HOLD_", "restaurant_holds", "hold_id") -> "R_HOLD_001"
        next_sequential_id("TR_HOLD_", "transfer_holds", "hold_id") -> "TR_HOLD_001"
        next_sequential_id("APR_", "approval_requests", "request_id") -> "APR_001"
        next_sequential_id("PAY_", "payment_requests", "request_id") -> "PAY_001"
        next_sequential_id("T_", "tickets", "ticket_id") -> "T_001"
        next_sequential_id("N_", "notifications", "notification_id") -> "N_001"
    """
    # Count existing rows to determine the next number
    query = f"SELECT COUNT(*) FROM {table}"  # noqa: S608
    count = await fetchval(query)
    next_num = (count or 0) + 1
    return f"{prefix}{next_num:03d}"
```

**Important ID patterns** (from the master spec):
- Stay holds: `S_HOLD_001`, `S_HOLD_002`, ...
- Restaurant holds: `R_HOLD_001`, `R_HOLD_002`, ...
- Transfer holds: `TR_HOLD_001`, `TR_HOLD_002`, ...
- Approval requests: `APR_001`, `APR_002`, ...
- Payment requests: `PAY_001`, `PAY_002`, ...
- Tickets: `T_001`, `T_002`, ...
- Notifications: `N_001`, `N_002`, ...

**File to create**: `src/velox/utils/id_gen.py`

---

## Step 4: Implement Repository — Conversation

Create `src/velox/db/repositories/conversation.py`:

```python
"""Repository for conversations and messages."""

from datetime import datetime
from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.conversation import Conversation, Message

logger = structlog.get_logger(__name__)


class ConversationRepository:
    """CRUD operations for conversations and messages."""

    # ---- Conversation CRUD ----

    async def create(self, conv: Conversation) -> Conversation:
        """Insert a new conversation. Returns the conversation with its generated UUID."""
        row = await fetchrow(
            """
            INSERT INTO conversations (hotel_id, phone_hash, phone_display, language,
                                       current_state, current_intent, entities_json, risk_flags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, created_at, updated_at
            """,
            conv.hotel_id,
            conv.phone_hash,
            conv.phone_display,
            conv.language,
            str(conv.current_state),
            str(conv.current_intent) if conv.current_intent else None,
            orjson.dumps(conv.entities_json).decode(),
            conv.risk_flags,
        )
        conv.id = row["id"]
        conv.created_at = row["created_at"]
        return conv

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Fetch a conversation by UUID."""
        row = await fetchrow(
            "SELECT * FROM conversations WHERE id = $1",
            conversation_id,
        )
        if row is None:
            return None
        return self._row_to_conversation(row)

    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        """Find the active conversation for a phone number at a specific hotel."""
        row = await fetchrow(
            """
            SELECT * FROM conversations
            WHERE hotel_id = $1 AND phone_hash = $2 AND is_active = true
            ORDER BY last_message_at DESC
            LIMIT 1
            """,
            hotel_id,
            phone_hash,
        )
        if row is None:
            return None
        return self._row_to_conversation(row)

    async def update_state(
        self,
        conversation_id: UUID,
        state: str,
        intent: str | None = None,
        entities: dict | None = None,
        risk_flags: list[str] | None = None,
    ) -> None:
        """Update conversation state, intent, entities, and risk flags."""
        await execute(
            """
            UPDATE conversations
            SET current_state = $2,
                current_intent = COALESCE($3, current_intent),
                entities_json = COALESCE($4, entities_json),
                risk_flags = COALESCE($5, risk_flags),
                last_message_at = now(),
                updated_at = now()
            WHERE id = $1
            """,
            conversation_id,
            state,
            intent,
            orjson.dumps(entities).decode() if entities else None,
            risk_flags,
        )

    async def close(self, conversation_id: UUID) -> None:
        """Mark a conversation as inactive (closed)."""
        await execute(
            """
            UPDATE conversations SET is_active = false, current_state = 'CLOSED', updated_at = now()
            WHERE id = $1
            """,
            conversation_id,
        )

    # ---- Message CRUD ----

    async def add_message(self, msg: Message) -> Message:
        """Insert a new message into a conversation."""
        row = await fetchrow(
            """
            INSERT INTO messages (conversation_id, role, content, internal_json, tool_calls)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at
            """,
            msg.conversation_id,
            msg.role,
            msg.content,
            orjson.dumps(msg.internal_json).decode() if msg.internal_json else None,
            orjson.dumps(msg.tool_calls).decode() if msg.tool_calls else None,
        )
        msg.id = row["id"]
        msg.created_at = row["created_at"]

        # Update conversation last_message_at
        await execute(
            "UPDATE conversations SET last_message_at = now() WHERE id = $1",
            msg.conversation_id,
        )
        return msg

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Message]:
        """Get messages for a conversation, ordered by creation time (newest last)."""
        rows = await fetch(
            """
            SELECT * FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2 OFFSET $3
            """,
            conversation_id,
            limit,
            offset,
        )
        return [self._row_to_message(row) for row in rows]

    async def get_recent_messages(self, conversation_id: UUID, count: int = 20) -> list[Message]:
        """Get the last N messages for a conversation (for LLM context window)."""
        rows = await fetch(
            """
            SELECT * FROM (
                SELECT * FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ) sub
            ORDER BY created_at ASC
            """,
            conversation_id,
            count,
        )
        return [self._row_to_message(row) for row in rows]

    # ---- Helpers ----

    @staticmethod
    def _row_to_conversation(row: asyncpg.Record) -> Conversation:
        return Conversation(
            id=row["id"],
            hotel_id=row["hotel_id"],
            phone_hash=row["phone_hash"],
            phone_display=row["phone_display"],
            language=row["language"],
            current_state=row["current_state"],
            current_intent=row["current_intent"],
            entities_json=orjson.loads(row["entities_json"]) if row["entities_json"] else {},
            risk_flags=list(row["risk_flags"]) if row["risk_flags"] else [],
            is_active=row["is_active"],
            last_message_at=row["last_message_at"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_message(row: asyncpg.Record) -> Message:
        return Message(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            internal_json=orjson.loads(row["internal_json"]) if row["internal_json"] else None,
            tool_calls=orjson.loads(row["tool_calls"]) if row["tool_calls"] else None,
            created_at=row["created_at"],
        )
```

**File to create**: `src/velox/db/repositories/conversation.py`

---

## Step 5: Implement Repository — Reservation (Stay Holds)

Create `src/velox/db/repositories/reservation.py`:

```python
"""Repository for stay holds and related reservation data."""

from datetime import datetime
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
        """Insert a new stay hold. Generates the hold_id automatically."""
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
            str(hold.status),
        )
        hold.id = row["id"]
        hold.created_at = row["created_at"]
        return hold

    async def get_by_hold_id(self, hold_id: str) -> StayHold | None:
        """Fetch a stay hold by its hold_id (e.g., S_HOLD_001)."""
        row = await fetchrow("SELECT * FROM stay_holds WHERE hold_id = $1", hold_id)
        if row is None:
            return None
        return self._row_to_hold(row)

    async def get_by_id(self, uuid: UUID) -> StayHold | None:
        """Fetch a stay hold by its UUID."""
        row = await fetchrow("SELECT * FROM stay_holds WHERE id = $1", uuid)
        if row is None:
            return None
        return self._row_to_hold(row)

    async def get_by_hotel_and_status(self, hotel_id: int, status: str) -> list[StayHold]:
        """Get all stay holds for a hotel filtered by status."""
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
        """Update the status of a stay hold (approve, reject, confirm)."""
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
```

**File to create**: `src/velox/db/repositories/reservation.py`

---

## Step 6: Implement Repository — Restaurant

Create `src/velox/db/repositories/restaurant.py`:

```python
"""Repository for restaurant holds and restaurant slots."""

from datetime import date, time
from uuid import UUID

import asyncpg
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.restaurant import RestaurantHold, RestaurantSlot
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class RestaurantRepository:
    """CRUD operations for restaurant_holds and restaurant_slots tables."""

    # ---- Restaurant Holds ----

    async def create_hold(self, hold: RestaurantHold) -> RestaurantHold:
        """Insert a new restaurant hold. Generates hold_id automatically."""
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
            str(hold.status),
        )
        hold.id = row["id"]
        hold.created_at = row["created_at"]
        return hold

    async def get_by_hold_id(self, hold_id: str) -> RestaurantHold | None:
        """Fetch a restaurant hold by its hold_id (e.g., R_HOLD_001)."""
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
        """Get all restaurant holds for a hotel on a specific date."""
        rows = await fetch(
            "SELECT * FROM restaurant_holds WHERE hotel_id = $1 AND date = $2 ORDER BY time ASC",
            hotel_id,
            target_date,
        )
        return [self._row_to_hold(row) for row in rows]

    # ---- Restaurant Slots ----

    async def get_available_slots(
        self,
        hotel_id: int,
        target_date: date,
        target_time: time,
        party_size: int,
        area: str | None = None,
    ) -> list[RestaurantSlot]:
        """Find available restaurant slots that can accommodate the party size."""
        query = """
            SELECT id AS slot_id, time, (total_capacity - booked_count) AS capacity_left
            FROM restaurant_slots
            WHERE hotel_id = $1 AND date = $2 AND is_active = true
              AND (total_capacity - booked_count) >= $3
        """
        params: list[object] = [hotel_id, target_date, party_size]

        if area:
            query += " AND area = $4"
            params.append(area)

        # Filter by time proximity (within 1 hour window)
        query += " ORDER BY ABS(EXTRACT(EPOCH FROM (time - $" + str(len(params) + 1) + "))) ASC"
        params.append(target_time)

        rows = await fetch(query, *params)
        return [
            RestaurantSlot(
                slot_id=str(row["slot_id"]),
                time=row["time"],
                capacity_left=row["capacity_left"],
            )
            for row in rows
        ]

    async def increment_booked_count(self, slot_id: int, increment: int = 1) -> None:
        """Increase the booked count for a slot (when a hold is created)."""
        await execute(
            "UPDATE restaurant_slots SET booked_count = booked_count + $2 WHERE id = $1",
            slot_id,
            increment,
        )

    async def decrement_booked_count(self, slot_id: int, decrement: int = 1) -> None:
        """Decrease the booked count for a slot (when a hold is cancelled)."""
        await execute(
            "UPDATE restaurant_slots SET booked_count = GREATEST(0, booked_count - $2) WHERE id = $1",
            slot_id,
            decrement,
        )

    @staticmethod
    def _row_to_hold(row: asyncpg.Record) -> RestaurantHold:
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
```

**File to create**: `src/velox/db/repositories/restaurant.py`

---

## Step 7: Implement Repository — Transfer

Create `src/velox/db/repositories/transfer.py`:

```python
"""Repository for transfer holds."""

from datetime import date
from uuid import UUID

import asyncpg
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.transfer import TransferHold
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class TransferRepository:
    """CRUD operations for transfer_holds table."""

    async def create_hold(self, hold: TransferHold) -> TransferHold:
        """Insert a new transfer hold. Generates hold_id automatically."""
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
            str(hold.status),
        )
        hold.id = row["id"]
        hold.created_at = row["created_at"]
        return hold

    async def get_by_hold_id(self, hold_id: str) -> TransferHold | None:
        """Fetch a transfer hold by its hold_id (e.g., TR_HOLD_001)."""
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
        """Get all transfer holds for a hotel on a specific date."""
        rows = await fetch(
            "SELECT * FROM transfer_holds WHERE hotel_id = $1 AND date = $2 ORDER BY time ASC",
            hotel_id,
            target_date,
        )
        return [self._row_to_hold(row) for row in rows]

    @staticmethod
    def _row_to_hold(row: asyncpg.Record) -> TransferHold:
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
```

**File to create**: `src/velox/db/repositories/transfer.py`

---

## Step 8: Implement Repository — Hotel

Create `src/velox/db/repositories/hotel.py`:

```python
"""Repository for hotels, approval_requests, payment_requests, tickets, notifications, crm_logs, admin_users."""

from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.utils.id_gen import next_sequential_id

logger = structlog.get_logger(__name__)


class HotelRepository:
    """CRUD operations for the hotels table."""

    async def get_by_hotel_id(self, hotel_id: int) -> asyncpg.Record | None:
        return await fetchrow("SELECT * FROM hotels WHERE hotel_id = $1", hotel_id)

    async def upsert(
        self,
        hotel_id: int,
        name_tr: str,
        name_en: str,
        profile_json: dict,
        **kwargs: object,
    ) -> asyncpg.Record:
        """Insert or update a hotel record."""
        row = await fetchrow(
            """
            INSERT INTO hotels (hotel_id, name_tr, name_en, profile_json,
                                hotel_type, timezone, currency_base, pms, whatsapp_number,
                                season_open, season_close)
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
    ) -> dict:
        request_id = await next_sequential_id("APR_", "approval_requests", "request_id")
        row = await fetchrow(
            """
            INSERT INTO approval_requests (request_id, hotel_id, approval_type, reference_id,
                                           details_summary, required_roles, any_of)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING request_id, status, created_at
            """,
            request_id, hotel_id, approval_type, reference_id,
            details_summary, required_roles, any_of,
        )
        return {"approval_request_id": row["request_id"], "status": row["status"]}

    async def get_by_request_id(self, request_id: str) -> asyncpg.Record | None:
        return await fetchrow("SELECT * FROM approval_requests WHERE request_id = $1", request_id)

    async def update_decision(
        self, request_id: str, approved: bool, decided_by_role: str, decided_by_name: str
    ) -> None:
        status = "APPROVED" if approved else "REJECTED"
        await execute(
            """
            UPDATE approval_requests
            SET status = $2, decided_by_role = $3, decided_by_name = $4, decided_at = now()
            WHERE request_id = $1
            """,
            request_id, status, decided_by_role, decided_by_name,
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
        scheduled_date: object = None,
    ) -> dict:
        request_id = await next_sequential_id("PAY_", "payment_requests", "request_id")
        row = await fetchrow(
            """
            INSERT INTO payment_requests (request_id, hotel_id, reference_id, amount,
                                          currency, methods, due_mode, scheduled_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING request_id, status, handled_by, created_at
            """,
            request_id, hotel_id, reference_id, amount,
            currency, methods, due_mode, scheduled_date,
        )
        return {
            "payment_request_id": row["request_id"],
            "status": row["status"],
            "handled_by": row["handled_by"],
        }

    async def update_status(self, request_id: str, status: str) -> None:
        paid_at_clause = "paid_at = CASE WHEN $2 = 'PAID' THEN now() ELSE paid_at END,"
        await execute(
            f"UPDATE payment_requests SET status = $2, {paid_at_clause} WHERE request_id = $1",  # noqa: S608
            request_id, status,
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
    ) -> dict:
        # Dedupe check: if an open ticket with the same dedupe_key exists, return it
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
            ticket_id, hotel_id, conversation_id, reason,
            transcript_summary, priority, assigned_to_role, dedupe_key,
        )
        return {"ticket_id": row["ticket_id"], "status": row["status"]}

    async def update_status(self, ticket_id: str, status: str) -> None:
        resolved = "resolved_at = CASE WHEN $2 = 'RESOLVED' THEN now() ELSE resolved_at END,"
        await execute(
            f"UPDATE tickets SET status = $2, {resolved} updated_at = now() WHERE ticket_id = $1",  # noqa: S608
            ticket_id, status,
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
    ) -> dict:
        notification_id = await next_sequential_id("N_", "notifications", "notification_id")
        row = await fetchrow(
            """
            INSERT INTO notifications (notification_id, hotel_id, to_role, channel, message, metadata_json)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING notification_id, status, created_at
            """,
            notification_id, hotel_id, to_role, channel, message,
            orjson.dumps(metadata_json).decode() if metadata_json else "{}",
        )
        return {"notification_id": row["notification_id"], "status": row["status"]}


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
    ) -> dict:
        await execute(
            """
            INSERT INTO crm_logs (hotel_id, conversation_id, user_phone_hash, intent,
                                  entities_json, actions, outcome, transcript_summary)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            hotel_id, conversation_id, user_phone_hash, intent,
            orjson.dumps(entities).decode(), actions, outcome, transcript_summary,
        )
        return {"ok": True}
```

**File to create**: `src/velox/db/repositories/hotel.py`

---

## Step 9: Wire Up Database in main.py

Modify `src/velox/main.py` to initialize and close the database pool in the lifespan:

```python
from velox.db.database import init_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    setup_logging()
    await init_db_pool()
    # TODO: Initialize Redis connection
    # TODO: Load hotel profiles from YAML
    # TODO: Load escalation matrix
    yield
    # Shutdown
    await close_db_pool()
    # TODO: Close Redis connection
```

**File to modify**: `src/velox/main.py`

---

## Step 10: Verify Migration Runs on docker-compose up

The `docker-compose.yml` already mounts migrations into PostgreSQL's init directory:
```yaml
volumes:
  - ./src/velox/db/migrations:/docker-entrypoint-initdb.d
```

This means `001_initial.sql` runs automatically when the PostgreSQL container starts for the first time. To verify:

1. Remove any existing data volume:
   ```bash
   docker-compose down -v
   ```
2. Start fresh:
   ```bash
   docker-compose up -d db
   ```
3. Connect and verify tables exist:
   ```bash
   docker exec -it $(docker-compose ps -q db) psql -U velox -d velox -c "\dt"
   ```
4. Expected output should list all 12+ tables defined in `001_initial.sql`.

---

## Verification Checklist

- [ ] `src/velox/db/database.py` exists with `init_db_pool()`, `close_db_pool()`, `get_pool()`, `execute()`, `fetch()`, `fetchrow()`, `fetchval()`
- [ ] `src/velox/utils/id_gen.py` exists with `next_sequential_id()` function
- [ ] `src/velox/db/repositories/conversation.py` exists with `ConversationRepository` class
- [ ] `src/velox/db/repositories/reservation.py` exists with `ReservationRepository` class
- [ ] `src/velox/db/repositories/restaurant.py` exists with `RestaurantRepository` class
- [ ] `src/velox/db/repositories/transfer.py` exists with `TransferRepository` class
- [ ] `src/velox/db/repositories/hotel.py` exists with `HotelRepository`, `ApprovalRequestRepository`, `PaymentRequestRepository`, `TicketRepository`, `NotificationRepository`, `CrmLogRepository` classes
- [ ] `docker-compose up -d db` creates all tables from `001_initial.sql`
- [ ] App starts with `uvicorn velox.main:app` and initializes the DB pool
- [ ] Each repository can insert and fetch records (test with a simple script or unit test)

---

## Files Created in This Task
| File | Purpose |
|------|---------|
| `src/velox/db/database.py` | AsyncPG connection pool manager |
| `src/velox/utils/id_gen.py` | Sequential ID generation |
| `src/velox/db/repositories/conversation.py` | Conversation & message CRUD |
| `src/velox/db/repositories/reservation.py` | Stay hold CRUD |
| `src/velox/db/repositories/restaurant.py` | Restaurant hold & slot CRUD |
| `src/velox/db/repositories/transfer.py` | Transfer hold CRUD |
| `src/velox/db/repositories/hotel.py` | Hotel, approval, payment, ticket, notification, CRM CRUD |

## Files Modified in This Task
| File | Change |
|------|--------|
| `src/velox/main.py` | Add `init_db_pool()` / `close_db_pool()` to lifespan |
