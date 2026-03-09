"""Repository for conversations and messages."""

from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.models.conversation import Conversation, Message

logger = structlog.get_logger(__name__)


class ConversationRepository:
    """CRUD operations for conversations and messages."""

    async def create(self, conv: Conversation) -> Conversation:
        """Insert a new conversation."""
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
            conv.current_state.value,
            conv.current_intent.value if conv.current_intent else None,
            orjson.dumps(conv.entities_json).decode(),
            conv.risk_flags,
        )
        if row is None:
            raise RuntimeError("Failed to create conversation.")

        conv.id = row["id"]
        conv.created_at = row["created_at"]
        return conv

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Fetch a conversation by UUID."""
        row = await fetchrow("SELECT * FROM conversations WHERE id = $1", conversation_id)
        if row is None:
            return None
        return self._row_to_conversation(row)

    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        """Find active conversation for a phone hash at a specific hotel."""
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
        """Update state, intent, entities, and risk flags for a conversation."""
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
        """Mark a conversation as inactive."""
        await execute(
            """
            UPDATE conversations
            SET is_active = false, current_state = 'CLOSED', updated_at = now()
            WHERE id = $1
            """,
            conversation_id,
        )

    async def update_language(self, conversation_id: UUID, language: str) -> None:
        """Update conversation language preference."""
        await execute(
            """
            UPDATE conversations
            SET language = $2, updated_at = now()
            WHERE id = $1
            """,
            conversation_id,
            language,
        )

    async def add_message(self, msg: Message) -> Message:
        """Insert a message into a conversation."""
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
        if row is None:
            raise RuntimeError("Failed to create message.")

        msg.id = row["id"]
        msg.created_at = row["created_at"]

        await execute(
            "UPDATE conversations SET last_message_at = now(), updated_at = now() WHERE id = $1",
            msg.conversation_id,
        )
        return msg

    async def get_messages(self, conversation_id: UUID, limit: int = 20, offset: int = 0) -> list[Message]:
        """Get conversation messages ordered by created_at ascending."""
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
        """Get last N messages ordered ascending (context-ready)."""
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

    @staticmethod
    def _row_to_conversation(row: asyncpg.Record) -> Conversation:
        """Map asyncpg row to Conversation model."""
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
        """Map asyncpg row to Message model."""
        return Message(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            internal_json=orjson.loads(row["internal_json"]) if row["internal_json"] else None,
            tool_calls=orjson.loads(row["tool_calls"]) if row["tool_calls"] else None,
            created_at=row["created_at"],
        )
