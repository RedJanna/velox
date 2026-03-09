"""Export helpers for test chat conversation downloads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from textwrap import wrap
from typing import Any, Literal

import orjson

ExportFormat = Literal["json", "pdf", "md", "txt"]

_MAX_PDF_LINE_LENGTH = 95
_PDF_LINES_PER_PAGE = 48


@dataclass(slots=True)
class ConversationExportPayload:
    """Normalized conversation payload used by all export formatters."""

    phone: str
    conversation: dict[str, Any]
    messages: list[dict[str, Any]]
    exported_at: datetime


def build_export_file_content(
    export_format: ExportFormat,
    payload: ConversationExportPayload,
) -> tuple[bytes, str, str]:
    """Build file bytes and metadata tuple: (content, media_type, extension)."""
    if export_format == "json":
        return _build_json(payload), "application/json", "json"
    if export_format == "md":
        return _build_markdown(payload).encode("utf-8"), "text/markdown; charset=utf-8", "md"
    if export_format == "txt":
        return _build_text(payload).encode("utf-8"), "text/plain; charset=utf-8", "txt"
    return _build_pdf(payload), "application/pdf", "pdf"


def build_export_filename(phone: str, extension: str, exported_at: datetime) -> str:
    """Create deterministic, download-safe filename for test chat exports."""
    safe_phone = re.sub(r"[^A-Za-z0-9_-]", "_", phone.strip()) or "test_user"
    stamp = exported_at.astimezone(UTC).strftime("%Y%m%d_%H%M%S")
    return f"test_conversation_{safe_phone}_{stamp}.{extension}"


def _build_json(payload: ConversationExportPayload) -> bytes:
    body = {
        "meta": {
            "phone": payload.phone,
            "exported_at": payload.exported_at.isoformat(),
        },
        "conversation": payload.conversation,
        "messages": payload.messages,
    }
    return orjson.dumps(body, option=orjson.OPT_INDENT_2)


def _build_markdown(payload: ConversationExportPayload) -> str:
    lines = [
        "# Test Konusma Transkripti",
        "",
        f"- Phone: `{payload.phone}`",
        f"- Exported At: `{payload.exported_at.isoformat()}`",
        f"- Conversation ID: `{payload.conversation.get('id', '-')}`",
        f"- State: `{payload.conversation.get('state', '-')}`",
        f"- Intent: `{payload.conversation.get('intent', '-')}`",
        "",
        "## Mesajlar",
        "",
    ]
    if not payload.messages:
        lines.append("_Mesaj bulunamadi._")
        return "\n".join(lines)

    for message in payload.messages:
        timestamp = message.get("created_at", "-")
        role = message.get("role", "unknown")
        content = str(message.get("content", "")).strip() or "-"
        lines.append(f"### {role.upper()} - {timestamp}")
        lines.append("")
        lines.append(content)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_text(payload: ConversationExportPayload) -> str:
    lines = [
        "TEST KONUSMA TRANSKRIPTI",
        f"Phone: {payload.phone}",
        f"Exported At: {payload.exported_at.isoformat()}",
        f"Conversation ID: {payload.conversation.get('id', '-')}",
        f"State: {payload.conversation.get('state', '-')}",
        f"Intent: {payload.conversation.get('intent', '-')}",
        "",
        "MESAJLAR",
        "--------",
    ]
    if not payload.messages:
        lines.append("Mesaj bulunamadi.")
        return "\n".join(lines)

    for message in payload.messages:
        timestamp = message.get("created_at", "-")
        role = str(message.get("role", "unknown")).upper()
        content = str(message.get("content", "")).strip() or "-"
        lines.append(f"[{timestamp}] {role}: {content}")
    return "\n".join(lines)


def _build_pdf(payload: ConversationExportPayload) -> bytes:
    lines = _build_pdf_lines(payload)
    return _render_minimal_pdf(lines)


def _build_pdf_lines(payload: ConversationExportPayload) -> list[str]:
    lines = [
        "TEST KONUSMA TRANSKRIPTI",
        f"Phone: {payload.phone}",
        f"Exported At: {payload.exported_at.isoformat()}",
        f"Conversation ID: {payload.conversation.get('id', '-')}",
        f"State: {payload.conversation.get('state', '-')}",
        f"Intent: {payload.conversation.get('intent', '-')}",
        "",
        "MESAJLAR",
        "--------",
    ]
    if not payload.messages:
        lines.append("Mesaj bulunamadi.")
        return lines

    for message in payload.messages:
        timestamp = str(message.get("created_at", "-"))
        role = str(message.get("role", "unknown")).upper()
        content = str(message.get("content", "")).strip() or "-"
        wrapped = wrap(content, width=_MAX_PDF_LINE_LENGTH) or ["-"]
        lines.append(f"[{timestamp}] {role}: {wrapped[0]}")
        for extra_line in wrapped[1:]:
            lines.append(f"  {extra_line}")
    return lines


def _render_minimal_pdf(lines: list[str]) -> bytes:
    pages = [lines[i : i + _PDF_LINES_PER_PAGE] for i in range(0, len(lines), _PDF_LINES_PER_PAGE)]
    if not pages:
        pages = [[""]]

    page_object_ids: list[int] = []
    content_object_ids: list[int] = []
    next_object_id = 3
    for _ in pages:
        page_object_ids.append(next_object_id)
        next_object_id += 1
        content_object_ids.append(next_object_id)
        next_object_id += 1
    font_object_id = next_object_id

    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
    }

    page_refs = " ".join(f"{page_id} 0 R" for page_id in page_object_ids)
    objects[2] = f"<< /Type /Pages /Kids [{page_refs}] /Count {len(page_object_ids)} >>".encode("ascii")

    for index, page_lines in enumerate(pages):
        page_id = page_object_ids[index]
        content_id = content_object_ids[index]
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")

        stream = _build_pdf_text_stream(page_lines)
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        )

    objects[font_object_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    return _serialize_pdf_objects(objects)


def _build_pdf_text_stream(page_lines: list[str]) -> bytes:
    stream_lines = [
        "BT",
        "/F1 10 Tf",
        "14 TL",
        "1 0 0 1 40 800 Tm",
    ]

    for index, line in enumerate(page_lines):
        escaped = _escape_pdf_text(line)
        if index == 0:
            stream_lines.append(f"({escaped}) Tj")
        else:
            stream_lines.append(f"T* ({escaped}) Tj")

    stream_lines.append("ET")
    return "\n".join(stream_lines).encode("latin-1", errors="replace")


def _escape_pdf_text(value: str) -> str:
    ascii_value = value.encode("latin-1", errors="replace").decode("latin-1")
    return (
        ascii_value.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _serialize_pdf_objects(objects: dict[int, bytes]) -> bytes:
    ordered_ids = sorted(objects.keys())
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]

    for object_id in ordered_ids:
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{object_id} 0 obj\n".encode("ascii"))
        chunks.append(objects[object_id])
        chunks.append(b"\nendobj\n")

    xref_offset = sum(len(chunk) for chunk in chunks)
    max_object_id = ordered_ids[-1]
    chunks.append(f"xref\n0 {max_object_id + 1}\n".encode("ascii"))
    chunks.append(b"0000000000 65535 f \n")

    by_id_offsets = {obj_id: offsets[idx + 1] for idx, obj_id in enumerate(ordered_ids)}
    for object_id in range(1, max_object_id + 1):
        offset = by_id_offsets.get(object_id, 0)
        chunks.append(f"{offset:010d} 00000 n \n".encode("ascii"))

    chunks.append(
        (
            "trailer\n"
            f"<< /Size {max_object_id + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return b"".join(chunks)
