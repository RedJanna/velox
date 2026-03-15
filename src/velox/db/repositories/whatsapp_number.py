"""Repository for WhatsApp destination number to hotel mapping."""

import re

import asyncpg

from velox.db.database import execute, fetchrow

_NON_DIGIT_RE = re.compile(r"\D+")


def _normalize_display_phone_number(value: str) -> str:
    """Normalize display phone to stable digits-only representation."""
    return _NON_DIGIT_RE.sub("", value)


class WhatsAppNumberRepository:
    """CRUD operations for whatsapp_numbers table."""

    async def get_hotel_id_by_phone_number_id(self, phone_number_id: str) -> int | None:
        """Resolve hotel id by Meta phone_number_id."""
        row = await fetchrow(
            """
            SELECT hotel_id
            FROM whatsapp_numbers
            WHERE phone_number_id = $1
              AND is_active = true
            LIMIT 1
            """,
            phone_number_id.strip(),
        )
        if row is None:
            return None
        return int(row["hotel_id"])

    async def get_hotel_id_by_display_phone_number(self, display_phone_number: str) -> int | None:
        """Resolve hotel id by WhatsApp display phone number."""
        normalized = _normalize_display_phone_number(display_phone_number)
        if not normalized:
            return None
        row = await fetchrow(
            """
            SELECT hotel_id
            FROM whatsapp_numbers
            WHERE regexp_replace(display_phone_number, '\\D', '', 'g') = $1
              AND is_active = true
            LIMIT 1
            """,
            normalized,
        )
        if row is None:
            return None
        return int(row["hotel_id"])

    async def upsert_mapping(
        self,
        *,
        hotel_id: int,
        phone_number_id: str,
        display_phone_number: str | None = None,
        is_active: bool = True,
    ) -> asyncpg.Record:
        """Insert or update one destination number mapping."""
        normalized_display = None
        if display_phone_number:
            normalized_display = _normalize_display_phone_number(display_phone_number)
            if not normalized_display:
                normalized_display = None

        row = await fetchrow(
            """
            INSERT INTO whatsapp_numbers (hotel_id, phone_number_id, display_phone_number, is_active)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (phone_number_id) DO UPDATE
            SET hotel_id = EXCLUDED.hotel_id,
                display_phone_number = EXCLUDED.display_phone_number,
                is_active = EXCLUDED.is_active,
                updated_at = now()
            RETURNING *
            """,
            hotel_id,
            phone_number_id.strip(),
            normalized_display,
            is_active,
        )
        if row is None:
            raise RuntimeError("Failed to upsert whatsapp number mapping.")
        return row

    async def deactivate_mapping(self, phone_number_id: str) -> None:
        """Mark a destination number mapping as inactive."""
        await execute(
            """
            UPDATE whatsapp_numbers
            SET is_active = false,
                updated_at = now()
            WHERE phone_number_id = $1
            """,
            phone_number_id.strip(),
        )
