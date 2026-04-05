"""Chat Lab feedback storage and transcript import services."""

from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog
import yaml

from velox.config.settings import settings
from velox.core.chat_lab_feedback_catalog import (
    CATEGORY_BY_KEY,
    CATEGORY_ITEMS,
    FEEDBACK_SCALE,
    TAG_ITEMS,
)
from velox.db.repositories.conversation import ConversationRepository
from velox.llm.client import get_llm_client
from velox.models.chat_lab_feedback import (
    ChatLabCatalogResponse,
    ChatLabFeedbackRequest,
    ChatLabFeedbackResponse,
    ChatLabImportFileItem,
    ChatLabImportListResponse,
    ChatLabImportRequest,
    ChatLabImportResponse,
    ChatLabMessageView,
    ChatLabParticipantOption,
)
from velox.models.conversation import Message
from velox.utils.privacy import hash_phone
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)

_FILE_WRITE_LOCK = asyncio.Lock()
_FEEDBACK_SCHEMA_VERSION = "chat_lab_feedback.v1"
_TRANSCRIPT_SCHEMA_VERSION = "chat_lab_import.v1"


class ChatLabFeedbackError(RuntimeError):
    """Base exception for Chat Lab feedback workflows."""


class FeedbackConversationNotFoundError(ChatLabFeedbackError):
    """Raised when no active live test conversation exists."""


class FeedbackMessageNotFoundError(ChatLabFeedbackError):
    """Raised when the selected assistant message cannot be found."""


class ChatLabImportError(ChatLabFeedbackError):
    """Raised when transcript import data is invalid."""


_FEEDBACK_BY_RATING = {item.rating: item for item in FEEDBACK_SCALE}


def build_feedback_catalog() -> ChatLabCatalogResponse:
    """Return static catalog plus dynamic report defaults."""
    now = datetime.now(UTC).replace(microsecond=0)
    last_report_end = _load_last_report_end(_feedback_root() / "reports")
    return ChatLabCatalogResponse(
        scales=list(FEEDBACK_SCALE),
        categories=list(CATEGORY_ITEMS),
        tags=list(TAG_ITEMS),
        default_report_start=last_report_end.isoformat() if last_report_end else None,
        default_report_end=now.isoformat(),
    )


class ChatLabFeedbackService:
    """Persist feedback records and normalize transcript imports."""

    def __init__(
        self,
        repository: ConversationRepository | None = None,
        feedback_root: Path | None = None,
        imports_root: Path | None = None,
    ) -> None:
        project_root = get_project_root(__file__)
        self._repository = repository or ConversationRepository()
        self._feedback_root = feedback_root or (project_root / settings.chat_lab_feedback_dir)
        self._imports_root = imports_root or (project_root / settings.chat_lab_imports_dir)

    async def get_catalog(self) -> ChatLabCatalogResponse:
        """Return catalog metadata for the Chat Lab UI."""
        self._imports_root.mkdir(parents=True, exist_ok=True)
        self._feedback_root.mkdir(parents=True, exist_ok=True)
        return build_feedback_catalog()

    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        """Persist one feedback file under the correct folder structure."""
        source = await self._load_source(payload)
        feedback_id = _build_feedback_id()
        category_key = _resolve_category_key(payload)
        tags = _resolve_tags(payload)
        rating_item = _FEEDBACK_BY_RATING[payload.rating]
        message_timestamp = source["assistant_created_at"]
        approved_example = payload.approved_example if payload.approved_example is not None else payload.rating == 5
        storage_group = "good_feedback" if payload.rating == 5 else "bad_feedback"
        storage_path = _build_feedback_path(
            feedback_root=self._feedback_root,
            feedback_id=feedback_id,
            storage_group=storage_group,
            rating=payload.rating,
            category_key=category_key,
            message_timestamp=message_timestamp,
            approved_example=approved_example,
        )

        record = {
            "schema_version": _FEEDBACK_SCHEMA_VERSION,
            "feedback_id": feedback_id,
            "status": "new",
            "approved_example": approved_example,
            "created_at": datetime.now(UTC).isoformat(),
            "rating": payload.rating,
            "rating_label": rating_item.label,
            "category": category_key,
            "category_label": CATEGORY_BY_KEY.get(category_key, CATEGORY_BY_KEY["ozel_kategori"]).label,
            "tags": tags,
            "gold_standard": payload.gold_standard,
            "notes": payload.notes,
            "source_type": payload.source_type,
            "storage_group": storage_group,
            "input": source["input_text"],
            "output": source["output_text"],
            "conversation_id": source["conversation_id"],
            "assistant_message_id": payload.assistant_message_id,
            "timestamp": source["assistant_created_at"].isoformat(),
            "language": source["language"],
            "intent": source["intent"],
            "state": source["state"],
            "risk_flags": source["risk_flags"],
            "tool_calls": source["tool_calls"],
            "model": source["model"],
            "excerpt": source["excerpt"],
            "source_file": source["source_file"],
        }

        async with _FILE_WRITE_LOCK:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            _write_yaml_file(storage_path, record)

        logger.info(
            "chat_lab_feedback_saved",
            feedback_id=feedback_id,
            rating=payload.rating,
            category=category_key,
            path=str(storage_path),
        )
        return ChatLabFeedbackResponse(
            status="saved",
            feedback_id=feedback_id,
            rating=payload.rating,
            rating_label=rating_item.label,
            storage_group=storage_group,
            category=category_key,
            tags=tags,
            storage_path=_display_path(storage_path),
            source_type=payload.source_type,
            approved_example=approved_example,
        )

    async def list_import_files(self) -> ChatLabImportListResponse:
        """List available transcript JSON files in the admin-only imports folder."""
        self._imports_root.mkdir(parents=True, exist_ok=True)
        try:
            await self._repository.export_recent_conversations_for_chat_lab(limit=200)
        except Exception:
            logger.exception("chat_lab_import_auto_export_failed")
        files = sorted(self._imports_root.glob("*.json"))
        items = []
        active_conv_ids = await self._get_active_conversation_ids()
        for file_path in files:
            if not self._is_import_file_active(file_path, active_conv_ids):
                continue
            items.append(
                ChatLabImportFileItem(
                    filename=file_path.name,
                    label=self._import_file_label(file_path),
                    modified_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC).isoformat(),
                    size_bytes=file_path.stat().st_size,
                )
            )
        return ChatLabImportListResponse(items=items)

    async def load_import(self, payload: ChatLabImportRequest) -> ChatLabImportResponse:
        """Load one transcript import file and normalize it for the Chat Lab UI."""
        raw_transcript = self._load_import_json(payload.filename)
        role_result = _resolve_import_roles(raw_transcript, payload.role_mapping)
        source_type = _resolve_import_source_type(raw_transcript)
        if role_result["status"] == "role_mapping_required":
            return ChatLabImportResponse(
                status="role_mapping_required",
                source_type=source_type,
                file_name=payload.filename,
                participants=role_result["participants"],
                metadata=role_result["metadata"],
            )

        messages = _normalize_import_messages(raw_transcript, role_result["role_mapping"])
        return ChatLabImportResponse(
            status="ready",
            source_type=source_type,
            file_name=payload.filename,
            conversation_id=str(raw_transcript.get("conversation_id") or payload.filename.removesuffix(".json")),
            source_label=str(raw_transcript.get("source_label") or payload.filename),
            messages=messages,
            participants=role_result["participants"],
            metadata=role_result["metadata"],
        )

    async def _load_source(self, payload: ChatLabFeedbackRequest) -> dict[str, Any]:
        if payload.source_type in {"imported_real", "imported_test"}:
            return await self._load_import_source(payload)
        if payload.source_type == "live_conversation":
            return await self._load_live_conversation_source(payload)
        return await self._load_live_source(payload)

    async def _load_live_source(self, payload: ChatLabFeedbackRequest) -> dict[str, Any]:
        phone = _ensure_test_phone(payload.phone)
        hashed_phone = hash_phone(phone)
        conversation = await self._repository.get_active_by_phone(settings.elektra_hotel_id, hashed_phone)
        if conversation is None or conversation.id is None:
            raise FeedbackConversationNotFoundError("No active test conversation found for this phone.")

        messages = await self._repository.get_messages(conversation.id, limit=500, offset=0)
        excerpt = _messages_until_target(messages, payload.assistant_message_id)
        assistant_message = excerpt[-1]
        if assistant_message.role != "assistant":
            raise FeedbackMessageNotFoundError("The selected message is not an assistant reply.")

        assistant_internal = assistant_message.internal_json or {}
        return {
            "conversation_id": str(conversation.id),
            "input_text": _latest_user_message(excerpt),
            "output_text": assistant_message.content,
            "assistant_created_at": assistant_message.created_at.astimezone(UTC),
            "language": conversation.language,
            "intent": str(assistant_internal.get("intent") or conversation.current_intent or ""),
            "state": str(assistant_internal.get("state") or conversation.current_state),
            "risk_flags": [str(flag) for flag in assistant_internal.get("risk_flags") or conversation.risk_flags],
            "tool_calls": _tool_call_names(assistant_internal.get("tool_calls") or assistant_message.tool_calls),
            "model": str(assistant_internal.get("model") or get_llm_client().primary_model),
            "excerpt": _serialize_excerpt(excerpt),
            "source_file": None,
        }

    async def _load_live_conversation_source(self, payload: ChatLabFeedbackRequest) -> dict[str, Any]:
        """Load feedback source from a live conversation selected by conversation ID."""
        if not payload.conversation_id:
            raise FeedbackConversationNotFoundError("Conversation ID is required for live conversation feedback.")
        try:
            conv_uuid = UUID(str(payload.conversation_id))
        except ValueError as error:
            raise FeedbackConversationNotFoundError("Invalid conversation ID format.") from error

        conversation = await self._repository.get_by_id(conv_uuid)
        if conversation is None or conversation.id is None:
            raise FeedbackConversationNotFoundError(
                f"Conversation not found for ID: {payload.conversation_id}"
            )

        messages = await self._repository.get_messages(conversation.id, limit=500, offset=0)
        excerpt = _messages_until_target(messages, payload.assistant_message_id)
        assistant_message = excerpt[-1]
        if assistant_message.role != "assistant":
            raise FeedbackMessageNotFoundError("The selected message is not an assistant reply.")

        assistant_internal = assistant_message.internal_json or {}
        return {
            "conversation_id": str(conversation.id),
            "input_text": _latest_user_message(excerpt),
            "output_text": assistant_message.content,
            "assistant_created_at": assistant_message.created_at.astimezone(UTC),
            "language": conversation.language,
            "intent": str(assistant_internal.get("intent") or conversation.current_intent or ""),
            "state": str(assistant_internal.get("state") or conversation.current_state),
            "risk_flags": [str(flag) for flag in assistant_internal.get("risk_flags") or conversation.risk_flags],
            "tool_calls": _tool_call_names(assistant_internal.get("tool_calls") or assistant_message.tool_calls),
            "model": str(assistant_internal.get("model") or get_llm_client().primary_model),
            "excerpt": _serialize_excerpt(excerpt),
            "source_file": None,
        }

    async def _load_import_source(self, payload: ChatLabFeedbackRequest) -> dict[str, Any]:
        if not payload.import_file:
            raise ChatLabImportError("Import file is required for imported transcript feedback.")

        raw_transcript = self._load_import_json(payload.import_file)
        role_result = _resolve_import_roles(raw_transcript, payload.role_mapping)
        if role_result["status"] != "ready":
            raise ChatLabImportError("Role mapping is required before saving imported transcript feedback.")

        messages = _normalize_import_messages(raw_transcript, role_result["role_mapping"])
        excerpt = _message_views_until_target(messages, payload.assistant_message_id)
        assistant_message = excerpt[-1]
        if assistant_message.role != "assistant":
            raise FeedbackMessageNotFoundError("The selected imported message is not an assistant reply.")

        assistant_internal = assistant_message.internal_json or {}
        return {
            "conversation_id": str(raw_transcript.get("conversation_id") or payload.import_file.removesuffix(".json")),
            "input_text": _latest_user_message_view(excerpt),
            "output_text": assistant_message.content,
            "assistant_created_at": datetime.fromisoformat(assistant_message.created_at),
            "language": str(raw_transcript.get("language") or assistant_internal.get("language") or "tr"),
            "intent": str(assistant_internal.get("intent") or raw_transcript.get("intent") or ""),
            "state": str(assistant_internal.get("state") or raw_transcript.get("state") or ""),
            "risk_flags": [
                str(flag)
                for flag in assistant_internal.get("risk_flags")
                or raw_transcript.get("risk_flags")
                or []
            ],
            "tool_calls": _tool_call_names(
                assistant_internal.get("tool_calls") or raw_transcript.get("tool_calls")
            ),
            "model": str(assistant_message.model or raw_transcript.get("model") or ""),
            "excerpt": [message.model_dump(mode="json") for message in excerpt[-8:]],
            "source_file": payload.import_file,
        }

    def _load_import_json(self, filename: str) -> dict[str, Any]:
        safe_name = Path(filename).name
        if safe_name != filename or not safe_name.endswith(".json"):
            raise ChatLabImportError("Invalid import file name.")

        file_path = self._imports_root / safe_name
        if not file_path.exists():
            raise ChatLabImportError("Import file not found.")

        try:
            with file_path.open(encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except json.JSONDecodeError as error:
            raise ChatLabImportError("Import file is not valid JSON.") from error

        if not isinstance(data, dict):
            raise ChatLabImportError("Import file must contain a JSON object.")
        if not isinstance(data.get("messages"), list):
            raise ChatLabImportError("Import file must contain a messages list.")
        schema_version = data.get("schema_version")
        if schema_version is not None and schema_version != _TRANSCRIPT_SCHEMA_VERSION:
            logger.warning("chat_lab_import_schema_mismatch", filename=safe_name, schema_version=schema_version)
        return data

    async def _get_active_conversation_ids(self) -> set[str]:
        """Return set of active conversation IDs from the database."""
        try:
            rows = await self._repository._get_active_ids()
            return {str(row) for row in rows}
        except Exception:
            logger.debug("chat_lab_active_ids_fetch_failed")
            return set()

    @staticmethod
    def _is_import_file_active(file_path: Path, active_ids: set[str]) -> bool:
        """Check if a live_conv_ import file belongs to an active conversation."""
        if not file_path.name.startswith("live_conv_"):
            return True
        if not active_ids:
            return True
        try:
            with file_path.open(encoding="utf-8") as file_obj:
                data = json.load(file_obj)
            conv_id = str(data.get("conversation_id") or "")
            return conv_id in active_ids
        except Exception:
            return True

    def _import_file_label(self, file_path: Path) -> str:
        """Build a readable option label from import file metadata."""
        try:
            with file_path.open(encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except Exception:
            return file_path.name

        source_label = str(data.get("source_label") or "").strip()
        phone_display = str(data.get("phone_display") or "").strip()
        conversation_id = str(data.get("conversation_id") or "").strip()
        short_id = conversation_id.split("-")[0] if conversation_id else ""

        parts = [part for part in [source_label, phone_display] if part]
        if short_id:
            parts.append(f"#{short_id}")
        return " | ".join(parts) if parts else file_path.name


def _feedback_root() -> Path:
    return get_project_root(__file__) / settings.chat_lab_feedback_dir


def _load_last_report_end(reports_dir: Path) -> datetime | None:
    if not reports_dir.exists():
        return None
    report_files = sorted(reports_dir.glob("report_*.yaml"))
    if not report_files:
        return None
    try:
        with report_files[-1].open(encoding="utf-8") as file_obj:
            data = yaml.safe_load(file_obj) or {}
    except Exception:
        return None
    period = data.get("period", {})
    if not isinstance(period, dict) or not period.get("date_to"):
        return None
    try:
        return datetime.fromisoformat(str(period["date_to"]))
    except ValueError:
        return None


def _build_feedback_path(
    feedback_root: Path,
    feedback_id: str,
    storage_group: str,
    rating: int,
    category_key: str,
    message_timestamp: datetime,
    approved_example: bool,
) -> Path:
    month_bucket = message_timestamp.astimezone(UTC).strftime("%Y-%m")
    if storage_group == "good_feedback":
        good_bucket = "approved_examples" if approved_example else "reviewed"
        return feedback_root / "good_feedback" / good_bucket / month_bucket / f"{feedback_id}.yaml"
    return feedback_root / "bad_feedback" / f"rating_{rating}" / category_key / month_bucket / f"{feedback_id}.yaml"


def _build_feedback_id() -> str:
    return datetime.now(UTC).strftime("fb_%Y%m%d_%H%M%S_%f")


def _resolve_category_key(payload: ChatLabFeedbackRequest) -> str:
    category = (payload.category or "").strip().lower()
    if category and category != "ozel_kategori":
        return category
    custom_category = (payload.custom_category or "").strip()
    if custom_category:
        return _slugify(custom_category)
    if payload.rating == 5:
        return "approved_example"
    return "ozel_kategori"


def _resolve_tags(payload: ChatLabFeedbackRequest) -> list[str]:
    tags = [tag.strip().lower() for tag in payload.tags if tag.strip()]
    tags.extend(_slugify(tag) for tag in payload.custom_tags if tag.strip())
    unique_tags: list[str] = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    return unique_tags


def _messages_until_target(messages: Sequence[Message], target_id: str) -> list[Message]:
    excerpt: list[Message] = []
    for message in messages:
        excerpt.append(message)
        if str(message.id) == target_id:
            return excerpt
    raise FeedbackMessageNotFoundError("The selected assistant reply could not be found.")


def _message_views_until_target(messages: Sequence[ChatLabMessageView], target_id: str) -> list[ChatLabMessageView]:
    excerpt: list[ChatLabMessageView] = []
    for message in messages:
        excerpt.append(message)
        if message.id == target_id:
            return excerpt
    raise FeedbackMessageNotFoundError("The selected imported reply could not be found.")


def _latest_user_message(messages: Sequence[Message]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _latest_user_message_view(messages: Sequence[ChatLabMessageView]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _serialize_excerpt(messages: Sequence[Message]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.astimezone(UTC).isoformat(),
            "internal_json": message.internal_json,
        }
        for message in messages[-8:]
    ]


def _tool_call_names(raw_tool_calls: Any) -> list[str]:
    if not isinstance(raw_tool_calls, list):
        return []
    names: list[str] = []
    for item in raw_tool_calls:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return names


def _write_yaml_file(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file_obj:
        yaml.safe_dump(payload, file_obj, allow_unicode=True, sort_keys=False, width=1000)


def _ensure_test_phone(phone: str) -> str:
    if phone.startswith("test_"):
        return phone
    return f"test_{phone}"


def _display_path(path: Path) -> str:
    raw_path = str(path)
    if raw_path.startswith("/mnt/") and len(raw_path) > 6:
        drive = raw_path[5].upper()
        remainder = raw_path[6:].replace("/", "\\")
        return f"{drive}:{remainder}"
    return raw_path


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return slug or "ozel"


def _resolve_import_roles(raw_transcript: dict[str, Any], role_mapping: Mapping[str, str]) -> dict[str, Any]:
    messages = raw_transcript.get("messages", [])
    participants = _extract_participants(raw_transcript)
    has_direct_roles = all(
        isinstance(message, dict) and str(message.get("role") or "").lower() in {"user", "assistant", "system"}
        for message in messages
    )
    if has_direct_roles:
        return {
            "status": "ready",
            "role_mapping": {participant.phone: participant.suggested_role for participant in participants},
            "participants": participants,
            "metadata": _transcript_metadata(raw_transcript),
        }

    normalized_mapping = {
        phone: role
        for phone, role in role_mapping.items()
        if role in {"user", "assistant", "system"}
    }
    participant_phones = [participant.phone for participant in participants]
    if not participant_phones or not all(phone in normalized_mapping for phone in participant_phones):
        return {
            "status": "role_mapping_required",
            "participants": participants,
            "metadata": _transcript_metadata(raw_transcript),
        }

    if "assistant" not in normalized_mapping.values():
        return {
            "status": "role_mapping_required",
            "participants": participants,
            "metadata": _transcript_metadata(raw_transcript),
        }
    return {
        "status": "ready",
        "role_mapping": normalized_mapping,
        "participants": participants,
        "metadata": _transcript_metadata(raw_transcript),
    }


def _extract_participants(raw_transcript: dict[str, Any]) -> list[ChatLabParticipantOption]:
    participants_raw = raw_transcript.get("participants")
    participants: list[ChatLabParticipantOption] = []
    if isinstance(participants_raw, list):
        for item in participants_raw:
            if not isinstance(item, dict):
                continue
            phone = str(item.get("phone") or "").strip()
            if not phone:
                continue
            participants.append(
                ChatLabParticipantOption(
                    phone=phone,
                    label=str(item.get("label") or phone),
                    suggested_role=str(item.get("role") or "other"),
                )
            )
    if participants:
        return participants

    discovered = []
    for message in raw_transcript.get("messages", []):
        if not isinstance(message, dict):
            continue
        phone = str(message.get("phone") or message.get("from") or "").strip()
        if phone and phone not in discovered:
            discovered.append(phone)
    return [
        ChatLabParticipantOption(phone=phone, label=phone, suggested_role="other")
        for phone in discovered
    ]


def _normalize_import_messages(
    raw_transcript: dict[str, Any],
    role_mapping: Mapping[str, str],
) -> list[ChatLabMessageView]:
    normalized: list[ChatLabMessageView] = []
    for index, raw_message in enumerate(raw_transcript.get("messages", []), start=1):
        if not isinstance(raw_message, dict):
            raise ChatLabImportError("Transcript message entries must be objects.")

        message_id = str(raw_message.get("id") or f"imp_{index}")
        content = str(raw_message.get("content") or "").strip()
        if not content:
            continue

        timestamp = _parse_import_timestamp(raw_message.get("timestamp") or raw_message.get("created_at"))
        phone = str(raw_message.get("phone") or raw_message.get("from") or "").strip() or None
        role = str(raw_message.get("role") or "").lower()
        if role not in {"user", "assistant", "system"}:
            mapped_role = role_mapping.get(phone or "", "other")
            role = "system" if mapped_role == "other" else mapped_role

        normalized.append(
            ChatLabMessageView(
                id=message_id,
                role=role,
                content=content,
                created_at=timestamp.isoformat(),
                phone=phone,
                internal_json=(
                    raw_message.get("internal_json")
                    if isinstance(raw_message.get("internal_json"), dict)
                    else None
                ),
                model=str(raw_message.get("model") or ""),
            )
        )
    return sorted(normalized, key=lambda item: item.created_at)


def _parse_import_timestamp(raw_value: Any) -> datetime:
    if isinstance(raw_value, str) and raw_value:
        try:
            parsed = datetime.fromisoformat(raw_value)
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
    return datetime.now(UTC)


def _transcript_metadata(raw_transcript: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": raw_transcript.get("schema_version") or _TRANSCRIPT_SCHEMA_VERSION,
        "source_label": raw_transcript.get("source_label"),
        "source_type": _resolve_import_source_type(raw_transcript),
        "language": raw_transcript.get("language"),
        "message_count": len(raw_transcript.get("messages", [])),
    }


def _resolve_import_source_type(raw_transcript: dict[str, Any]) -> str:
    source_type = str(raw_transcript.get("source_type") or "").strip().lower()
    if source_type == "imported_test":
        return "imported_test"
    return "imported_real"
