"""Unit tests for WhatsApp number repository."""

import pytest

from velox.db.repositories import whatsapp_number


@pytest.mark.asyncio
async def test_get_hotel_id_by_display_phone_number_normalizes_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Display phone lookup should ignore formatting characters."""
    repository = whatsapp_number.WhatsAppNumberRepository()
    captured: dict[str, object] = {}

    async def _fake_fetchrow(query: str, normalized_phone: str) -> dict[str, int] | None:
        captured["query"] = query
        captured["phone"] = normalized_phone
        return {"hotel_id": 33469}

    monkeypatch.setattr(whatsapp_number, "fetchrow", _fake_fetchrow)
    resolved = await repository.get_hotel_id_by_display_phone_number("+90 (555) 123-45-67")
    assert resolved == 33469
    assert captured["phone"] == "905551234567"


@pytest.mark.asyncio
async def test_upsert_mapping_normalizes_display_phone(monkeypatch: pytest.MonkeyPatch) -> None:
    """Upsert should save normalized display phone value."""
    repository = whatsapp_number.WhatsAppNumberRepository()
    captured: dict[str, object] = {}

    async def _fake_fetchrow(
        _query: str,
        hotel_id: int,
        phone_number_id: str,
        display_phone_number: str | None,
        is_active: bool,
    ) -> dict[str, object] | None:
        captured["hotel_id"] = hotel_id
        captured["phone_number_id"] = phone_number_id
        captured["display_phone_number"] = display_phone_number
        captured["is_active"] = is_active
        return {"hotel_id": hotel_id, "phone_number_id": phone_number_id}

    monkeypatch.setattr(whatsapp_number, "fetchrow", _fake_fetchrow)
    row = await repository.upsert_mapping(
        hotel_id=21966,
        phone_number_id="  123456789012345  ",
        display_phone_number="+90 555 999 00 11",
        is_active=True,
    )
    assert row["hotel_id"] == 21966
    assert captured["phone_number_id"] == "123456789012345"
    assert captured["display_phone_number"] == "905559990011"
    assert captured["is_active"] is True
