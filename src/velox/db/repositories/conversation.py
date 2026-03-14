"""Repository for conversations and messages."""

import asyncio
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.config.settings import settings
from velox.db.database import execute, fetch, fetchrow
from velox.models.conversation import Conversation, Message
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)

_TRANSCRIPT_SCHEMA_VERSION = "chat_lab_import.v1"
_TRANSCRIPT_WRITE_LOCK = asyncio.Lock()


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
            INSERT INTO messages (conversation_id, role, content, client_message_id, internal_json, tool_calls)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, created_at
            """,
            msg.conversation_id,
            msg.role,
            msg.content,
            msg.client_message_id,
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
        await self._safe_export_conversation_transcript(msg.conversation_id)
        return msg

    async def export_recent_conversations_for_chat_lab(self, limit: int = 100) -> int:
        """Export latest conversations as masked JSON transcript files for Chat Lab imports."""
        rows = await fetch(
            """
            SELECT id
            FROM conversations
            ORDER BY last_message_at DESC
            LIMIT $1
            """,
            limit,
        )
        exported_count = 0
        for row in rows:
            conversation_id = row["id"]
            if await self._export_conversation_transcript(conversation_id):
                exported_count += 1
        return exported_count

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

    async def get_assistant_by_client_message_id(
        self,
        conversation_id: UUID,
        client_message_id: str,
    ) -> Message | None:
        """Return assistant message linked to a client-generated message id."""
        row = await fetchrow(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = $1
              AND role = 'assistant'
              AND (
                client_message_id = $2
                OR internal_json->>'client_message_id' = $2
              )
            ORDER BY created_at DESC
            LIMIT 1
            """,
            conversation_id,
            client_message_id,
        )
        if row is None:
            return None
        return self._row_to_message(row)

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
            client_message_id=row.get("client_message_id"),
            internal_json=orjson.loads(row["internal_json"]) if row["internal_json"] else None,
            tool_calls=orjson.loads(row["tool_calls"]) if row["tool_calls"] else None,
            created_at=row["created_at"],
        )

    async def _safe_export_conversation_transcript(self, conversation_id: UUID) -> None:
        """Best-effort exporter that never breaks runtime message flow."""
        try:
            await self._export_conversation_transcript(conversation_id)
        except Exception:
            logger.exception("chat_lab_transcript_export_failed", conversation_id=str(conversation_id))

    async def _export_conversation_transcript(self, conversation_id: UUID) -> bool:
        """Write one masked conversation transcript JSON for admin Chat Lab import."""
        conversation = await fetchrow(
            """
            SELECT
                c.id,
                c.hotel_id,
                c.phone_display,
                c.language,
                c.current_state,
                c.current_intent,
                c.risk_flags,
                c.created_at,
                c.last_message_at,
                (
                    SELECT m.internal_json->>'intent'
                    FROM messages m
                    WHERE m.conversation_id = c.id
                      AND m.role = 'assistant'
                    ORDER BY m.created_at DESC
                    LIMIT 1
                ) AS last_assistant_intent,
                (
                    SELECT m.internal_json->>'state'
                    FROM messages m
                    WHERE m.conversation_id = c.id
                      AND m.role = 'assistant'
                    ORDER BY m.created_at DESC
                    LIMIT 1
                ) AS last_assistant_state
            FROM conversations c
            WHERE c.id = $1
            """,
            conversation_id,
        )
        if conversation is None:
            return False

        message_rows = await fetch(
            """
            SELECT id, role, content, internal_json, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            """,
            conversation_id,
        )
        if not message_rows:
            return False

        masked_phone = str(conversation["phone_display"] or "maskeli_kullanici")
        conversation_id_str = str(conversation["id"])
        intent = str(conversation["current_intent"] or conversation["last_assistant_intent"] or "")
        state = str(conversation["current_state"] or conversation["last_assistant_state"] or "GREETING")

        messages: list[dict[str, Any]] = []
        for row in message_rows:
            role = str(row["role"] or "system")
            internal_json = self._decode_json_field(row["internal_json"])
            model = str(internal_json.get("model") or "") if isinstance(internal_json, dict) else ""
            message_phone = masked_phone if role == "user" else "velox_assistant"
            messages.append(
                {
                    "id": str(row["id"]),
                    "role": role,
                    "content": str(row["content"] or ""),
                    "phone": message_phone,
                    "from": message_phone,
                    "timestamp": row["created_at"].astimezone(UTC).isoformat(),
                    "created_at": row["created_at"].astimezone(UTC).isoformat(),
                    "internal_json": internal_json if isinstance(internal_json, dict) else None,
                    "model": model,
                }
            )

        payload = {
            "schema_version": _TRANSCRIPT_SCHEMA_VERSION,
            "source_type": "imported_real",
            "source_label": f"Canli WhatsApp - {masked_phone}",
            "conversation_id": conversation_id_str,
            "hotel_id": int(conversation["hotel_id"]),
            "phone_display": masked_phone,
            "language": str(conversation["language"] or "tr"),
            "state": state,
            "intent": intent,
            "risk_flags": list(conversation["risk_flags"] or []),
            "created_at": conversation["created_at"].astimezone(UTC).isoformat(),
            "last_message_at": conversation["last_message_at"].astimezone(UTC).isoformat(),
            "generated_at": datetime.now(UTC).isoformat(),
            "participants": [
                {
                    "phone": masked_phone,
                    "label": f"Misafir ({masked_phone})",
                    "role": "user",
                },
                {
                    "phone": "velox_assistant",
                    "label": "Velox Assistant",
                    "role": "assistant",
                },
            ],
            "messages": messages,
        }

        project_root = get_project_root(__file__)
        imports_root = project_root / settings.chat_lab_imports_dir
        file_path = imports_root / self._build_transcript_filename(conversation_id_str, masked_phone)
        content = orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode("utf-8")

        async with _TRANSCRIPT_WRITE_LOCK:
            await asyncio.to_thread(imports_root.mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(file_path.write_text, content, "utf-8")
        return True

    @staticmethod
    def _build_transcript_filename(conversation_id: str, masked_phone: str) -> str:
        """Create deterministic filename for one conversation transcript."""
        safe_phone = re.sub(r"[^a-zA-Z0-9]+", "_", masked_phone).strip("_").lower()
        if not safe_phone:
            safe_phone = "maskeli"
        return f"live_conv_{conversation_id}_{safe_phone}.json"

    @staticmethod
    def _decode_json_field(raw: Any) -> dict[str, Any] | None:
        """Safely decode jsonb values returned by asyncpg or helpers."""
        if raw is None:
            return None
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (bytes, bytearray, str)):
            try:
                decoded = orjson.loads(raw)
            except orjson.JSONDecodeError:
                return None
            if isinstance(decoded, dict):
                return decoded
        return None
