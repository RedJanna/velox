"""Chat Lab endpoints and UI for admin-operated testing workflows."""

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

import asyncpg
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
from velox.config.constants import Role
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
            raise ValueError("Tek mesajda en fazla 5 dosya gonderilebilir.")
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
        ),
        "provider_status": "unknown",
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
        return "Dosya gonderildi."
    return "Ek gonderildi: " + ", ".join(labels[:3])


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


def _derive_delivery_state(
    *,
    send_blocked: bool,
    approval_pending: bool,
    rejected: bool,
    whatsapp_message_id: str | None,
) -> str:
    """Map known assistant metadata into one conservative UI delivery state."""
    if rejected:
        return "failed"
    if approval_pending or send_blocked:
        return "pending_approval"
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
        raise HTTPException(status_code=503, detail="Database not available")

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
            raise HTTPException(status_code=500, detail="Conversation id is missing")

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
                    detail="Duplicate request is already being processed",
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
            raise HTTPException(status_code=500, detail="Assistant message was not created")

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
        raise HTTPException(status_code=503, detail="Database not available")

    repository = ConversationRepository()
    conversation = await repository.get_active_by_phone(
        settings.elektra_hotel_id,
        _hash_phone(_ensure_test_phone(phone)),
    )
    if conversation is None:
        return {"messages": [], "conversation": None}
    if conversation.id is None:
        raise HTTPException(status_code=500, detail="Conversation id is missing")

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
        raise HTTPException(status_code=503, detail="Database not available")

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
        raise HTTPException(status_code=503, detail="Database not available")

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
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        await attachment_service.delete_asset(asset_id=asset_id, hotel_id=settings.elektra_hotel_id)
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"status": "deleted", "asset_id": asset_id}


@router.get("/chat/upload-asset/{asset_id}/content")
async def get_chat_asset_content(request: Request, asset_id: str) -> FileResponse:
    """Serve one uploaded attachment to authenticated Chat Lab users."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        asset = await attachment_service.get_asset_for_hotel(
            asset_id=asset_id,
            hotel_id=settings.elektra_hotel_id,
        )
    except ChatLabAttachmentError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    storage_path = Path(asset.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Dosya depoda bulunamadi.")

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
        raise HTTPException(status_code=503, detail="Database not available")

    repository = ConversationRepository()
    conversation = await repository.get_active_by_phone(
        settings.elektra_hotel_id,
        _hash_phone(_ensure_test_phone(phone)),
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="No active conversation for this phone")
    if conversation.id is None:
        raise HTTPException(status_code=500, detail="Conversation id is missing")

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
        raise HTTPException(status_code=503, detail="Veritabani kullanilamiyor")

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
async def live_feed(request: Request, limit: int = 20) -> dict[str, Any]:
    """Return recent real (non-test) conversations with their last messages."""
    if getattr(request.app.state, "db_pool", None) is None:
        raise HTTPException(status_code=503, detail="Database not available")

    pool = request.app.state.db_pool
    capped_limit = min(max(limit, 1), 50)

    try:
        rows = await pool.fetch(
            """
            SELECT c.id, c.phone_display, c.language, c.current_state,
                   c.current_intent, c.risk_flags, c.is_active,
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
                   (SELECT m.id FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS last_assistant_msg_id,
                   (SELECT m.internal_json->>'rejected' FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'assistant'
                    ORDER BY m.created_at DESC LIMIT 1) AS rejected
            FROM conversations c
            WHERE c.phone_hash NOT LIKE 'test_%'
              AND c.is_active = true
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
        )
        conversations.append({
            "id": str(row["id"]),
            "phone_display": row["phone_display"] or "***",
            "language": row["language"] or "-",
            "state": row["current_state"] or "-",
            "intent": row["current_intent"] or "-",
            "risk_flags": list(row["risk_flags"] or []),
            "is_active": row["is_active"],
            "msg_count": row["msg_count"],
            "last_user_msg": (row["last_user_msg"] or "")[:500],
            "last_assistant_msg": (row["last_assistant_msg"] or "")[:500],
            "send_blocked": row["send_blocked"],
            "approval_pending": row["approval_pending"],
            "whatsapp_message_id": row["whatsapp_message_id"],
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


@router.get("/chat/conversation/{conversation_id}")
async def get_conversation_detail(request: Request, conversation_id: str) -> dict[str, Any]:
    """Return full conversation with all messages for the detail modal."""
    from uuid import UUID as _UUID

    import orjson

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        conv_uuid = _UUID(str(conversation_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Invalid conversation_id") from err

    conv_row = await pool.fetchrow(
        """
        SELECT id, phone_display, language, current_state, current_intent,
               risk_flags, is_active, hotel_id, created_at, last_message_at
        FROM conversations WHERE id = $1
        """,
        conv_uuid,
    )
    if conv_row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

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

    messages = []
    last_user_message_at: datetime | None = None
    last_outbound_at: datetime | None = None
    latest_assistant_internal: dict[str, Any] = {}
    for m in msg_rows:
        ij = _pj(m["internal_json"])
        if m["role"] == "user":
            last_user_message_at = m["created_at"] or last_user_message_at
        if m["role"] == "assistant":
            last_outbound_at = m["created_at"] or last_outbound_at
            latest_assistant_internal = ij
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
            ),
            "provider_status": "unknown",
        })

    service_window = _build_service_window(last_user_message_at)
    delivery_state = _derive_delivery_state(
        send_blocked=bool(latest_assistant_internal.get("send_blocked")),
        approval_pending=bool(latest_assistant_internal.get("approval_pending")),
        rejected=bool(latest_assistant_internal.get("rejected")),
        whatsapp_message_id=str(latest_assistant_internal.get("whatsapp_message_id") or "").strip() or None,
    )

    return {
        "id": str(conv_row["id"]),
        "phone_display": conv_row["phone_display"] or "***",
        "language": conv_row["language"] or "-",
        "state": conv_row["current_state"] or "-",
        "intent": conv_row["current_intent"] or "-",
        "risk_flags": list(conv_row["risk_flags"] or []),
        "is_active": conv_row["is_active"],
        "hotel_id": conv_row["hotel_id"],
        "created_at": conv_row["created_at"].isoformat() if conv_row["created_at"] else None,
        "last_message_at": conv_row["last_message_at"].isoformat() if conv_row["last_message_at"] else None,
        "last_inbound_at": last_user_message_at.isoformat() if last_user_message_at else None,
        "last_outbound_at": last_outbound_at.isoformat() if last_outbound_at else None,
        "delivery_state": delivery_state,
        **service_window,
        "messages": messages,
        "operation_mode": settings.operation_mode,
    }


@router.post("/chat/reject-message")
async def reject_and_flag_message(request: Request) -> dict[str, Any]:
    """Reject an assistant message: mark as rejected and ensure send_blocked."""
    from uuid import UUID as _UUID

    import orjson

    body = await request.json()
    conv_id = body.get("conversation_id")
    msg_id = body.get("message_id")
    if not conv_id or not msg_id:
        raise HTTPException(status_code=400, detail="conversation_id and message_id required")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        msg_uuid = _UUID(str(msg_id))
        conv_uuid = _UUID(str(conv_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Invalid id format") from err

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
            raise HTTPException(status_code=404, detail="Message not found")
        if msg_row["role"] != "assistant":
            raise HTTPException(status_code=400, detail="Only assistant messages can be rejected")

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
        raise HTTPException(status_code=400, detail="conversation_id required")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        conv_uuid = _UUID(str(conv_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Invalid id format") from err

    repo = ConversationRepository()

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1", conv_uuid,
        )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Find last user message (context for regeneration)
        last_user = await conn.fetchrow(
            "SELECT content FROM messages "
            "WHERE conversation_id = $1 AND role = 'user' "
            "ORDER BY created_at DESC LIMIT 1",
            conv_uuid,
        )
        if last_user is None:
            raise HTTPException(status_code=400, detail="No user message to regenerate from")

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
        raise HTTPException(status_code=404, detail="Conversation not found after cleanup")

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
        raise HTTPException(status_code=400, detail="conversation_id and message or attachments required")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        conv_uuid = _UUID(str(conv_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Invalid id format") from err

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
            raise HTTPException(status_code=404, detail="Conversation not found")

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
            raise HTTPException(status_code=400, detail="Gercek telefon numarasi bulunamadi")

    # Send via WhatsApp
    whatsapp_client = get_whatsapp_client()
    outbound_events: list[dict[str, Any]] = []
    try:
        if message:
            text_result = await whatsapp_client.send_text_message(to=phone, body=message, force=True)
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
                raise HTTPException(status_code=400, detail=f"Dosya bulunamadi: {asset.file_name}")

            if asset.kind == "image":
                media_result = await whatsapp_client.send_image_message(
                    to=phone,
                    file_path=storage_path,
                    mime_type=asset.mime_type,
                    force=True,
                )
                title = f"[Gorsel] {asset.file_name}"
            elif asset.kind == "document":
                media_result = await whatsapp_client.send_document_message(
                    to=phone,
                    file_path=storage_path,
                    mime_type=asset.mime_type,
                    file_name=asset.file_name,
                    force=True,
                )
                title = f"[Belge] {asset.file_name}"
            elif asset.kind == "audio":
                media_result = await whatsapp_client.send_audio_message(
                    to=phone,
                    file_path=storage_path,
                    mime_type=asset.mime_type,
                    force=True,
                )
                title = f"[Ses] {asset.file_name}"
            else:
                raise HTTPException(status_code=400, detail="Bilinmeyen dosya tipi.")

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
        raise HTTPException(status_code=502, detail=f"WhatsApp gonderilemedi: {exc}") from exc

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
    }


@router.post("/chat/note-to-conversation")
async def add_note_to_conversation(body: ConversationNoteRequest, request: Request) -> dict[str, Any]:
    """Persist one internal admin note for a live conversation."""
    from uuid import UUID as _UUID

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        conv_uuid = _UUID(str(body.conversation_id))
    except (ValueError, AttributeError) as err:
        raise HTTPException(status_code=400, detail="Invalid conversation_id") from err

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow("SELECT id FROM conversations WHERE id = $1", conv_uuid)
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

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

    import orjson

    from velox.adapters.whatsapp.client import get_whatsapp_client

    body = await request.json()
    conv_id = body.get("conversation_id")
    msg_id = body.get("message_id")
    if not conv_id or not msg_id:
        raise HTTPException(status_code=400, detail="conversation_id and message_id required")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    async with pool.acquire() as conn:
        conv_row = await conn.fetchrow(
            "SELECT id, phone_display FROM conversations WHERE id = $1",
            _UUID(str(conv_id)),
        )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        msg_row = await conn.fetchrow(
            "SELECT id, role, content, internal_json FROM messages WHERE id = $1 AND conversation_id = $2",
            _UUID(str(msg_id)),
            conv_row["id"],
        )
        if msg_row is None:
            raise HTTPException(status_code=404, detail="Message not found")
        if msg_row["role"] != "assistant":
            raise HTTPException(status_code=400, detail="Only assistant messages can be sent")

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
            detail="Bu konusma icin gercek telefon numarasi bulunamadi. Maskeli numaraya mesaj gonderilemez.",
        )

    whatsapp_client = get_whatsapp_client()
    try:
        await whatsapp_client.send_text_message(to=phone, body=str(msg_row["content"]), force=True)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"WhatsApp gonderilemedi: {exc}") from exc

    internal["send_blocked"] = False
    internal["approval_pending"] = False
    internal["approved_at"] = datetime.now(UTC).isoformat()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET internal_json = $1 WHERE id = $2",
            orjson.dumps(internal).decode(),
            _UUID(str(msg_id)),
        )

    return {"status": "sent", "message_id": msg_id, "conversation_id": str(conv_id)}


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
