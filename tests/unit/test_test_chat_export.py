"""Unit tests for test chat export formatters."""

from datetime import UTC, datetime

import orjson

from velox.api.routes.test_chat_export import (
    ConversationExportPayload,
    build_export_file_content,
    build_export_filename,
)


def _sample_payload() -> ConversationExportPayload:
    return ConversationExportPayload(
        phone="test_user_123",
        conversation={
            "id": "3d6f5d3c-8e10-43b1-9e97-b9fcadf4b7cb",
            "state": "GREETING",
            "intent": "general",
            "language": "tr",
            "entities": {},
            "risk_flags": [],
            "is_active": True,
        },
        messages=[
            {
                "id": "a",
                "role": "user",
                "content": "Merhaba",
                "internal_json": None,
                "created_at": "2026-03-09T10:00:00+00:00",
            },
            {
                "id": "b",
                "role": "assistant",
                "content": "Hos geldiniz, nasil yardimci olabilirim?",
                "internal_json": {"intent": "greeting"},
                "created_at": "2026-03-09T10:00:01+00:00",
            },
        ],
        exported_at=datetime(2026, 3, 9, 10, 5, tzinfo=UTC),
    )


def test_build_export_filename_sanitizes_phone() -> None:
    filename = build_export_filename(
        phone="test user/+90",
        extension="md",
        exported_at=datetime(2026, 3, 9, 10, 5, 7, tzinfo=UTC),
    )
    assert filename == "test_conversation_test_user__90_20260309_100507.md"


def test_json_export_contains_metadata_and_messages() -> None:
    payload = _sample_payload()
    content, media_type, extension = build_export_file_content("json", payload)
    parsed = orjson.loads(content)
    assert media_type == "application/json"
    assert extension == "json"
    assert parsed["meta"]["phone"] == "test_user_123"
    assert parsed["conversation"]["id"] == payload.conversation["id"]
    assert len(parsed["messages"]) == 2


def test_markdown_export_contains_sections() -> None:
    payload = _sample_payload()
    content, media_type, extension = build_export_file_content("md", payload)
    text = content.decode("utf-8")
    assert media_type.startswith("text/markdown")
    assert extension == "md"
    assert "# Test Konusma Transkripti" in text
    assert "## Mesajlar" in text
    assert "### USER - 2026-03-09T10:00:00+00:00" in text


def test_text_export_contains_flat_transcript() -> None:
    payload = _sample_payload()
    content, media_type, extension = build_export_file_content("txt", payload)
    text = content.decode("utf-8")
    assert media_type.startswith("text/plain")
    assert extension == "txt"
    assert "TEST KONUSMA TRANSKRIPTI" in text
    assert "[2026-03-09T10:00:00+00:00] USER: Merhaba" in text


def test_pdf_export_returns_pdf_document() -> None:
    payload = _sample_payload()
    content, media_type, extension = build_export_file_content("pdf", payload)
    assert media_type == "application/pdf"
    assert extension == "pdf"
    assert content.startswith(b"%PDF-1.4")
    assert b"/Type /Catalog" in content
    assert b"/Type /Page" in content
