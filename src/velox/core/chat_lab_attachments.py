"""Chat Lab attachment upload/storage helpers."""

from __future__ import annotations

import asyncio
import hashlib
import mimetypes
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog

from velox.db.database import execute, fetch, fetchrow
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)

CHAT_LAB_UPLOADS_DIR = "data/chat_lab_uploads"
MAX_ATTACHMENTS_PER_MESSAGE = 5
ASSET_TTL_HOURS = 24

_ALLOWED_BY_EXTENSION: dict[str, tuple[str, set[str]]] = {
    ".jpg": ("image", {"image/jpeg"}),
    ".jpeg": ("image", {"image/jpeg"}),
    ".png": ("image", {"image/png"}),
    ".webp": ("image", {"image/webp"}),
    ".pdf": ("document", {"application/pdf"}),
    ".docx": (
        "document",
        {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/zip",
        },
    ),
    ".txt": ("document", {"text/plain"}),
    ".ogg": ("audio", {"audio/ogg", "application/ogg"}),
    ".mp3": ("audio", {"audio/mpeg"}),
    ".m4a": ("audio", {"audio/mp4", "audio/x-m4a"}),
    ".mp4": ("audio", {"audio/mp4"}),
    ".webm": ("audio", {"audio/webm", "video/webm"}),
}

_MAX_SIZE_BY_KIND = {
    "image": 10 * 1024 * 1024,
    "document": 15 * 1024 * 1024,
    "audio": 16 * 1024 * 1024,
}

_SAFE_FILENAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


class ChatLabAttachmentError(RuntimeError):
    """Raised when upload or attachment validation fails."""


@dataclass(slots=True)
class StoredChatLabAsset:
    """Stored attachment metadata used by routes and send pipelines."""

    id: str
    hotel_id: int
    kind: str
    mime_type: str
    file_name: str
    storage_path: str
    size_bytes: int
    sha256: str


class ChatLabAttachmentService:
    """Manage upload lifecycle for Chat Lab attachments."""

    def __init__(self, uploads_root: Path | None = None) -> None:
        project_root = get_project_root(__file__)
        self._uploads_root = uploads_root or (project_root / CHAT_LAB_UPLOADS_DIR)

    async def save_upload(
        self,
        *,
        hotel_id: int,
        file_name: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> StoredChatLabAsset:
        """Validate, store, and persist one attachment."""
        sanitized_name = self._sanitize_filename(file_name)
        if not sanitized_name:
            raise ChatLabAttachmentError("Dosya adi gecersiz.")

        extension = Path(sanitized_name).suffix.lower()
        if extension not in _ALLOWED_BY_EXTENSION:
            raise ChatLabAttachmentError("Desteklenmeyen dosya turu.")

        kind, allowed_mimes = _ALLOWED_BY_EXTENSION[extension]
        max_bytes = _MAX_SIZE_BY_KIND[kind]
        if len(file_bytes) == 0:
            raise ChatLabAttachmentError("Bos dosya yuklenemez.")
        if len(file_bytes) > max_bytes:
            raise ChatLabAttachmentError(f"Dosya limiti asildi ({kind}).")

        declared_mime = (content_type or "").split(";")[0].strip().lower()
        guessed_mime = self._guess_mime(extension, file_bytes)
        effective_mime = guessed_mime or declared_mime or (next(iter(allowed_mimes)))

        if declared_mime and declared_mime not in allowed_mimes:
            raise ChatLabAttachmentError("Dosya tipi dogrulamasi basarisiz.")
        if (
            guessed_mime
            and guessed_mime not in allowed_mimes
            # Docx files are zip containers; keep extension as the trust anchor there.
            and not (extension == ".docx" and guessed_mime == "application/zip")
        ):
            raise ChatLabAttachmentError("Dosya icerigi ile tipi uyusmuyor.")

        if extension == ".txt" and not self._is_probably_text(file_bytes):
            raise ChatLabAttachmentError("Metin dosyasi UTF-8 degil veya gecersiz.")

        sha256 = hashlib.sha256(file_bytes).hexdigest()
        now = datetime.now(UTC)

        row = await fetchrow(
            """
            INSERT INTO chat_lab_assets (
                hotel_id,
                kind,
                mime_type,
                file_name,
                storage_path,
                size_bytes,
                sha256,
                status,
                uploaded_at,
                expires_at,
                metadata_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'uploaded', $8, $9, '{}'::jsonb)
            RETURNING id
            """,
            hotel_id,
            kind,
            effective_mime,
            sanitized_name,
            "",
            len(file_bytes),
            sha256,
            now,
            now + timedelta(hours=ASSET_TTL_HOURS),
        )
        if row is None:
            raise ChatLabAttachmentError("Dosya kaydi olusturulamadi.")

        asset_id = str(row["id"])
        dest_path = self._build_storage_path(asset_id=asset_id, file_name=sanitized_name)
        await asyncio.to_thread(dest_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(dest_path.write_bytes, file_bytes)

        await execute(
            "UPDATE chat_lab_assets SET storage_path = $2 WHERE id = $1::uuid",
            asset_id,
            str(dest_path),
        )

        return StoredChatLabAsset(
            id=asset_id,
            hotel_id=hotel_id,
            kind=kind,
            mime_type=effective_mime,
            file_name=sanitized_name,
            storage_path=str(dest_path),
            size_bytes=len(file_bytes),
            sha256=sha256,
        )

    async def get_asset_for_hotel(self, *, asset_id: str, hotel_id: int) -> StoredChatLabAsset:
        """Return one uploaded asset if visible to the provided hotel."""
        try:
            UUID(asset_id)
        except ValueError as error:
            raise ChatLabAttachmentError("Dosya kimligi gecersiz.") from error
        row = await fetchrow(
            """
            SELECT id, hotel_id, kind, mime_type, file_name, storage_path, size_bytes, sha256
            FROM chat_lab_assets
            WHERE id = $1::uuid AND hotel_id = $2
              AND status IN ('uploaded', 'attached')
            """,
            asset_id,
            hotel_id,
        )
        if row is None:
            raise ChatLabAttachmentError("Dosya bulunamadi.")

        return StoredChatLabAsset(
            id=str(row["id"]),
            hotel_id=int(row["hotel_id"]),
            kind=str(row["kind"]),
            mime_type=str(row["mime_type"]),
            file_name=str(row["file_name"]),
            storage_path=str(row["storage_path"]),
            size_bytes=int(row["size_bytes"]),
            sha256=str(row["sha256"]),
        )

    async def resolve_assets_for_message(
        self,
        *,
        hotel_id: int,
        attachment_ids: list[str],
    ) -> list[StoredChatLabAsset]:
        """Validate attachment ids for one outbound message."""
        if not attachment_ids:
            return []
        if len(attachment_ids) > MAX_ATTACHMENTS_PER_MESSAGE:
            raise ChatLabAttachmentError("Tek mesajda en fazla 5 dosya gonderilebilir.")

        # Deduplicate while preserving order.
        normalized_ids: list[str] = []
        seen: set[str] = set()
        for raw in attachment_ids:
            candidate = str(raw or "").strip()
            if not candidate or candidate in seen:
                continue
            try:
                UUID(candidate)
            except ValueError as error:
                raise ChatLabAttachmentError("Ek kimligi gecersiz.") from error
            seen.add(candidate)
            normalized_ids.append(candidate)

        if not normalized_ids:
            return []

        rows = await fetch(
            """
            SELECT id, hotel_id, kind, mime_type, file_name, storage_path, size_bytes, sha256
            FROM chat_lab_assets
            WHERE id = ANY($1::uuid[]) AND hotel_id = $2 AND status = 'uploaded'
            """,
            normalized_ids,
            hotel_id,
        )

        assets_by_id: dict[str, StoredChatLabAsset] = {
            str(row["id"]): StoredChatLabAsset(
                id=str(row["id"]),
                hotel_id=int(row["hotel_id"]),
                kind=str(row["kind"]),
                mime_type=str(row["mime_type"]),
                file_name=str(row["file_name"]),
                storage_path=str(row["storage_path"]),
                size_bytes=int(row["size_bytes"]),
                sha256=str(row["sha256"]),
            )
            for row in rows
        }

        missing = [asset_id for asset_id in normalized_ids if asset_id not in assets_by_id]
        if missing:
            raise ChatLabAttachmentError("Eklerden biri bulunamadi veya kullanilamaz durumda.")

        return [assets_by_id[asset_id] for asset_id in normalized_ids]

    async def attach_assets_to_message(self, *, asset_ids: list[str], message_id: UUID) -> None:
        """Mark assets as attached to a persisted message."""
        if not asset_ids:
            return
        await execute(
            """
            UPDATE chat_lab_assets
            SET status = 'attached', attached_message_id = $2, attached_at = now(), expires_at = NULL
            WHERE id = ANY($1::uuid[])
            """,
            asset_ids,
            message_id,
        )

    async def delete_asset(self, *, asset_id: str, hotel_id: int) -> None:
        """Delete one uploaded-but-not-attached asset and mark DB record."""
        try:
            UUID(asset_id)
        except ValueError as error:
            raise ChatLabAttachmentError("Dosya kimligi gecersiz.") from error
        row = await fetchrow(
            """
            SELECT id, storage_path, status
            FROM chat_lab_assets
            WHERE id = $1::uuid AND hotel_id = $2
            """,
            asset_id,
            hotel_id,
        )
        if row is None:
            raise ChatLabAttachmentError("Dosya bulunamadi.")

        status = str(row["status"])
        if status != "uploaded":
            raise ChatLabAttachmentError("Bu dosya artik silinemez.")

        path = Path(str(row["storage_path"] or ""))
        if path and path.exists():
            await asyncio.to_thread(path.unlink)

        await execute(
            """
            UPDATE chat_lab_assets
            SET status = 'deleted', deleted_at = now()
            WHERE id = $1::uuid
            """,
            asset_id,
        )

    @staticmethod
    def _sanitize_filename(file_name: str) -> str:
        name = Path(file_name or "").name
        if not name:
            return ""
        normalized = _SAFE_FILENAME_PATTERN.sub("_", name)
        return normalized.strip("._")[:180]

    def _build_storage_path(self, *, asset_id: str, file_name: str) -> Path:
        now = datetime.now(UTC)
        return self._uploads_root / str(now.year) / f"{now.month:02d}" / f"{asset_id}_{file_name}"

    @staticmethod
    def _guess_mime(extension: str, file_bytes: bytes) -> str | None:
        head = file_bytes[:32]
        if head.startswith(b"\xFF\xD8\xFF"):
            return "image/jpeg"
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if head.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP":
            return "image/webp"
        if head.startswith(b"%PDF-"):
            return "application/pdf"
        if head.startswith(b"OggS"):
            return "audio/ogg"
        if head.startswith(b"ID3"):
            return "audio/mpeg"
        if len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
            return "audio/mpeg"
        if len(file_bytes) > 12 and file_bytes[4:8] == b"ftyp":
            return "audio/mp4"
        if head.startswith(b"PK\x03\x04") and extension == ".docx":
            return "application/zip"
        guessed = mimetypes.guess_type(f"file{extension}")[0]
        return guessed.lower() if guessed else None

    @staticmethod
    def _is_probably_text(file_bytes: bytes) -> bool:
        try:
            decoded = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return False
        sample = decoded[:2048]
        control_count = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\r\t")
        return control_count == 0

    async def cleanup_expired_assets(self) -> int:
        """Best-effort cleanup for expired uploaded assets."""
        rows = await fetch(
            """
            SELECT id, storage_path
            FROM chat_lab_assets
            WHERE status = 'uploaded' AND expires_at IS NOT NULL AND expires_at < now()
            LIMIT 200
            """,
        )
        cleaned = 0
        for row in rows:
            asset_id = str(row["id"])
            storage_path = str(row["storage_path"] or "")
            if storage_path and os.path.exists(storage_path):
                await asyncio.to_thread(Path(storage_path).unlink)
            await execute(
                "UPDATE chat_lab_assets SET status = 'expired' WHERE id = $1::uuid",
                asset_id,
            )
            cleaned += 1
        if cleaned:
            logger.info("chat_lab_asset_cleanup_done", count=cleaned)
        return cleaned


def serialize_asset_for_client(asset: StoredChatLabAsset) -> dict[str, Any]:
    """Return sanitized attachment metadata for API/UI payloads."""
    return {
        "asset_id": asset.id,
        "kind": asset.kind,
        "mime_type": asset.mime_type,
        "file_name": asset.file_name,
        "size_bytes": asset.size_bytes,
        "sha256": asset.sha256,
        "content_url": f"/api/v1/test/chat/upload-asset/{asset.id}/content",
    }
