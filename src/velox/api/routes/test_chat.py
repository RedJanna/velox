"""Chat Lab endpoints and UI for admin-operated testing workflows."""

import asyncio
import contextlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from string import Formatter
from typing import Annotated, Any
from uuid import uuid4

import asyncpg
import httpx
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field, model_validator

from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.api.middleware.auth import require_role
from velox.api.routes.test_chat_export import (
    ConversationExportPayload,
    ExportFormat,
    build_export_file_content,
    build_export_filename,
)
from velox.api.routes.test_chat_ui import TEST_CHAT_HTML
from velox.api.routes.whatsapp_webhook import (
    _activate_handoff_guard,
    _detect_message_language,
    _extract_user_message_parts,
    _finalize_handoff_transition,
    _HandoffToolAdapter,
    _hash_phone,
    _is_human_override_active,
    _mask_phone,
    _merge_entities_with_context,
    _normalize_text,
    _NotifyToolAdapter,
    _run_message_pipeline,
    _should_activate_handoff_lock,
)
from velox.config.constants import HoldStatus, Role
from velox.config.settings import settings
from velox.core.chat_lab_attachments import (
    ChatLabAttachmentError,
    ChatLabAttachmentService,
    serialize_asset_for_client,
)
from velox.core.chat_lab_feedback import (
    ChatLabFeedbackError,
    ChatLabFeedbackService,
    ChatLabImportError,
    FeedbackConversationNotFoundError,
    FeedbackMessageNotFoundError,
)
from velox.core.chat_lab_metrics import compute_feedback_metrics
from velox.core.chat_lab_report import ChatLabReportError, ChatLabReportService
from velox.core.hotel_profile_loader import get_profile, load_all_profiles
from velox.core.template_engine import get_all_templates, load_templates
from velox.db.repositories.conversation import ConversationRepository
from velox.llm.client import get_llm_client
from velox.models.chat_lab_feedback import (
    ChatLabCatalogResponse,
    ChatLabFeedbackRequest,
    ChatLabFeedbackResponse,
    ChatLabImportListResponse,
    ChatLabImportRequest,
    ChatLabImportResponse,
    ChatLabReportRequest,
    ChatLabReportResponse,
)
from velox.models.conversation import Conversation, Message
from velox.utils.operation_mode import REDIS_OPERATION_MODE_KEY, sync_operation_mode_from_redis

logger = structlog.get_logger(__name__)


def _chat_lab_dependencies() -> list[Any]:
    """Protect Chat Lab APIs with admin auth in production."""
    if settings.app_env == "production":
        return [Depends(require_role(Role.ADMIN))]
    return []


router = APIRouter(prefix="/test", tags=["test-chat"], dependencies=_chat_lab_dependencies())
ui_router = APIRouter(tags=["test-chat-ui"])
formatter = WhatsAppFormatter()
attachment_service = ChatLabAttachmentService()

TEST_PHONE_PREFIX = "test_"
_chat_locks: dict[str, asyncio.Lock] = {}
_chat_locks_guard = asyncio.Lock()
IDEMPOTENT_ASSISTANT_WAIT_ATTEMPTS = 20
IDEMPOTENT_ASSISTANT_WAIT_SECONDS = 0.1
_SESSION_REOPEN_TEMPLATE_NAME = "hello_world"
_SESSION_REOPEN_TEMPLATE_LANGUAGE = "en_US"
_SESSION_REOPEN_META_CODES = {470, 131047, 131051}


class TestChatRequest(BaseModel):
    """Inbound payload for Chat Lab message simulation."""

    message: str = Field(default="", max_length=4096)
    phone: str = Field(default="test_user_123")
    client_message_id: str | None = Field(default=None, min_length=1, max_length=128)
    reply_to_message_id: str | None = Field(default=None, min_length=1, max_length=128)
    attachments: list[dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_payload(self) -> "TestChatRequest":
        """Require text or at least one attachment."""
        has_text = bool(str(self.message or "").strip())
        has_attachments = bool(self.attachments)
        if not has_text and not has_attachments:
            raise ValueError("Mesaj veya en az bir dosya gerekli.")
        if len(self.attachments) > 5:
            raise ValueError("Tek mesajda en fazla 5 dosya gönderilebilir.")
        return self


class TestChatResponse(BaseModel):
    """Chat Lab reply payload with debug metadata."""

    reply: str
    user_message_id: str
    assistant_message_id: str
    blocked: bool = False
    block_reason: str | None = None
    internal_json: dict[str, Any]
    conversation: dict[str, Any]
    timestamp: str


class SetModelRequest(BaseModel):
    """Request payload for switching the active test model."""

    model: str = Field(min_length=1)


class SetModeRequest(BaseModel):
    """Request payload for switching the operation mode."""

    mode: str = Field(pattern=r"^(test|ai|approval|off)$")


class ConversationNoteRequest(BaseModel):
    """Persist one internal admin note for a live conversation."""

    conversation_id: str = Field(min_length=1)
    note: str = Field(min_length=1, max_length=4000)


def _ensure_test_phone(phone: str) -> str:
    if phone.startswith(TEST_PHONE_PREFIX):
        return phone
    return f"{TEST_PHONE_PREFIX}{phone}"


async def _get_chat_lock(phone_hash: str) -> asyncio.Lock:
    """Return one per-phone lock for serializing Chat Lab turns."""
    async with _chat_locks_guard:
        lock = _chat_locks.get(phone_hash)
        if lock is None:
            lock = asyncio.Lock()
            _chat_locks[phone_hash] = lock
        return lock


async def _wait_for_assistant_by_client_id(
    repository: ConversationRepository,
    conversation_id: Any,
    client_message_id: str,
) -> Message | None:
    """Poll shortly for assistant message created by another concurrent worker."""
    for _ in range(IDEMPOTENT_ASSISTANT_WAIT_ATTEMPTS):
        existing = await repository.get_assistant_by_client_message_id(conversation_id, client_message_id)
        if existing is not None:
            return existing
        await asyncio.sleep(IDEMPOTENT_ASSISTANT_WAIT_SECONDS)
    return None


def _serialize_message(message: Message) -> dict[str, Any]:
    internal_json = message.internal_json if isinstance(message.internal_json, dict) else {}
    raw_attachments = internal_json.get("attachments")
    attachments: list[dict[str, Any]] = []
    if isinstance(raw_attachments, list):
        for item in raw_attachments:
            if not isinstance(item, dict):
                continue
            attachments.append(
                {
                    "asset_id": str(item.get("asset_id") or ""),
                    "kind": str(item.get("kind") or ""),
                    "mime_type": str(item.get("mime_type") or ""),
                    "file_name": str(item.get("file_name") or ""),
                    "size_bytes": int(item.get("size_bytes") or 0),
                    "content_url": str(item.get("content_url") or ""),
                }
            )
    return {
        "id": str(message.id),
        "role": message.role,
        "content": message.content,
        "internal_json": message.internal_json,
        "attachments": attachments,
        "created_at": message.created_at.isoformat(),
        "send_blocked": bool(internal_json.get("send_blocked")),
        "approval_pending": bool(internal_json.get("approval_pending")),
        "rejected": bool(internal_json.get("rejected")),
        "internal_note": bool(internal_json.get("internal_note")),
        "whatsapp_message_id": str(internal_json.get("whatsapp_message_id") or "").strip() or None,
        "local_status": _derive_delivery_state(
            send_blocked=bool(internal_json.get("send_blocked")),
            approval_pending=bool(internal_json.get("approval_pending")),
            rejected=bool(internal_json.get("rejected")),
            whatsapp_message_id=str(internal_json.get("whatsapp_message_id") or "").strip() or None,
            provider_status=str(internal_json.get("provider_status") or "").strip() or None,
        ),
        "provider_status": str(internal_json.get("provider_status") or "").strip() or "unknown",
        "provider_status_updated_at": str(internal_json.get("provider_status_updated_at") or "").strip() or None,
        "provider_sent_at": str(internal_json.get("provider_sent_at") or "").strip() or None,
        "delivered_at": str(internal_json.get("delivered_at") or "").strip() or None,
        "read_at": str(internal_json.get("read_at") or "").strip() or None,
        "failed_at": str(internal_json.get("failed_at") or "").strip() or None,
        "provider_error": internal_json.get("provider_error") if isinstance(internal_json.get("provider_error"), dict) else None,
        "provider_events": internal_json.get("provider_events") if isinstance(internal_json.get("provider_events"), list) else [],
        "session_reopen_template_sent": bool(internal_json.get("session_reopen_template_sent")),
        "session_reopen_template_name": str(internal_json.get("session_reopen_template_name") or "").strip() or None,
        "session_reopen_template_sent_at": str(internal_json.get("session_reopen_template_sent_at") or "").strip() or None,
    }


def _build_attachment_summary(attachments: list[dict[str, Any]]) -> str:
    """Create short text describing attached assets for test pipeline context."""
    parts: list[str] = []
    for item in attachments:
        kind = str(item.get("kind") or "file")
        file_name = str(item.get("file_name") or kind)
        parts.append(f"{kind}:{file_name}")
    if not parts:
        return ""
    return "Kullanici dosya paylasti: " + ", ".join(parts[:5])


def _build_attachment_only_fallback_text(attachments: list[dict[str, Any]]) -> str:
    """Create visible message text when user sends only attachments."""
    labels = [str(item.get("file_name") or item.get("kind") or "dosya") for item in attachments]
    if not labels:
        return "Dosya gönderildi."
    return "Ek gönderildi: " + ", ".join(labels[:3])


def _extract_attachment_ids(payload: list[dict[str, str]]) -> list[str]:
    """Parse attachment ids from client payload."""
    ids: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        candidate = str(item.get("asset_id") or "").strip()
        if candidate:
            ids.append(candidate)
    return ids


def _extract_whatsapp_message_id(response_payload: dict[str, Any]) -> str | None:
    """Extract provider message id from WhatsApp API response payload."""
    messages = response_payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    first = messages[0]
    if not isinstance(first, dict):
        return None
    message_id = str(first.get("id") or "").strip()
    return message_id or None


def _conversation_state_value(conversation: Conversation) -> str:
    if hasattr(conversation.current_state, "value"):
        return str(conversation.current_state.value)
    return str(conversation.current_state)


def _conversation_intent_value(conversation: Conversation) -> str | None:
    if conversation.current_intent is None:
        return None
    if hasattr(conversation.current_intent, "value"):
        return str(conversation.current_intent.value)
    return str(conversation.current_intent)


async def _clear_human_override_cache(
    redis_client: Any | None,
    phone_hash: str,
) -> None:
    """Best-effort cleanup for phone-scoped human override cache."""
    if redis_client is None:
        return
    try:
        await redis_client.delete(f"velox:human_override:{phone_hash}")
    except Exception:
        logger.warning("test_chat_human_override_cache_clear_failed", phone_hash=phone_hash[:8] + "***")


def _serialize_conversation(conversation: Conversation) -> dict[str, Any]:
    return {
        "id": str(conversation.id),
        "state": _conversation_state_value(conversation),
        "intent": _conversation_intent_value(conversation),
        "language": conversation.language,
        "entities": conversation.entities_json,
        "risk_flags": conversation.risk_flags,
        "is_active": conversation.is_active,
    }


def _build_service_window(last_user_message_at: datetime | None) -> dict[str, Any]:
    """Derive customer service window state from the latest inbound user message."""
    if last_user_message_at is None:
        return {
            "window_state": "unknown",
            "window_expires_at": None,
            "window_remaining_seconds": None,
        }
    expires_at = last_user_message_at + timedelta(hours=24)
    remaining_seconds = int((expires_at - datetime.now(UTC)).total_seconds())
    if remaining_seconds <= 0:
        window_state = "closed"
    elif remaining_seconds <= 3600:
        window_state = "closing_soon"
    else:
        window_state = "open"
    return {
        "window_state": window_state,
        "window_expires_at": expires_at.isoformat(),
        "window_remaining_seconds": max(remaining_seconds, 0),
    }


def _extract_template_fields(template_text: str) -> list[str]:
    """Collect placeholder field names from a format string."""
    fields: list[str] = []
    formatter = Formatter()
    for _, field_name, _, _ in formatter.parse(template_text):
        if field_name and field_name not in fields:
            fields.append(field_name)
    return fields


class _SafeTemplateValues(dict[str, str]):
    """Return readable placeholders for missing values in template previews."""

    def __missing__(self, key: str) -> str:
        return f"[{key}]"


def _build_template_preview(template_text: str, variables: dict[str, str]) -> str:
    """Render template preview without failing on missing variables."""
    safe_values = _SafeTemplateValues(variables)
    with contextlib.suppress(Exception):
        return template_text.format_map(safe_values)
    return template_text


def _is_session_reopen_error(error: httpx.HTTPStatusError) -> bool:
    """Return True when Meta rejects a free-form send because the session window is closed."""
    if error.response.status_code not in {400, 403}:
        return False
    try:
        payload = error.response.json()
    except ValueError:
        return False
    if not isinstance(payload, dict):
        return False
    error_obj = payload.get("error")
    if not isinstance(error_obj, dict):
        return False
    code = error_obj.get("code")
    if isinstance(code, int):
        return code in _SESSION_REOPEN_META_CODES
    if isinstance(code, str) and code.isdigit():
        return int(code) in _SESSION_REOPEN_META_CODES
    return False


async def _send_with_session_reopen_fallback(
    *,
    whatsapp_client: Any,
    phone: str,
    send_operation: Any,
    reopen_state: dict[str, Any],
) -> Any:
    """Retry one outbound WhatsApp operation after sending the approved reopen template."""
    try:
        return await send_operation()
    except httpx.HTTPStatusError as error:
        if not _is_session_reopen_error(error):
            raise
        if reopen_state.get("sent"):
            raise

    logger.info("chat_lab_session_reopen_attempt", phone=_mask_phone(phone))
    await whatsapp_client.send_template_message(
        to=phone,
        template_name=_SESSION_REOPEN_TEMPLATE_NAME,
        language=_SESSION_REOPEN_TEMPLATE_LANGUAGE,
        components=[],
        force=True,
    )
    reopen_state["sent"] = True
    reopen_state["template_name"] = _SESSION_REOPEN_TEMPLATE_NAME
    reopen_state["sent_at"] = datetime.now(UTC).isoformat()
    return await send_operation()


def _derive_delivery_state(
    *,
    send_blocked: bool,
    approval_pending: bool,
    rejected: bool,
    whatsapp_message_id: str | None,
    provider_status: str | None = None,
) -> str:
    """Map known assistant metadata into one conservative UI delivery state."""
    normalized_provider_status = str(provider_status or "").strip().lower()
    if rejected:
        return "failed"
    if normalized_provider_status in {"failed", "undelivered"}:
        return "failed"
    if approval_pending or send_blocked:
        return "pending_approval"
    if normalized_provider_status in {"read", "delivered", "sent"}:
        return normalized_provider_status
    if whatsapp_message_id:
        return "accepted"
    return "unknown"


def _resolve_test_chat_reply_context(
    conversation: Conversation,
    reply_to_message_id: str | None,
) -> dict[str, Any] | None:
    """Resolve a Chat Lab reply target using persisted message row ids."""
    normalized_reply_to_message_id = str(reply_to_message_id or "").strip()
    if not normalized_reply_to_message_id:
        return None

    for target in conversation.messages:
        if str(target.id) != normalized_reply_to_message_id:
            continue
        return {
            "present": True,
            "resolved": True,
            "reply_to_message_id": normalized_reply_to_message_id,
            "target_message_db_id": str(target.id) if target.id is not None else None,
            "target_role": target.role,
            "target_content": str(target.content or "")[:500],
        }

    return {
        "present": True,
        "resolved": False,
        "reason": "target_not_found",
        "reply_to_message_id": normalized_reply_to_message_id,
    }


@router.post("/chat", response_model=TestChatResponse)
async def test_chat(body: TestChatRequest, request: Request) -> TestChatResponse:
    """Process a test message synchronously and return the assistant reply."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    phone = _ensure_test_phone(body.phone)
    repository = ConversationRepository()
    phone_hash = _hash_phone(phone)
    chat_lock = await _get_chat_lock(phone_hash)
    normalized_client_message_id = (body.client_message_id or "").strip() or f"cl_{uuid4().hex}"
    normalized_reply_to_message_id = str(body.reply_to_message_id or "").strip() or None
    dispatcher = getattr(request.app.state, "tool_dispatcher", None)
    redis_client = getattr(request.app.state, "redis", None)
    db_pool = getattr(request.app.state, "db_pool", None)
    tools = {
        "handoff": _HandoffToolAdapter(dispatcher) if dispatcher is not None else None,
        "notify": _NotifyToolAdapter(dispatcher) if dispatcher is not None else None,
    }
    attachment_ids = _extract_attachment_ids(body.attachments)
    try:
        resolved_assets = await attachment_service.resolve_assets_for_message(
            hotel_id=settings.elektra_hotel_id,
            attachment_ids=attachment_ids,
        )
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    serialized_attachments = [serialize_asset_for_client(asset) for asset in resolved_assets]

    async with chat_lock:
        conversation = await repository.get_active_by_phone(settings.elektra_hotel_id, phone_hash)

        if conversation is None:
            initial_language = _detect_message_language(body.message, "tr")
            conversation = Conversation(
                hotel_id=settings.elektra_hotel_id,
                phone_hash=phone_hash,
                phone_display=_mask_phone(phone),
                language=initial_language,
            )
            conversation = await repository.create(conversation)
        if conversation.id is None:
            raise HTTPException(status_code=500, detail="Konuşma kimliği eksik")

        existing_assistant = await repository.get_assistant_by_client_message_id(
            conversation.id,
            normalized_client_message_id,
        )
        if existing_assistant is not None:
            latest_conversation = await repository.get_by_id(conversation.id)
            safe_conversation = latest_conversation or conversation
            internal_json = (
                existing_assistant.internal_json
                if isinstance(existing_assistant.internal_json, dict)
                else {}
            )
            return TestChatResponse(
                reply=existing_assistant.content,
                user_message_id="",
                assistant_message_id=str(existing_assistant.id),
                blocked=False,
                block_reason=None,
                internal_json=internal_json,
                conversation=_serialize_conversation(safe_conversation),
                timestamp=datetime.now(UTC).isoformat(),
            )

        normalized = _normalize_text(body.message)
        attachment_context = _build_attachment_summary(serialized_attachments)
        message_for_pipeline = normalized
        if attachment_context:
            message_for_pipeline = f"{normalized}\n\n[{attachment_context}]" if normalized else attachment_context
        if len(message_for_pipeline) > 4096:
            message_for_pipeline = message_for_pipeline[:4096]
        display_content = normalized or _build_attachment_only_fallback_text(serialized_attachments)

        detected_language = _detect_message_language(message_for_pipeline, conversation.language)
        if conversation.language != detected_language:
            conversation.language = detected_language
            await repository.update_language(conversation.id, detected_language)

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=display_content,
            client_message_id=normalized_client_message_id,
            internal_json={
                "source_type": "live_test_chat",
                "client_message_id": normalized_client_message_id,
                "reply_to_message_id": normalized_reply_to_message_id,
                "attachments": serialized_attachments,
                "route_audit": {
                    "route": "/api/v1/test/chat",
                    "received_at": datetime.now(UTC).isoformat(),
                },
            },
        )
        try:
            await repository.add_message(user_message)
            if user_message.id is not None and attachment_ids:
                await attachment_service.attach_assets_to_message(
                    asset_ids=attachment_ids,
                    message_id=user_message.id,
                )
        except asyncpg.UniqueViolationError:
            existing_assistant = await _wait_for_assistant_by_client_id(
                repository,
                conversation.id,
                normalized_client_message_id,
            )
            if existing_assistant is None:
                raise HTTPException(
                    status_code=409,
                    detail="Aynı istek zaten işleniyor",
                ) from None
            latest_conversation = await repository.get_by_id(conversation.id)
            safe_conversation = latest_conversation or conversation
            internal_json = (
                existing_assistant.internal_json
                if isinstance(existing_assistant.internal_json, dict)
                else {}
            )
            return TestChatResponse(
                reply=existing_assistant.content,
                user_message_id="",
                assistant_message_id=str(existing_assistant.id),
                blocked=False,
                block_reason=None,
                internal_json=internal_json,
                conversation=_serialize_conversation(safe_conversation),
                timestamp=datetime.now(UTC).isoformat(),
            )
        conversation.messages = await repository.get_recent_messages(conversation.id, count=20)
        reply_context = _resolve_test_chat_reply_context(conversation, normalized_reply_to_message_id)
        if reply_context:
            user_internal_json = dict(user_message.internal_json or {})
            user_internal_json["reply_context"] = reply_context
            user_message.internal_json = user_internal_json
            if user_message.id is not None:
                await repository.update_message_internal_json(user_message.id, user_internal_json)

        human_override = await _is_human_override_active(
            conversation.phone_hash,
            conversation.id,
            redis_client,
        )
        if human_override:
            latest_conversation = await repository.get_by_id(conversation.id)
            safe_conversation = latest_conversation or conversation
            internal_json = dict(user_message.internal_json or {})
            internal_json["human_override_blocked"] = True
            internal_json["handoff_lock_activated"] = True
            if user_message.id is not None:
                await repository.update_message_internal_json(user_message.id, internal_json)
            return TestChatResponse(
                reply="",
                user_message_id=str(user_message.id) if user_message.id is not None else "",
                assistant_message_id="",
                blocked=True,
                block_reason="human_override_active",
                internal_json=internal_json,
                conversation=_serialize_conversation(safe_conversation),
                timestamp=datetime.now(UTC).isoformat(),
            )

        llm_response = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=message_for_pipeline,
            dispatcher=dispatcher,
            expected_language=detected_language,
            reply_context=reply_context,
        )
        current_state_value = (
            str(conversation.current_state.value)
            if hasattr(conversation.current_state, "value")
            else str(conversation.current_state or "GREETING")
        )
        merged_entities = _merge_entities_with_context(
            conversation.entities_json,
            llm_response.internal_json.entities if isinstance(llm_response.internal_json.entities, dict) else {},
        )
        llm_response.internal_json.entities = merged_entities
        conversation.entities_json = merged_entities
        await repository.update_state(
            conversation_id=conversation.id,
            state=str(llm_response.internal_json.state or current_state_value),
            intent=str(llm_response.internal_json.intent or "").strip() or None,
            entities=merged_entities or None,
            risk_flags=llm_response.internal_json.risk_flags or None,
        )
        next_state = str(llm_response.internal_json.state or current_state_value)
        handoff_lock_activated = _should_activate_handoff_lock(
            next_state,
            llm_response.internal_json.handoff,
        )
        if handoff_lock_activated:
            await _activate_handoff_guard(
                conversation_repository=repository,
                conversation=conversation,
                llm_response=llm_response,
                phone=phone,
                tools=tools,
                redis_client=redis_client,
            )

        outbound_messages = _extract_user_message_parts(llm_response)
        if not outbound_messages:
            outbound_messages = [llm_response.user_message]
        if handoff_lock_activated and outbound_messages:
            outbound_messages = outbound_messages[:1]
        reply_text = formatter.truncate(outbound_messages[0])
        assistant_internal = llm_response.internal_json.model_dump(mode="json")
        assistant_internal["client_message_id"] = normalized_client_message_id
        assistant_internal["human_override_blocked"] = False
        assistant_internal["handoff_lock_activated"] = handoff_lock_activated
        if len(outbound_messages) > 1:
            assistant_internal["user_message_parts"] = [formatter.truncate(message) for message in outbound_messages]

        assistant_message: Message | None = None
        for index, raw_message in enumerate(outbound_messages, start=1):
            part_client_message_id = normalized_client_message_id
            if index > 1:
                part_client_message_id = f"{normalized_client_message_id}__part{index}"

            part_text = formatter.truncate(raw_message)
            part_internal = dict(assistant_internal)
            part_internal["message_part_index"] = index
            part_internal["message_part_total"] = len(outbound_messages)

            candidate = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=part_text,
                client_message_id=part_client_message_id,
                internal_json=part_internal,
                tool_calls=part_internal.get("tool_calls") or None,
            )
            try:
                saved_message = await repository.add_message(candidate)
            except asyncpg.UniqueViolationError:
                existing_assistant = await repository.get_assistant_by_client_message_id(
                    conversation.id,
                    part_client_message_id,
                )
                if existing_assistant is None:
                    raise
                saved_message = existing_assistant

            if assistant_message is None:
                assistant_message = saved_message
            conversation.messages.append(saved_message)

        if assistant_message is None:
            raise HTTPException(status_code=500, detail="Asistan mesajı oluşturulamadı")

        if handoff_lock_activated:
            await _finalize_handoff_transition(
                conversation=conversation,
                llm_response=llm_response,
                phone=phone,
                tools=tools,
                db_pool=db_pool,
                escalation_result=None,
            )

        return TestChatResponse(
            reply=reply_text,
            user_message_id=str(user_message.id) if user_message.id is not None else "",
            assistant_message_id=str(assistant_message.id),
            blocked=False,
            block_reason=None,
            internal_json=assistant_internal,
            conversation=_serialize_conversation(conversation),
            timestamp=datetime.now(UTC).isoformat(),
        )


@router.get("/chat/history")
async def test_chat_history(request: Request, phone: str = "test_user_123") -> dict[str, Any]:
    """Load conversation history for one test phone number."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    repository = ConversationRepository()
    conversation = await repository.get_active_by_phone(
        settings.elektra_hotel_id,
        _hash_phone(_ensure_test_phone(phone)),
    )
    if conversation is None:
        return {"messages": [], "conversation": None}
    if conversation.id is None:
        raise HTTPException(status_code=500, detail="Konuşma kimliği eksik")

    messages = await repository.get_messages(conversation.id, limit=100, offset=0)
    last_user_message_at = next((message.created_at for message in reversed(messages) if message.role == "user"), None)
    return {
        "messages": [_serialize_message(message) for message in messages],
        "conversation": _serialize_conversation(conversation),
        **_build_service_window(last_user_message_at),
    }


@router.post("/chat/reset")
async def test_chat_reset(request: Request, phone: str = "test_user_123") -> dict[str, str]:
    """Close the active Chat Lab conversation and start fresh on the next turn."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    repository = ConversationRepository()
    conversation = await repository.get_active_by_phone(
        settings.elektra_hotel_id,
        _hash_phone(_ensure_test_phone(phone)),
    )
    if conversation is None or conversation.id is None:
        return {"status": "no_active_conversation"}

    await repository.close(conversation.id)
    await _clear_human_override_cache(getattr(request.app.state, "redis", None), conversation.phone_hash)
    return {"status": "reset", "closed_conversation_id": str(conversation.id)}


@router.post("/chat/upload-asset")
async def upload_chat_asset(
    request: Request,
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    """Upload a Chat Lab attachment and return reusable metadata."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    file_name = file.filename or "upload.bin"
    try:
        file_bytes = await file.read()
    finally:
        await file.close()

    try:
        stored = await attachment_service.save_upload(
            hotel_id=settings.elektra_hotel_id,
            file_name=file_name,
            content_type=file.content_type,
            file_bytes=file_bytes,
        )
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "status": "uploaded",
        "asset": serialize_asset_for_client(stored),
    }


@router.delete("/chat/upload-asset/{asset_id}")
async def delete_chat_asset(request: Request, asset_id: str) -> dict[str, str]:
    """Delete one not-yet-sent Chat Lab attachment."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")
    try:
        await attachment_service.delete_asset(asset_id=asset_id, hotel_id=settings.elektra_hotel_id)
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"status": "deleted", "asset_id": asset_id}


@router.get("/chat/upload-asset/{asset_id}/content")
async def get_chat_asset_content(request: Request, asset_id: str) -> FileResponse:
    """Serve one uploaded attachment to authenticated Chat Lab users."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")
    try:
        asset = await attachment_service.get_asset_for_hotel(
            asset_id=asset_id,
            hotel_id=settings.elektra_hotel_id,
        )
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    storage_path = Path(asset.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Dosya depoda bulunamadı.")

    return FileResponse(
        path=storage_path,
        media_type=asset.mime_type,
        filename=asset.file_name,
    )


@router.get("/chat/export")
async def test_chat_export(
    request: Request,
    phone: str = "test_user_123",
    export_format: Annotated[ExportFormat, Query(alias="format")] = "md",
) -> Response:
    """Export the active test conversation as json/pdf/md/txt."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    repository = ConversationRepository()
    conversation = await repository.get_active_by_phone(
        settings.elektra_hotel_id,
        _hash_phone(_ensure_test_phone(phone)),
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Bu telefon için aktif bir konuşma bulunamadı")
    if conversation.id is None:
        raise HTTPException(status_code=500, detail="Konuşma kimliği eksik")

    messages = await repository.get_messages(conversation.id, limit=500, offset=0)
    exported_at = datetime.now(UTC)
    payload = ConversationExportPayload(
        phone=phone,
        conversation=_serialize_conversation(conversation),
        messages=[_serialize_message(message) for message in messages],
        exported_at=exported_at,
    )
    content, media_type, extension = build_export_file_content(export_format, payload)
    filename = build_export_filename(phone=phone, extension=extension, exported_at=exported_at)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/chat/feedback-catalog", response_model=ChatLabCatalogResponse)
async def get_feedback_catalog() -> ChatLabCatalogResponse:
    """Return catalog data for feedback forms, imports, and reports."""
    service = ChatLabFeedbackService()
    return await service.get_catalog()


@router.post("/chat/feedback", response_model=ChatLabFeedbackResponse)
async def test_chat_feedback(
    body: ChatLabFeedbackRequest,
    request: Request,
) -> ChatLabFeedbackResponse:
    """Persist one admin review for a selected assistant reply."""
    if (
        body.source_type in {"live_test_chat", "live_conversation"}
        and getattr(request.app.state, "db_pool", None) is None
    ):
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    service = ChatLabFeedbackService()
    try:
        return await service.submit_feedback(body)
    except FeedbackConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except FeedbackMessageNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ChatLabImportError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ChatLabFeedbackError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("test_chat_feedback_unexpected_error")
        raise HTTPException(status_code=500, detail=f"Beklenmeyen feedback hatasi: {error}") from error


@router.get("/chat/import-files", response_model=ChatLabImportListResponse)
async def list_chat_import_files() -> ChatLabImportListResponse:
    """List available admin transcript imports."""
    service = ChatLabFeedbackService()
    return await service.list_import_files()


@router.post("/chat/import-load", response_model=ChatLabImportResponse)
async def load_chat_import(body: ChatLabImportRequest) -> ChatLabImportResponse:
    """Preview or confirm one transcript import file."""
    service = ChatLabFeedbackService()
    try:
        return await service.load_import(body)
    except ChatLabImportError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("test_chat_import_unexpected_error")
        raise HTTPException(status_code=500, detail=f"Beklenmeyen import hatasi: {error}") from error


@router.post("/chat/report", response_model=ChatLabReportResponse)
async def generate_chat_lab_report(body: ChatLabReportRequest) -> ChatLabReportResponse:
    """Generate one aggregate bad-feedback report."""
    service = ChatLabReportService()
    try:
        return await service.generate_report(body)
    except ChatLabReportError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        logger.exception("test_chat_report_unexpected_error")
        raise HTTPException(status_code=500, detail=f"Beklenmeyen rapor hatasi: {error}") from error


@router.get("/chat/mode")
async def get_operation_mode(request: Request) -> dict[str, str]:
    """Return the current operation mode (reads from Redis for cross-worker consistency)."""
    await sync_operation_mode_from_redis(getattr(request.app.state, "redis", None))
    return {"mode": settings.operation_mode}


@router.post("/chat/mode")
async def set_operation_mode(body: SetModeRequest, request: Request) -> dict[str, str]:
    """Change the operation mode at runtime (persisted to Redis for all workers)."""
    old_mode = settings.operation_mode
    settings.operation_mode = body.mode
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is not None:
        try:
            await redis_client.set(REDIS_OPERATION_MODE_KEY, body.mode)
        except Exception:
            logger.warning("operation_mode_redis_write_failed")
    logger.info(
        "operation_mode_changed",
        old_mode=old_mode,
        new_mode=body.mode,
    )
    return {"status": "ok", "old_mode": old_mode, "mode": body.mode}


@router.get("/chat/live-feed")
async def live_feed(request: Request, limit: int = 20, include_inactive: bool = False) -> dict[str, Any]:
    """Return recent real (non-test) conversations with their last messages.
    
    Args:
        limit: Maximum number of conversations to return (1-50)
        include_inactive: If true, also include closed/inactive conversations
    """
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    pool = request.app.state.db_pool
    capped_limit = min(max(limit, 1), 50)

    is_active_filter = "" if include_inactive else "AND c.is_active = true"

    try:
        rows = await pool.fetch(
            f"""
            SELECT c.id, c.phone_display, c.language, c.current_state,
                   c.current_intent, c.risk_flags, c.is_active,
                   c.human_override,
                   c.last_message_at, c.created_at,
                   (SELECT m.created_at FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'user'
                    ORDER BY m.created_at DESC LIMIT 1) AS last_user_message_at,
                   (SELECT count(*) FROM messages m WHERE m.conversation_id = c.id) AS msg_count,
                   (SELECT m.content FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'user'
                    ORDER BY m.created_at DESC LIMIT 1) AS last_user_msg,
                   (SELECT m.content FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS last_assistant_msg,
                    (SELECT m.internal_json->>'send_blocked' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS send_blocked,
                    (SELECT m.internal_json->>'approval_pending' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS approval_pending,
                    (SELECT m.internal_json->>'whatsapp_message_id' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS whatsapp_message_id,
                    (SELECT m.internal_json->>'provider_status' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS provider_status,
                    (SELECT m.internal_json->>'provider_status_updated_at' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS provider_status_updated_at,
                    (SELECT m.internal_json->>'session_reopen_template_sent' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS session_reopen_template_sent,
                    (SELECT m.internal_json->>'session_reopen_template_name' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS session_reopen_template_name,
                    (SELECT m.id FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS last_assistant_msg_id,
                    (SELECT m.internal_json->>'rejected' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS rejected
            FROM conversations c
            WHERE c.phone_hash NOT LIKE 'test_%'
              {is_active_filter}
            ORDER BY c.last_message_at DESC
            LIMIT $1
            """,
            capped_limit,
        )
    except Exception as error:
        logger.exception("live_feed_query_error")
        raise HTTPException(status_code=500, detail=f"Canli akis sorgu hatasi: {error}") from error

    conversations = []
    for row in rows:
        service_window = _build_service_window(row["last_user_message_at"])
        delivery_state = _derive_delivery_state(
            send_blocked=str(row["send_blocked"] or "").lower() == "true",
            approval_pending=str(row["approval_pending"] or "").lower() == "true",
            rejected=str(row["rejected"] or "").lower() == "true",
            whatsapp_message_id=str(row["whatsapp_message_id"] or "").strip() or None,
            provider_status=str(row["provider_status"] or "").strip() or None,
        )
        conversations.append({
            "id": str(row["id"]),
            "phone_display": row["phone_display"] or "***",
            "language": row["language"] or "-",
            "state": row["current_state"] or "-",
            "intent": row["current_intent"] or "-",
            "risk_flags": list(row["risk_flags"] or []),
            "is_active": row["is_active"],
            "human_override": bool(row["human_override"]),
            "msg_count": row["msg_count"],
            "last_user_msg": (row["last_user_msg"] or "")[:500],
            "last_assistant_msg": (row["last_assistant_msg"] or "")[:500],
            "send_blocked": row["send_blocked"],
            "approval_pending": row["approval_pending"],
            "whatsapp_message_id": row["whatsapp_message_id"],
            "provider_status": row["provider_status"] or "unknown",
            "provider_status_updated_at": row["provider_status_updated_at"],
            "session_reopen_template_sent": str(row["session_reopen_template_sent"] or "").lower() == "true",
            "session_reopen_template_name": str(row["session_reopen_template_name"] or "").strip() or None,
            "last_assistant_msg_id": row["last_assistant_msg_id"],
            "rejected": row["rejected"],
            "last_message_at": row["last_message_at"].isoformat() if row["last_message_at"] else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "last_user_message_at": row["last_user_message_at"].isoformat() if row["last_user_message_at"] else None,
            "delivery_state": delivery_state,
            **service_window,
        })

    return {
        "conversations": conversations,
        "operation_mode": settings.operation_mode,
        "total": len(conversations),
    }


_STAY_STATUS_LABELS: dict[str, str] = {
    HoldStatus.PENDING_APPROVAL.value: "Onay Bekliyor",
    HoldStatus.PMS_PENDING.value: "PMS İşleniyor",
    HoldStatus.PMS_CREATED.value: "PMS Oluşturuldu",
    HoldStatus.PMS_FAILED.value: "PMS Hatası",
    HoldStatus.PAYMENT_PENDING.value: "Ödeme Bekliyor",
    HoldStatus.PAYMENT_EXPIRED.value: "Ödeme Süresi Doldu",
    HoldStatus.MANUAL_REVIEW.value: "İnceleme Gerekli",
    HoldStatus.APPROVED.value: "Onaylandı",
    HoldStatus.REJECTED.value: "Reddedildi",
    HoldStatus.CONFIRMED.value: "Kesinleşti",
    HoldStatus.CANCELLED.value: "İptal Edildi",
}
_STAY_STATUS_TONES: dict[str, str] = {
    HoldStatus.PENDING_APPROVAL.value: "warning",
    HoldStatus.PMS_PENDING.value: "warning",
    HoldStatus.PMS_CREATED.value: "info",
    HoldStatus.PMS_FAILED.value: "danger",
    HoldStatus.PAYMENT_PENDING.value: "warning",
    HoldStatus.PAYMENT_EXPIRED.value: "danger",
    HoldStatus.MANUAL_REVIEW.value: "danger",
    HoldStatus.APPROVED.value: "info",
    HoldStatus.REJECTED.value: "danger",
    HoldStatus.CONFIRMED.value: "success",
    HoldStatus.CANCELLED.value: "danger",
}
_APPROVE_ACTIONABLE_STAY_STATUSES = {
    HoldStatus.PENDING_APPROVAL.value,
    HoldStatus.APPROVED.value,
    HoldStatus.MANUAL_REVIEW.value,
    HoldStatus.PMS_FAILED.value,
}


def _parse_chat_payload(raw: object) -> dict[str, Any]:
    """Decode stringified JSON blobs used by admin-facing payloads."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (str, bytes, bytearray)):
        try:
            decoded = orjson.loads(raw)
        except Exception:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _load_profile_for_hotel(hotel_id: int) -> Any | None:
    """Resolve hotel profile from cache and refresh once when needed."""
    profile = get_profile(hotel_id)
    if profile is not None:
        return profile
    load_all_profiles()
    return get_profile(hotel_id)


def _localized_profile_value(value: object, language: str, fallback: str = "-") -> str:
    """Return localized profile text while preserving safe fallbacks."""
    if value is None:
        return fallback
    localized = getattr(value, language, None)
    if isinstance(localized, str) and localized.strip():
        return localized.strip()
    tr_value = getattr(value, "tr", None)
    if isinstance(tr_value, str) and tr_value.strip():
        return tr_value.strip()
    en_value = getattr(value, "en", None)
    if isinstance(en_value, str) and en_value.strip():
        return en_value.strip()
    text = str(value).strip()
    return text or fallback


def _profile_room_label(profile: Any | None, raw_value: object, language: str) -> str:
    """Translate stored room identifiers into human-readable labels."""
    if raw_value in (None, ""):
        return "-"
    value = str(raw_value).strip()
    if profile is not None:
        for room in getattr(profile, "room_types", []):
            candidates = {
                str(getattr(room, "id", "")).strip(),
                str(getattr(room, "pms_room_type_id", "")).strip(),
            }
            if value in candidates:
                return _localized_profile_value(getattr(room, "name", None), language, fallback=value)
    return value


def _profile_board_label(profile: Any | None, raw_value: object, language: str) -> str:
    """Translate stored board identifiers into human-readable labels."""
    if raw_value in (None, ""):
        return "-"
    value = str(raw_value).strip()
    if profile is not None:
        for board in getattr(profile, "board_types", []):
            candidates = {
                str(getattr(board, "id", "")).strip(),
                str(getattr(board, "code", "")).strip(),
            }
            if value in candidates:
                return _localized_profile_value(getattr(board, "name", None), language, fallback=value)
    return value


def _parse_iso_date(value: object) -> date | None:
    """Parse YYYY-MM-DD values emitted by stay drafts."""
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _stay_status_meta(status: object) -> tuple[str, str]:
    """Map stay workflow states into UI badge metadata."""
    normalized = str(status or "").strip().upper()
    if not normalized:
        return ("Durum Bilinmiyor", "muted")
    return (
        _STAY_STATUS_LABELS.get(normalized, normalized.replace("_", " ").title()),
        _STAY_STATUS_TONES.get(normalized, "muted"),
    )


def _stay_hold_approve_state(hold_row: dict[str, Any]) -> tuple[bool, str]:
    """Mirror admin approve constraints so Chat Lab buttons match backend rules."""
    current_status = str(hold_row.get("status") or "").strip().upper()
    if current_status in {
        HoldStatus.PMS_PENDING.value,
        HoldStatus.PMS_CREATED.value,
        HoldStatus.PAYMENT_PENDING.value,
        HoldStatus.CONFIRMED.value,
    }:
        return (False, "Rezervasyon zaten işlenmiş durumda.")
    if current_status not in _APPROVE_ACTIONABLE_STAY_STATUSES:
        return (False, "Bu statüde onay aksiyonu kullanılamaz.")
    manual_review_reason = str(hold_row.get("manual_review_reason") or "").strip()
    if current_status == HoldStatus.MANUAL_REVIEW.value:
        create_state_uncertain = manual_review_reason in {
            "create_missing_identifiers",
            "create_unverified_after_readback",
        }
        if hold_row.get("pms_reservation_id") or hold_row.get("voucher_no") or create_state_uncertain:
            return (False, "Belirsiz PMS durumu nedeniyle manuel inceleme gerekli.")
    return (True, "")


def _stay_hold_cancel_state(hold_row: dict[str, Any]) -> tuple[str | None, bool, str]:
    """Choose the cancel action that should be exposed to Chat Lab."""
    current_status = str(hold_row.get("status") or "").strip().upper()
    if current_status in {HoldStatus.CANCELLED.value, HoldStatus.REJECTED.value}:
        return (None, False, "Rezervasyon zaten kapatılmış durumda.")
    if hold_row.get("pms_reservation_id") or hold_row.get("voucher_no"):
        return ("cancel_reservation", True, "")
    if current_status in {
        HoldStatus.PENDING_APPROVAL.value,
        HoldStatus.PAYMENT_PENDING.value,
    }:
        return ("reject_hold", True, "PMS kaydı oluşmadığı için yerel hold iptal edilecek.")
    return (None, False, "PMS rezervasyon kimliği bulunmadığı için iptal aksiyonu kapalı.")


def _extract_reservation_hint_from_internal(internal_json: dict[str, Any]) -> dict[str, Any]:
    """Extract reservation detail hints from approval.updated tool payloads."""
    if not isinstance(internal_json, dict):
        return {}
    tool_results = internal_json.get("tool_results")
    if not isinstance(tool_results, dict):
        return {}
    readback_payload = tool_results.get("booking_get_reservation")
    if not isinstance(readback_payload, dict):
        return {}
    result_payload = readback_payload.get("result")
    if not isinstance(result_payload, dict):
        return {}
    raw_data = result_payload.get("raw_data")
    if not isinstance(raw_data, dict):
        raw_data = {}

    hint: dict[str, Any] = {}
    hint["guest_name"] = (
        str(raw_data.get("contact_name") or raw_data.get("guest_name") or "").strip() or None
    )
    hint["checkin_date"] = (
        str(raw_data.get("checkin_date") or raw_data.get("checkin") or "").strip() or None
    )
    hint["checkout_date"] = (
        str(raw_data.get("checkout_date") or raw_data.get("checkout") or "").strip() or None
    )
    hint["room_label"] = str(raw_data.get("room_type") or "").strip() or None
    hint["board_label"] = str(raw_data.get("board_type") or "").strip() or None

    total_price = result_payload.get("total_price")
    if total_price in (None, ""):
        total_price = raw_data.get("total_price")
    hint["total_price"] = total_price
    hint["currency_display"] = (
        str(result_payload.get("currency_code") or raw_data.get("currency_code") or "").strip() or None
    )
    return hint


def _build_guest_info(conv_row: Any, hold_row: Any, reservation_hint: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the Chat Lab guest rail payload from conversation and stay hold data."""
    language = str(conv_row["language"] or "tr").strip().lower() or "tr"
    hotel_id = int(conv_row["hotel_id"] or settings.elektra_hotel_id)
    profile = _load_profile_for_hotel(hotel_id)
    resolved_hint = reservation_hint if isinstance(reservation_hint, dict) else {}

    if hold_row is None:
        return {
            "available": False,
            "info_status_label": "Misafir bilgi durumu: rezervasyon kaydı bağlı değil",
            "info_status_tone": "muted",
            "guest_name": "-",
            "phone": conv_row["phone_display"] or "***",
            "email": "-",
            "nationality": "-",
            "language": language,
            "checkin_date": "-",
            "checkout_date": "-",
            "nights": 0,
            "adults": 0,
            "children": 0,
            "room_label": "-",
            "board_label": "-",
            "total_price_display": "-",
            "hold_id": None,
            "hold_status": None,
            "hold_status_label": "Rezervasyon Kaydı Yok",
            "hold_status_tone": "muted",
            "reservation_reference": None,
            "status_detail": "Bu konuşma için henüz stay hold veya Elektra rezervasyonu bağlanmadı.",
            "approve_enabled": False,
            "approve_reason": "Onaylanacak bir stay hold bulunmuyor.",
            "cancel_enabled": False,
            "cancel_reason": "İptal edilecek bir stay hold bulunmuyor.",
            "cancel_action": None,
        }

    draft = _parse_chat_payload(hold_row.get("draft_json"))
    status_label, status_tone = _stay_status_meta(hold_row.get("status"))
    approve_enabled, approve_reason = _stay_hold_approve_state(hold_row)
    cancel_action, cancel_enabled, cancel_reason = _stay_hold_cancel_state(hold_row)
    checkin_date = _parse_iso_date(draft.get("checkin_date"))
    checkout_date = _parse_iso_date(draft.get("checkout_date"))
    nights = (checkout_date - checkin_date).days if checkin_date and checkout_date and checkout_date > checkin_date else 0
    reservation_reference = (
        str(hold_row.get("voucher_no") or "").strip()
        or str(hold_row.get("reservation_no") or "").strip()
        or str(hold_row.get("pms_reservation_id") or "").strip()
        or None
    )
    has_pms_reservation = bool(
        str(hold_row.get("pms_reservation_id") or "").strip() or str(hold_row.get("voucher_no") or "").strip()
    )
    checkin_value = draft.get("checkin_date") or resolved_hint.get("checkin_date")
    checkout_value = draft.get("checkout_date") or resolved_hint.get("checkout_date")
    checkin_date = _parse_iso_date(checkin_value)
    checkout_date = _parse_iso_date(checkout_value)
    nights = (checkout_date - checkin_date).days if checkin_date and checkout_date and checkout_date > checkin_date else 0

    room_label = _profile_room_label(profile, draft.get("room_type_id"), language)
    if room_label == "-":
        room_label = str(resolved_hint.get("room_label") or "-")
    board_label = _profile_board_label(profile, draft.get("board_type_id"), language)
    if board_label == "-":
        board_label = str(resolved_hint.get("board_label") or "-")

    adults = int(draft.get("adults") or 0)
    if adults <= 0:
        adults = int(resolved_hint.get("adults") or 0)
    children = len(draft.get("chd_ages") or [])
    if children <= 0:
        children = int(resolved_hint.get("children") or 0)

    total_price = draft.get("total_price_eur")
    if total_price in (None, ""):
        total_price = resolved_hint.get("total_price")
    currency_display = (
        str(draft.get("currency_display") or resolved_hint.get("currency_display") or "EUR").strip() or "EUR"
    )

    return {
        "available": True,
        "info_status_label": (
            "Misafir bilgi durumu: stay hold + PMS rezervasyonu bağlı"
            if has_pms_reservation
            else "Misafir bilgi durumu: stay hold bağlı"
        ),
        "info_status_tone": "success" if reservation_reference else "warning",
        "guest_name": str(draft.get("guest_name") or resolved_hint.get("guest_name") or "").strip() or "-",
        "phone": str(draft.get("phone") or "").strip() or conv_row["phone_display"] or "***",
        "email": str(draft.get("email") or "").strip() or "-",
        "nationality": str(draft.get("nationality") or "").strip() or "-",
        "language": language,
        "checkin_date": checkin_date.isoformat() if checkin_date else "-",
        "checkout_date": checkout_date.isoformat() if checkout_date else "-",
        "nights": nights,
        "adults": adults,
        "children": children,
        "room_label": room_label,
        "board_label": board_label,
        "total_price_display": (
            f"{total_price} {currency_display}"
            if total_price not in (None, "")
            else "-"
        ),
        "hold_id": str(hold_row.get("hold_id") or "").strip() or None,
        "hold_status": str(hold_row.get("status") or "").strip() or None,
        "hold_status_label": status_label,
        "hold_status_tone": status_tone,
        "reservation_reference": reservation_reference,
        "pms_reservation_id": str(hold_row.get("pms_reservation_id") or "").strip() or None,
        "voucher_no": str(hold_row.get("voucher_no") or "").strip() or None,
        "reservation_no": str(hold_row.get("reservation_no") or "").strip() or None,
        "status_detail": cancel_reason or approve_reason or "Rezervasyon aksiyonları mevcut durum ve PMS kayıtlarına göre hazırlanmıştır.",
        "approve_enabled": approve_enabled,
        "approve_reason": approve_reason,
        "cancel_enabled": cancel_enabled,
        "cancel_reason": cancel_reason,
        "cancel_action": cancel_action,
    }


@router.get("/chat/conversation/{conversation_id}")
async def get_conversation_detail(request: Request, conversation_id: str) -> dict[str, Any]:
    """Return full conversation with all messages for the detail modal."""
    from uuid import UUID as _UUID

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    try:
        conv_uuid = _UUID(str(conversation_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Konuşma kimliği geçersiz") from err

    conv_row = await pool.fetchrow(
        """
        SELECT id, phone_display, language, current_state, current_intent,
               risk_flags, is_active, human_override, hotel_id, created_at, last_message_at
        FROM conversations WHERE id = $1
        """,
        conv_uuid,
    )
    if conv_row is None:
        raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

    hold_row = await pool.fetchrow(
        """
        SELECT hold_id, status, draft_json, pms_reservation_id, voucher_no, reservation_no,
               manual_review_reason, approved_by, approved_at, rejected_reason, created_at
        FROM stay_holds
        WHERE conversation_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        conv_uuid,
    )

    msg_rows = await pool.fetch(
        """
        SELECT id, role, content, internal_json, created_at
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
        """,
        conv_uuid,
    )

    def _pj(raw: object) -> dict[str, Any]:
        return _parse_chat_payload(raw)

    messages = []
    last_user_message_at: datetime | None = None
    last_outbound_at: datetime | None = None
    latest_assistant_internal: dict[str, Any] = {}
    reservation_hint: dict[str, Any] = {}
    for m in msg_rows:
        ij = _pj(m["internal_json"])
        if m["role"] == "user":
            last_user_message_at = m["created_at"] or last_user_message_at
        if m["role"] == "assistant":
            last_outbound_at = m["created_at"] or last_outbound_at
            latest_assistant_internal = ij
        if m["role"] == "system":
            extracted_hint = _extract_reservation_hint_from_internal(ij)
            if extracted_hint:
                reservation_hint = extracted_hint
        raw_attachments = ij.get("attachments") if isinstance(ij, dict) else None
        attachments: list[dict[str, Any]] = []
        if isinstance(raw_attachments, list):
            for item in raw_attachments:
                if not isinstance(item, dict):
                    continue
                attachments.append(
                    {
                        "asset_id": str(item.get("asset_id") or ""),
                        "kind": str(item.get("kind") or ""),
                        "mime_type": str(item.get("mime_type") or ""),
                        "file_name": str(item.get("file_name") or ""),
                        "size_bytes": int(item.get("size_bytes") or 0),
                        "content_url": str(item.get("content_url") or ""),
                    }
                )
        messages.append({
            "id": str(m["id"]),
            "role": m["role"],
            "content": m["content"] or "",
            "created_at": m["created_at"].isoformat() if m["created_at"] else None,
            "internal_json": ij,
            "attachments": attachments,
            "send_blocked": ij.get("send_blocked", False),
            "approval_pending": ij.get("approval_pending", False),
            "rejected": ij.get("rejected", False),
            "internal_note": bool(ij.get("internal_note")),
            "whatsapp_message_id": str(ij.get("whatsapp_message_id") or "").strip() or None,
            "local_status": _derive_delivery_state(
                send_blocked=bool(ij.get("send_blocked")),
                approval_pending=bool(ij.get("approval_pending")),
                rejected=bool(ij.get("rejected")),
                whatsapp_message_id=str(ij.get("whatsapp_message_id") or "").strip() or None,
                provider_status=str(ij.get("provider_status") or "").strip() or None,
            ),
            "provider_status": str(ij.get("provider_status") or "").strip() or "unknown",
            "provider_status_updated_at": str(ij.get("provider_status_updated_at") or "").strip() or None,
            "provider_sent_at": str(ij.get("provider_sent_at") or "").strip() or None,
            "delivered_at": str(ij.get("delivered_at") or "").strip() or None,
            "read_at": str(ij.get("read_at") or "").strip() or None,
            "failed_at": str(ij.get("failed_at") or "").strip() or None,
            "provider_error": ij.get("provider_error") if isinstance(ij.get("provider_error"), dict) else None,
            "provider_events": ij.get("provider_events") if isinstance(ij.get("provider_events"), list) else [],
            "session_reopen_template_sent": bool(ij.get("session_reopen_template_sent")),
            "session_reopen_template_name": str(ij.get("session_reopen_template_name") or "").strip() or None,
            "session_reopen_template_sent_at": str(ij.get("session_reopen_template_sent_at") or "").strip() or None,
        })

    service_window = _build_service_window(last_user_message_at)
    delivery_state = _derive_delivery_state(
        send_blocked=bool(latest_assistant_internal.get("send_blocked")),
        approval_pending=bool(latest_assistant_internal.get("approval_pending")),
        rejected=bool(latest_assistant_internal.get("rejected")),
        whatsapp_message_id=str(latest_assistant_internal.get("whatsapp_message_id") or "").strip() or None,
        provider_status=str(latest_assistant_internal.get("provider_status") or "").strip() or None,
    )

    return {
        "id": str(conv_row["id"]),
        "phone_display": conv_row["phone_display"] or "***",
        "language": conv_row["language"] or "-",
        "state": conv_row["current_state"] or "-",
        "intent": conv_row["current_intent"] or "-",
        "risk_flags": list(conv_row["risk_flags"] or []),
        "is_active": conv_row["is_active"],
        "human_override": bool(conv_row["human_override"]),
        "hotel_id": conv_row["hotel_id"],
        "created_at": conv_row["created_at"].isoformat() if conv_row["created_at"] else None,
        "last_message_at": conv_row["last_message_at"].isoformat() if conv_row["last_message_at"] else None,
        "last_inbound_at": last_user_message_at.isoformat() if last_user_message_at else None,
        "last_outbound_at": last_outbound_at.isoformat() if last_outbound_at else None,
        "delivery_state": delivery_state,
        "last_webhook_at": str(latest_assistant_internal.get("provider_status_updated_at") or "").strip() or None,
        **service_window,
        "guest_info": _build_guest_info(conv_row, hold_row, reservation_hint),
        "messages": messages,
        "operation_mode": settings.operation_mode,
    }


@router.get("/chat/templates")
async def list_chat_templates(
    request: Request,
    conversation_id: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    state_name: str | None = Query(default=None, alias="state"),
    language: str | None = Query(default=None),
    hotel_id: int | None = Query(default=None),
) -> dict[str, Any]:
    """Return template candidates and previews for the current chat context."""
    resolved_intent = str(intent or "").strip()
    resolved_state = str(state_name or "").strip()
    resolved_language = str(language or "").strip() or "tr"
    resolved_hotel_id = hotel_id or settings.elektra_hotel_id

    pool = getattr(request.app.state, "db_pool", None)
    if conversation_id:
        if pool is None:
            raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")
        from uuid import UUID as _UUID

        try:
            conv_uuid = _UUID(str(conversation_id))
        except (ValueError, AttributeError) as err:
            raise HTTPException(status_code=400, detail="Konuşma kimliği geçersiz") from err

        async with pool.acquire() as conn:
            conv_row = await conn.fetchrow(
                """
                SELECT id, hotel_id, language, current_state, current_intent
                FROM conversations
                WHERE id = $1
                """,
                conv_uuid,
            )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")
        resolved_hotel_id = int(conv_row["hotel_id"] or resolved_hotel_id)
        resolved_language = str(conv_row["language"] or resolved_language or "tr")
        resolved_state = str(conv_row["current_state"] or resolved_state or "")
        resolved_intent = str(conv_row["current_intent"] or resolved_intent or "")

    templates = get_all_templates()
    if not templates:
        templates = load_templates()

    profile = get_profile(resolved_hotel_id)
    if profile is None:
        load_all_profiles()
        profile = get_profile(resolved_hotel_id)
    hotel_name = "-"
    if profile is not None:
        localized_name = getattr(profile.hotel_name, resolved_language, None)
        hotel_name = str(localized_name or profile.hotel_name.tr or profile.hotel_name.en or "-")

    preview_variables = {
        "hotel_name": hotel_name,
        "summary": "[summary]",
        "name": "[name]",
        "date": "[date]",
    }

    scored_templates: list[tuple[int, Any]] = []
    for template in templates:
        if resolved_language and template.language not in {resolved_language, "en"}:
            continue
        score = 0
        if template.language == resolved_language:
            score += 40
        elif template.language == "en":
            score += 10
        if resolved_intent and template.intent == resolved_intent:
            score += 30
        if resolved_state and template.state == resolved_state:
            score += 20
        if not resolved_intent and template.intent:
            score += 5
        if score <= 0:
            continue
        scored_templates.append((score, template))

    scored_templates.sort(key=lambda item: (-item[0], item[1].id))
    candidates = []
    for score, template in scored_templates[:12]:
        fields = _extract_template_fields(template.template)
        preview = _build_template_preview(template.template, preview_variables)
        candidates.append(
            {
                "id": template.id,
                "intent": template.intent,
                "state": template.state,
                "language": template.language,
                "score": score,
                "recommended": bool(
                    template.language == resolved_language
                    and (not resolved_intent or template.intent == resolved_intent)
                    and (not resolved_state or template.state == resolved_state)
                ),
                "fields": fields,
                "preview": preview,
                "body": template.template,
            }
        )

    return {
        "context": {
            "conversation_id": conversation_id,
            "intent": resolved_intent or None,
            "state": resolved_state or None,
            "language": resolved_language,
            "hotel_id": resolved_hotel_id,
            "hotel_name": hotel_name,
        },
        "templates": candidates,
    }


@router.post("/chat/reject-message")
async def reject_and_flag_message(request: Request) -> dict[str, Any]:
    """Reject an assistant message: mark as rejected and ensure send_blocked."""
    from uuid import UUID as _UUID

    body = await request.json()
    conv_id = body.get("conversation_id")
    msg_id = body.get("message_id")
    if not conv_id or not msg_id:
        raise HTTPException(status_code=400, detail="conversation_id ve message_id alanları zorunludur")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    try:
        msg_uuid = _UUID(str(msg_id))
        conv_uuid = _UUID(str(conv_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Kimlik biçimi geçersiz") from err

    def _pj(raw: object) -> dict[str, Any]:
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (str, bytes, bytearray)):
            try:
                result = orjson.loads(raw)
                return result if isinstance(result, dict) else {}
            except Exception:
                return {}
        return {}

    async with pool.acquire() as conn:
        msg_row = await conn.fetchrow(
            "SELECT id, role, internal_json FROM messages WHERE id = $1 AND conversation_id = $2",
            msg_uuid,
            conv_uuid,
        )
        if msg_row is None:
            raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
        if msg_row["role"] != "assistant":
            raise HTTPException(status_code=400, detail="Yalnızca asistan mesajları reddedilebilir")

        internal = _pj(msg_row["internal_json"])
        internal["rejected"] = True
        internal["rejected_at"] = datetime.now(UTC).isoformat()
        internal["rejected_by"] = "admin"
        internal["send_blocked"] = True

        await conn.execute(
            "UPDATE messages SET internal_json = $1 WHERE id = $2",
            orjson.dumps(internal).decode(),
            msg_uuid,
        )

    return {"status": "rejected", "message_id": str(msg_id), "conversation_id": str(conv_id)}


@router.post("/chat/regenerate")
async def regenerate_assistant_message(request: Request) -> dict[str, Any]:
    """Delete the last assistant message(s) and re-run the LLM pipeline."""
    from uuid import UUID as _UUID

    from velox.adapters.whatsapp.formatter import WhatsAppFormatter as _Fmt
    from velox.models.conversation import Message

    body = await request.json()
    conv_id = body.get("conversation_id")
    if not conv_id:
        raise HTTPException(status_code=400, detail="conversation_id alanı zorunludur")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    try:
        conv_uuid = _UUID(str(conv_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Kimlik biçimi geçersiz") from err

    repo = ConversationRepository()

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1", conv_uuid,
        )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        # Find last user message (context for regeneration)
        last_user = await conn.fetchrow(
            "SELECT content FROM messages "
            "WHERE conversation_id = $1 AND role = 'user' "
            "ORDER BY created_at DESC LIMIT 1",
            conv_uuid,
        )
        if last_user is None:
            raise HTTPException(status_code=400, detail="Yeniden oluşturma için kullanıcı mesajı bulunamadı")

        # Delete last assistant message(s) that came after the last user message
        await conn.execute(
            """
            DELETE FROM messages
            WHERE conversation_id = $1
              AND role = 'assistant'
              AND created_at >= (
                SELECT created_at FROM messages
                WHERE conversation_id = $1 AND role = 'user'
                ORDER BY created_at DESC LIMIT 1
              )
            """,
            conv_uuid,
        )

    # Load conversation object for pipeline
    conversation = await repo.get_by_id(conv_uuid)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Temizlik sonrası konuşma bulunamadı")

    conversation.messages = await repo.get_recent_messages(conv_uuid, count=20)
    normalized_text = _normalize_text(last_user["content"] or "")
    detected_language = _detect_message_language(normalized_text, conversation.language)

    try:
        llm_response = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=normalized_text,
            expected_language=detected_language,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM pipeline hatasi: {exc}") from exc

    # Save new assistant message
    formatter = _Fmt()
    message_parts = _extract_user_message_parts(llm_response)
    if not message_parts:
        message_parts = [llm_response.user_message]

    for index, raw_message in enumerate(message_parts, start=1):
        reply_text = formatter.truncate(raw_message)
        assistant_internal = llm_response.internal_json.model_dump(mode="json")
        assistant_internal["message_part_index"] = index
        assistant_internal["message_part_total"] = len(message_parts)
        assistant_internal["send_blocked"] = True
        assistant_internal["regenerated"] = True
        assistant_internal["regenerated_at"] = datetime.now(UTC).isoformat()

        assistant_msg = Message(
            conversation_id=conv_uuid,
            role="assistant",
            content=reply_text,
            internal_json=assistant_internal,
            tool_calls=assistant_internal.get("tool_calls") or None,
        )
        await repo.add_message(assistant_msg)

    # Update conversation state
    next_state = str(llm_response.internal_json.state or conversation.current_state or "GREETING")
    next_intent = str(llm_response.internal_json.intent or "").strip() or None
    await repo.update_state(
        conversation_id=conv_uuid,
        state=next_state,
        intent=next_intent,
        entities=llm_response.internal_json.entities if isinstance(llm_response.internal_json.entities, dict) else None,
        risk_flags=llm_response.internal_json.risk_flags or None,
    )

    return {"status": "regenerated", "conversation_id": str(conv_id)}


@router.post("/chat/send-to-conversation")
async def send_message_to_conversation(request: Request) -> dict[str, Any]:
    """Admin sends a manual message to a WhatsApp conversation."""
    from uuid import UUID as _UUID

    from velox.adapters.whatsapp.client import get_whatsapp_client

    body = await request.json()
    conv_id = body.get("conversation_id")
    message = body.get("message", "").strip()
    raw_attachments = body.get("attachments") or []
    attachment_ids: list[str] = []
    if isinstance(raw_attachments, list):
        for item in raw_attachments:
            candidate = str(item.get("asset_id") or "").strip() if isinstance(item, dict) else str(item or "").strip()
            if candidate:
                attachment_ids.append(candidate)
    if not conv_id or (not message and not attachment_ids):
        raise HTTPException(status_code=400, detail="conversation_id ile birlikte message veya attachments alanı zorunludur")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    try:
        conv_uuid = _UUID(str(conv_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Kimlik biçimi geçersiz") from err

    repo = ConversationRepository()
    try:
        resolved_assets = await attachment_service.resolve_assets_for_message(
            hotel_id=settings.elektra_hotel_id,
            attachment_ids=attachment_ids,
        )
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow(
            "SELECT id, phone_display FROM conversations WHERE id = $1", conv_uuid,
        )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        # Resolve real phone
        phone = str(conv_row["phone_display"] or "")
        if not phone or "*" in phone:
            user_row = await conn.fetchrow(
                "SELECT internal_json FROM messages "
                "WHERE conversation_id = $1 AND role = 'user' "
                "ORDER BY created_at DESC LIMIT 1",
                conv_uuid,
            )
            if user_row:
                import orjson
                raw = user_row["internal_json"]
                ij = {}
                if isinstance(raw, dict):
                    ij = raw
                elif isinstance(raw, (str, bytes)):
                    with contextlib.suppress(Exception):
                        ij = orjson.loads(raw)
                phone = ij.get("wa_id", "")
        if not phone or "*" in phone:
            raise HTTPException(status_code=400, detail="Gerçek telefon numarası bulunamadı")

    # Send via WhatsApp
    whatsapp_client = get_whatsapp_client()
    outbound_events: list[dict[str, Any]] = []
    reopen_state: dict[str, Any] = {"sent": False, "template_name": None, "sent_at": None}
    try:
        if message:
            text_result = await _send_with_session_reopen_fallback(
                whatsapp_client=whatsapp_client,
                phone=phone,
                send_operation=lambda: whatsapp_client.send_text_message(to=phone, body=message, force=True),
                reopen_state=reopen_state,
            )
            outbound_events.append(
                {
                    "kind": "text",
                    "content": message,
                    "whatsapp_message_id": _extract_whatsapp_message_id(text_result),
                    "attachments": [],
                }
            )

        for asset in resolved_assets:
            storage_path = Path(asset.storage_path)
            if not storage_path.exists():
                raise HTTPException(status_code=400, detail=f"Dosya bulunamadı: {asset.file_name}")

            if asset.kind == "image":
                media_result = await _send_with_session_reopen_fallback(
                    whatsapp_client=whatsapp_client,
                    phone=phone,
                    send_operation=lambda: whatsapp_client.send_image_message(
                        to=phone,
                        file_path=storage_path,
                        mime_type=asset.mime_type,
                        force=True,
                    ),
                    reopen_state=reopen_state,
                )
                title = f"[Gorsel] {asset.file_name}"
            elif asset.kind == "document":
                media_result = await _send_with_session_reopen_fallback(
                    whatsapp_client=whatsapp_client,
                    phone=phone,
                    send_operation=lambda: whatsapp_client.send_document_message(
                        to=phone,
                        file_path=storage_path,
                        mime_type=asset.mime_type,
                        file_name=asset.file_name,
                        force=True,
                    ),
                    reopen_state=reopen_state,
                )
                title = f"[Belge] {asset.file_name}"
            elif asset.kind == "audio":
                media_result = await _send_with_session_reopen_fallback(
                    whatsapp_client=whatsapp_client,
                    phone=phone,
                    send_operation=lambda: whatsapp_client.send_audio_message(
                        to=phone,
                        file_path=storage_path,
                        mime_type=asset.mime_type,
                        force=True,
                    ),
                    reopen_state=reopen_state,
                )
                title = f"[Ses] {asset.file_name}"
            else:
                raise HTTPException(status_code=400, detail="Bilinmeyen dosya türü.")

            outbound_events.append(
                {
                    "kind": asset.kind,
                    "content": title,
                    "whatsapp_message_id": _extract_whatsapp_message_id(media_result),
                    "attachments": [serialize_asset_for_client(asset)],
                    "asset_id": asset.id,
                }
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"WhatsApp mesajı gönderilemedi: {exc}") from exc

    # Save outbound events as assistant messages in DB
    from velox.models.conversation import Message
    sent_ids: list[str] = []
    for event in outbound_events:
        assistant_msg = Message(
            conversation_id=conv_uuid,
            role="assistant",
            content=str(event["content"]),
            internal_json={
                "send_blocked": False,
                "manual_send": True,
                "sent_at": datetime.now(UTC).isoformat(),
                "sent_by": "admin",
                "whatsapp_message_id": event.get("whatsapp_message_id"),
                "attachments": event.get("attachments") or [],
                "session_reopen_template_sent": bool(reopen_state.get("sent")),
                "session_reopen_template_name": reopen_state.get("template_name"),
                "session_reopen_template_sent_at": reopen_state.get("sent_at"),
            },
        )
        await repo.add_message(assistant_msg)
        if assistant_msg.id is not None:
            sent_ids.append(str(assistant_msg.id))
            asset_id = str(event.get("asset_id") or "").strip()
            if asset_id:
                await attachment_service.attach_assets_to_message(
                    asset_ids=[asset_id],
                    message_id=assistant_msg.id,
                )

    return {
        "status": "sent",
        "conversation_id": str(conv_id),
        "message_ids": sent_ids,
        "session_reopen_template_sent": bool(reopen_state.get("sent")),
        "session_reopen_template_name": reopen_state.get("template_name"),
    }


@router.post("/chat/note-to-conversation")
async def add_note_to_conversation(body: ConversationNoteRequest, request: Request) -> dict[str, Any]:
    """Persist one internal admin note for a live conversation."""
    from uuid import UUID as _UUID

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    try:
        conv_uuid = _UUID(str(body.conversation_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Konuşma kimliği geçersiz") from err

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow("SELECT id FROM conversations WHERE id = $1", conv_uuid)
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

    repository = ConversationRepository()
    note_message = await repository.add_message(
        Message(
            conversation_id=conv_uuid,
            role="system",
            content=str(body.note).strip(),
            internal_json={
                "internal_note": True,
                "source": "chat_lab_admin_note",
                "created_by": "admin",
                "created_at": datetime.now(UTC).isoformat(),
            },
        )
    )
    return {
        "status": "saved",
        "conversation_id": body.conversation_id,
        "message_id": str(note_message.id) if note_message.id is not None else None,
    }


@router.post("/chat/approve-message")
async def approve_and_send_message(request: Request) -> dict[str, Any]:
    """Approve a pending assistant message and send it via WhatsApp."""
    from uuid import UUID as _UUID

    from velox.adapters.whatsapp.client import get_whatsapp_client

    body = await request.json()
    conv_id = body.get("conversation_id")
    msg_id = body.get("message_id")
    if not conv_id or not msg_id:
        raise HTTPException(status_code=400, detail="conversation_id ve message_id alanları zorunludur")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı kullanılamıyor")

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow(
            "SELECT id, phone_display FROM conversations WHERE id = $1",
            _UUID(str(conv_id)),
        )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        msg_row = await conn.fetchrow(
            "SELECT id, role, content, internal_json FROM messages WHERE id = $1 AND conversation_id = $2",
            _UUID(str(msg_id)),
            conv_row["id"],
        )
        if msg_row is None:
            raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
        if msg_row["role"] != "assistant":
            raise HTTPException(status_code=400, detail="Yalnızca asistan mesajları gönderilebilir")

        # Try to find real phone from user message audit context (wa_id field)
        user_phone_row = await conn.fetchrow(
            """
            SELECT internal_json FROM messages
            WHERE conversation_id = $1 AND role = 'user'
            ORDER BY created_at DESC LIMIT 1
            """,
            conv_row["id"],
        )

    def _parse_json(raw: Any) -> dict[str, Any]:
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (str, bytes, bytearray)):
            try:
                result = orjson.loads(raw)
                return result if isinstance(result, dict) else {}
            except Exception:
                return {}
        return {}

    internal = _parse_json(msg_row["internal_json"])
    if not internal.get("send_blocked") and not internal.get("approval_pending"):
        return {"status": "already_sent", "message_id": msg_id}

    # Resolve phone: prefer phone_display, fallback to wa_id from user message
    phone = str(conv_row["phone_display"] or "")
    if not phone or "***" in phone or "*" in phone:
        user_internal = _parse_json(user_phone_row["internal_json"] if user_phone_row else None)
        wa_id = user_internal.get("wa_id") or ""
        if wa_id:
            phone = wa_id
    if not phone or "*" in phone:
        raise HTTPException(
            status_code=400,
            detail="Bu konuşma için gerçek telefon numarası bulunamadı. Maskeli numaraya mesaj gönderilemez.",
        )

    whatsapp_client = get_whatsapp_client()
    reopen_state: dict[str, Any] = {"sent": False, "template_name": None, "sent_at": None}
    try:
        send_result = await _send_with_session_reopen_fallback(
            whatsapp_client=whatsapp_client,
            phone=phone,
            send_operation=lambda: whatsapp_client.send_text_message(to=phone, body=str(msg_row["content"]), force=True),
            reopen_state=reopen_state,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"WhatsApp mesajı gönderilemedi: {exc}") from exc

    wa_message_id = _extract_whatsapp_message_id(send_result)
    internal["send_blocked"] = False
    internal["approval_pending"] = False
    internal["approved_at"] = datetime.now(UTC).isoformat()
    internal["session_reopen_template_sent"] = bool(reopen_state.get("sent"))
    internal["session_reopen_template_name"] = reopen_state.get("template_name")
    internal["session_reopen_template_sent_at"] = reopen_state.get("sent_at")
    if wa_message_id:
        internal["whatsapp_message_id"] = wa_message_id
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET internal_json = $1, whatsapp_message_id = COALESCE($3, whatsapp_message_id) WHERE id = $2",
            orjson.dumps(internal).decode(),
            _UUID(str(msg_id)),
            wa_message_id,
        )

    return {
        "status": "sent",
        "message_id": msg_id,
        "conversation_id": str(conv_id),
        "session_reopen_template_sent": bool(reopen_state.get("sent")),
        "session_reopen_template_name": reopen_state.get("template_name"),
    }


@router.get("/chat/metrics")
async def get_chat_metrics() -> dict[str, Any]:
    """Return aggregated feedback metrics for the Chat Lab dashboard."""
    try:
        return compute_feedback_metrics()
    except Exception as error:
        logger.exception("chat_lab_metrics_error")
        raise HTTPException(status_code=500, detail=f"Metrik hesaplama hatasi: {error}") from error


@router.get("/models")
async def list_models() -> dict[str, Any]:
    """List available GPT models and the currently active one."""
    client = get_llm_client()
    try:
        models_page = await client.client.models.list()
        gpt_models = sorted(
            [model.id for model in models_page.data if "gpt" in model.id],
            reverse=True,
        )
    except Exception:
        logger.exception("test_chat_model_list_failed")
        gpt_models = []
    return {"models": gpt_models, "current": client.primary_model}


@router.post("/model")
async def set_model(body: SetModelRequest) -> dict[str, str]:
    """Change the active LLM model at runtime in development mode."""
    client = get_llm_client()
    client.primary_model = body.model
    return {"status": "ok", "model": body.model}


@ui_router.get("/admin/chat-lab", response_class=HTMLResponse)
async def test_chat_ui() -> HTMLResponse:
    """Serve the Chat Lab web interface."""
    return HTMLResponse(content=TEST_CHAT_HTML)


@ui_router.get("/test-chat", response_class=HTMLResponse, include_in_schema=False)
async def test_chat_ui_legacy() -> HTMLResponse:
    """Serve the legacy Chat Lab URL for backwards compatibility."""
    return HTMLResponse(content=TEST_CHAT_HTML)
