"""Repository for tenant-scoped WhatsApp Cloud API integrations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import orjson

from velox.db.database import get_pool
from velox.utils.json import decode_json_value


CONNECT_SESSION_TTL_MINUTES = 20


def _json_dumps(payload: Any) -> str:
    return orjson.dumps(payload).decode()


def _row_to_dict(row: asyncpg.Record | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = dict(row)
    for key in ("token_scopes_json", "components_json", "safe_payload_json"):
        if key in payload:
            payload[key] = decode_json_value(payload[key])
    return payload


class WhatsAppIntegrationRepository:
    """CRUD operations for WhatsApp integration, templates, and audit events."""

    async def get_latest_for_hotel(self, hotel_id: int) -> dict[str, Any] | None:
        """Return the most recent integration for a hotel."""
        row = await get_pool().fetchrow(
            """
            SELECT *
            FROM whatsapp_integrations
            WHERE hotel_id = $1
            ORDER BY is_active DESC, updated_at DESC, id DESC
            LIMIT 1
            """,
            hotel_id,
        )
        return _row_to_dict(row)

    async def get_active_for_hotel(self, hotel_id: int) -> dict[str, Any] | None:
        """Return the active integration for a hotel."""
        row = await get_pool().fetchrow(
            """
            SELECT *
            FROM whatsapp_integrations
            WHERE hotel_id = $1
              AND is_active = true
            LIMIT 1
            """,
            hotel_id,
        )
        return _row_to_dict(row)

    async def upsert_integration(
        self,
        *,
        hotel_id: int,
        business_id: str | None,
        waba_id: str | None,
        phone_number_id: str,
        display_phone_number: str | None,
        verified_name: str | None,
        quality_rating: str | None,
        messaging_limit: str | None,
        token_ciphertext: str | None,
        token_last4: str | None,
        token_expires_at: datetime | None,
        token_scopes: list[str],
        webhook_verify_token_ciphertext: str | None,
        created_by_admin_id: int,
        connection_status: str = "active",
        webhook_status: str = "unknown",
    ) -> dict[str, Any]:
        """Insert a new active integration and deactivate stale active rows."""
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    UPDATE whatsapp_integrations
                    SET is_active = false,
                        updated_at = now()
                    WHERE hotel_id = $1
                      AND is_active = true
                    """,
                    hotel_id,
                )
                row = await conn.fetchrow(
                    """
                    INSERT INTO whatsapp_integrations (
                        hotel_id, business_id, waba_id, phone_number_id,
                        display_phone_number, verified_name, quality_rating,
                        messaging_limit, token_ciphertext, token_last4,
                        token_expires_at, token_scopes_json,
                        webhook_verify_token_ciphertext, webhook_status,
                        connection_status, created_by_admin_id
                    )
                    VALUES (
                        $1, $2, $3, $4,
                        $5, $6, $7,
                        $8, $9, $10,
                        $11, $12::jsonb,
                        $13, $14,
                        $15, $16
                    )
                    RETURNING *
                    """,
                    hotel_id,
                    business_id,
                    waba_id,
                    phone_number_id,
                    display_phone_number,
                    verified_name,
                    quality_rating,
                    messaging_limit,
                    token_ciphertext,
                    token_last4,
                    token_expires_at,
                    _json_dumps(token_scopes),
                    webhook_verify_token_ciphertext,
                    webhook_status,
                    connection_status,
                    created_by_admin_id,
                )
                if row is None:
                    raise RuntimeError("Failed to create WhatsApp integration.")
                if display_phone_number:
                    await conn.execute(
                        """
                        DELETE FROM whatsapp_numbers
                        WHERE display_phone_number = $1
                          AND phone_number_id <> $2
                        """,
                        display_phone_number,
                        phone_number_id,
                    )
                await conn.execute(
                    """
                    INSERT INTO whatsapp_numbers (hotel_id, phone_number_id, display_phone_number, is_active)
                    VALUES ($1, $2, $3, true)
                    ON CONFLICT (phone_number_id) DO UPDATE
                    SET hotel_id = EXCLUDED.hotel_id,
                        display_phone_number = EXCLUDED.display_phone_number,
                        is_active = true,
                        updated_at = now()
                    """,
                    hotel_id,
                    phone_number_id,
                    display_phone_number,
                )
                integration = _row_to_dict(row)
                if integration is None:
                    raise RuntimeError("Failed to decode WhatsApp integration.")
                await self.record_event(
                    hotel_id=hotel_id,
                    integration_id=int(integration["id"]),
                    connect_session_id=None,
                    actor_admin_id=created_by_admin_id,
                    event_type="integration_saved",
                    safe_payload={
                        "phone_number_id": phone_number_id,
                        "waba_id": waba_id,
                        "business_id": business_id,
                        "connection_status": connection_status,
                    },
                    conn=conn,
                )
                return integration

    async def update_health(
        self,
        *,
        integration_id: int,
        hotel_id: int,
        connection_status: str,
        webhook_status: str | None = None,
        quality_rating: str | None = None,
        messaging_limit: str | None = None,
        last_error_code: str | None = None,
        last_error_message: str | None = None,
    ) -> dict[str, Any]:
        """Persist the latest health check result."""
        row = await get_pool().fetchrow(
            """
            UPDATE whatsapp_integrations
            SET connection_status = $3,
                webhook_status = COALESCE($4, webhook_status),
                quality_rating = COALESCE($5, quality_rating),
                messaging_limit = COALESCE($6, messaging_limit),
                last_error_code = $7,
                last_error_message = $8,
                last_health_check_at = now(),
                updated_at = now()
            WHERE id = $1
              AND hotel_id = $2
            RETURNING *
            """,
            integration_id,
            hotel_id,
            connection_status,
            webhook_status,
            quality_rating,
            messaging_limit,
            last_error_code,
            last_error_message,
        )
        integration = _row_to_dict(row)
        if integration is None:
            raise RuntimeError("WhatsApp integration was not found.")
        return integration

    async def create_connect_session(
        self,
        *,
        hotel_id: int,
        state_token: str,
        created_by_admin_id: int,
    ) -> dict[str, Any]:
        """Create a short-lived OAuth connection session."""
        session_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=CONNECT_SESSION_TTL_MINUTES)
        row = await get_pool().fetchrow(
            """
            INSERT INTO whatsapp_connect_sessions (
                id, hotel_id, state_token, created_by_admin_id, expires_at
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            session_id,
            hotel_id,
            state_token,
            created_by_admin_id,
            expires_at,
        )
        session = _row_to_dict(row)
        if session is None:
            raise RuntimeError("Failed to create WhatsApp connection session.")
        return session

    async def get_connect_session(self, session_id: UUID, hotel_id: int | None = None) -> dict[str, Any] | None:
        """Return a connect session by id."""
        if hotel_id is None:
            row = await get_pool().fetchrow(
                "SELECT * FROM whatsapp_connect_sessions WHERE id = $1",
                session_id,
            )
        else:
            row = await get_pool().fetchrow(
                """
                SELECT *
                FROM whatsapp_connect_sessions
                WHERE id = $1
                  AND hotel_id = $2
                """,
                session_id,
                hotel_id,
            )
        return _row_to_dict(row)

    async def get_connect_session_by_state(self, state_token: str) -> dict[str, Any] | None:
        """Return a connect session by OAuth state token."""
        row = await get_pool().fetchrow(
            """
            SELECT *
            FROM whatsapp_connect_sessions
            WHERE state_token = $1
            LIMIT 1
            """,
            state_token,
        )
        return _row_to_dict(row)

    async def mark_connect_session_authorized(
        self,
        *,
        session_id: UUID,
        token_ciphertext: str,
        token_last4: str | None,
    ) -> dict[str, Any]:
        """Persist the encrypted OAuth token on a connection session."""
        row = await get_pool().fetchrow(
            """
            UPDATE whatsapp_connect_sessions
            SET status = 'authorized',
                token_ciphertext = $2,
                token_last4 = $3,
                updated_at = now()
            WHERE id = $1
            RETURNING *
            """,
            session_id,
            token_ciphertext,
            token_last4,
        )
        session = _row_to_dict(row)
        if session is None:
            raise RuntimeError("WhatsApp connection session was not found.")
        return session

    async def mark_connect_session_error(
        self,
        *,
        session_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Persist a safe connection-session error."""
        await get_pool().execute(
            """
            UPDATE whatsapp_connect_sessions
            SET status = 'error',
                error_code = $2,
                error_message = $3,
                updated_at = now()
            WHERE id = $1
            """,
            session_id,
            error_code[:128],
            error_message[:500],
        )

    async def complete_connect_session(
        self,
        *,
        session_id: UUID,
        business_id: str | None,
        waba_id: str,
        phone_number_id: str,
    ) -> dict[str, Any]:
        """Mark an authorized OAuth session as completed after asset selection."""
        row = await get_pool().fetchrow(
            """
            UPDATE whatsapp_connect_sessions
            SET status = 'completed',
                selected_business_id = $2,
                selected_waba_id = $3,
                selected_phone_number_id = $4,
                updated_at = now()
            WHERE id = $1
            RETURNING *
            """,
            session_id,
            business_id,
            waba_id,
            phone_number_id,
        )
        session = _row_to_dict(row)
        if session is None:
            raise RuntimeError("WhatsApp connection session was not found.")
        return session

    async def list_events(self, hotel_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent connection audit events."""
        rows = await get_pool().fetch(
            """
            SELECT *
            FROM whatsapp_connection_events
            WHERE hotel_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            hotel_id,
            limit,
        )
        return [dict(_row_to_dict(row) or {}) for row in rows]

    async def record_event(
        self,
        *,
        hotel_id: int,
        integration_id: int | None,
        connect_session_id: UUID | None,
        actor_admin_id: int | None,
        event_type: str,
        safe_payload: dict[str, Any],
        conn: asyncpg.Connection | None = None,
    ) -> None:
        """Insert an audit event with a secret-free payload."""
        executor = conn if conn is not None else get_pool()
        await executor.execute(
            """
            INSERT INTO whatsapp_connection_events (
                hotel_id, integration_id, connect_session_id,
                actor_admin_id, event_type, safe_payload_json
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            hotel_id,
            integration_id,
            connect_session_id,
            actor_admin_id,
            event_type,
            _json_dumps(safe_payload),
        )

    async def list_templates(self, hotel_id: int) -> list[dict[str, Any]]:
        """Return local template snapshots for a hotel."""
        rows = await get_pool().fetch(
            """
            SELECT *
            FROM whatsapp_templates
            WHERE hotel_id = $1
            ORDER BY updated_at DESC, name ASC
            """,
            hotel_id,
        )
        return [dict(_row_to_dict(row) or {}) for row in rows]

    async def upsert_template(
        self,
        *,
        hotel_id: int,
        waba_id: str,
        meta_template_id: str | None,
        name: str,
        language: str,
        category: str | None,
        status: str,
        components: list[dict[str, Any]],
        rejection_reason: str | None,
    ) -> dict[str, Any]:
        """Upsert a template snapshot returned by Meta."""
        row = await get_pool().fetchrow(
            """
            INSERT INTO whatsapp_templates (
                hotel_id, waba_id, meta_template_id, name, language,
                category, status, components_json, rejection_reason,
                last_synced_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, now())
            ON CONFLICT (hotel_id, waba_id, name, language) DO UPDATE
            SET meta_template_id = EXCLUDED.meta_template_id,
                category = EXCLUDED.category,
                status = EXCLUDED.status,
                components_json = EXCLUDED.components_json,
                rejection_reason = EXCLUDED.rejection_reason,
                last_synced_at = now(),
                updated_at = now()
            RETURNING *
            """,
            hotel_id,
            waba_id,
            meta_template_id,
            name,
            language,
            category,
            status,
            _json_dumps(components),
            rejection_reason,
        )
        template = _row_to_dict(row)
        if template is None:
            raise RuntimeError("Failed to upsert WhatsApp template.")
        return template
