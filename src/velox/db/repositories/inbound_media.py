"""Repository for inbound WhatsApp media analysis records."""

from __future__ import annotations

from typing import Any

import orjson

from velox.db.database import execute, fetchrow


class InboundMediaRepository:
    """CRUD helpers for inbound_media table."""

    async def create_pending(
        self,
        *,
        hotel_id: int,
        conversation_id: Any,
        whatsapp_message_id: str,
        whatsapp_media_id: str,
        media_type: str,
        mime_type: str,
        caption: str = "",
        file_size_bytes: int | None = None,
        sha256: str | None = None,
        expires_hours: int = 24,
    ) -> None:
        """Insert or update a media row in pending state."""
        await execute(
            """
            INSERT INTO inbound_media (
                hotel_id,
                conversation_id,
                whatsapp_message_id,
                whatsapp_media_id,
                media_type,
                mime_type,
                caption,
                file_size_bytes,
                sha256,
                analysis_status,
                expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'PENDING', now() + ($10 * interval '1 hour'))
            ON CONFLICT (whatsapp_message_id, whatsapp_media_id) DO UPDATE
            SET media_type = EXCLUDED.media_type,
                mime_type = EXCLUDED.mime_type,
                caption = EXCLUDED.caption,
                file_size_bytes = COALESCE(EXCLUDED.file_size_bytes, inbound_media.file_size_bytes),
                sha256 = COALESCE(EXCLUDED.sha256, inbound_media.sha256),
                analysis_status = 'PENDING',
                error_type = NULL,
                error_detail = NULL,
                updated_at = now()
            """,
            hotel_id,
            conversation_id,
            whatsapp_message_id,
            whatsapp_media_id,
            media_type,
            mime_type,
            caption,
            file_size_bytes,
            sha256,
            expires_hours,
        )

    async def mark_analyzed(
        self,
        *,
        whatsapp_message_id: str,
        whatsapp_media_id: str,
        analysis_json: dict[str, Any],
        confidence: float,
        model_name: str,
        risk_flags: list[str],
        file_size_bytes: int | None = None,
        sha256: str | None = None,
    ) -> None:
        """Mark media record as analyzed successfully."""
        await execute(
            """
            UPDATE inbound_media
            SET analysis_status = 'ANALYZED',
                analysis_json = $3,
                analysis_confidence = $4,
                analysis_model = $5,
                risk_flags = $6,
                file_size_bytes = COALESCE($7, file_size_bytes),
                sha256 = COALESCE($8, sha256),
                error_type = NULL,
                error_detail = NULL,
                updated_at = now()
            WHERE whatsapp_message_id = $1
              AND whatsapp_media_id = $2
            """,
            whatsapp_message_id,
            whatsapp_media_id,
            orjson.dumps(analysis_json).decode(),
            confidence,
            model_name,
            risk_flags,
            file_size_bytes,
            sha256,
        )

    async def mark_failed(
        self,
        *,
        whatsapp_message_id: str,
        whatsapp_media_id: str,
        error_type: str,
        error_detail: str,
        status: str = "FAILED",
    ) -> None:
        """Mark media record as failed or unsupported."""
        await execute(
            """
            UPDATE inbound_media
            SET analysis_status = $3,
                error_type = $4,
                error_detail = $5,
                updated_at = now()
            WHERE whatsapp_message_id = $1
              AND whatsapp_media_id = $2
            """,
            whatsapp_message_id,
            whatsapp_media_id,
            status,
            error_type,
            error_detail[:1024],
        )

    async def get_by_provider_ids(
        self,
        *,
        whatsapp_message_id: str,
        whatsapp_media_id: str,
    ) -> dict[str, Any] | None:
        """Fetch one media row by WhatsApp ids."""
        row = await fetchrow(
            """
            SELECT *
            FROM inbound_media
            WHERE whatsapp_message_id = $1
              AND whatsapp_media_id = $2
            LIMIT 1
            """,
            whatsapp_message_id,
            whatsapp_media_id,
        )
        if row is None:
            return None
        return dict(row)
