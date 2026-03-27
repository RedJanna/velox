"""Unit tests for inbound media repository queries."""

from __future__ import annotations

import pytest

from velox.db.repositories import inbound_media


@pytest.mark.asyncio
async def test_create_pending_uses_interval_multiplication(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = inbound_media.InboundMediaRepository()
    captured: dict[str, object] = {}

    async def _fake_execute(query: str, *args: object) -> None:
        captured["query"] = query
        captured["args"] = args

    monkeypatch.setattr(inbound_media, "execute", _fake_execute)

    await repository.create_pending(
        hotel_id=21966,
        conversation_id="conv-1",
        whatsapp_message_id="wamid.1",
        whatsapp_media_id="media-1",
        media_type="audio",
        mime_type="audio/ogg",
        expires_hours=24,
    )

    assert "interval '1 hour'" in str(captured["query"])
    assert "|| ' hour'" not in str(captured["query"])
    assert captured["args"][-1] == 24
