"""Chat Lab endpoints and UI for admin-operated testing workflows."""

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

import asyncpg
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

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
    _detect_message_language,
    _extract_user_message_parts,
    _hash_phone,
    _mask_phone,
    _merge_entities_with_context,
    _normalize_text,
    _run_message_pipeline,
)
from velox.config.constants import Role
from velox.config.settings import settings
from velox.core.chat_lab_feedback import (
    ChatLabFeedbackError,
    ChatLabFeedbackService,
    ChatLabImportError,
    FeedbackConversationNotFoundError,
    FeedbackMessageNotFoundError,
)
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

logger = structlog.get_logger(__name__)


def _chat_lab_dependencies() -> list[Any]:
    """Protect Chat Lab APIs with admin auth in production."""
    if settings.app_env == "production":
        return [Depends(require_role(Role.ADMIN))]
    return []


router = APIRouter(prefix="/test", tags=["test-chat"], dependencies=_chat_lab_dependencies())
ui_router = APIRouter(tags=["test-chat-ui"])
formatter = WhatsAppFormatter()

TEST_PHONE_PREFIX = "test_"
_chat_locks: dict[str, asyncio.Lock] = {}
_chat_locks_guard = asyncio.Lock()
IDEMPOTENT_ASSISTANT_WAIT_ATTEMPTS = 20
IDEMPOTENT_ASSISTANT_WAIT_SECONDS = 0.1


class TestChatRequest(BaseModel):
    """Inbound payload for Chat Lab message simulation."""

    message: str = Field(min_length=1, max_length=4096)
    phone: str = Field(default="test_user_123")
    client_message_id: str | None = Field(default=None, min_length=1, max_length=128)


class TestChatResponse(BaseModel):
    """Chat Lab reply payload with debug metadata."""

    reply: str
    assistant_message_id: str
    internal_json: dict[str, Any]
    conversation: dict[str, Any]
    timestamp: str


class SetModelRequest(BaseModel):
    """Request payload for switching the active test model."""

    model: str = Field(min_length=1)


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
    return {
        "id": str(message.id),
        "role": message.role,
        "content": message.content,
        "internal_json": message.internal_json,
        "created_at": message.created_at.isoformat(),
    }


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
                assistant_message_id=str(existing_assistant.id),
                internal_json=internal_json,
                conversation=_serialize_conversation(safe_conversation),
                timestamp=datetime.now(UTC).isoformat(),
            )

        normalized = _normalize_text(body.message)
        detected_language = _detect_message_language(normalized, conversation.language)
        if conversation.language != detected_language:
            conversation.language = detected_language
            await repository.update_language(conversation.id, detected_language)

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=normalized,
            client_message_id=normalized_client_message_id,
            internal_json={
                "source_type": "live_test_chat",
                "client_message_id": normalized_client_message_id,
                "route_audit": {
                    "route": "/api/v1/test/chat",
                    "received_at": datetime.now(UTC).isoformat(),
                },
            },
        )
        try:
            await repository.add_message(user_message)
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
                assistant_message_id=str(existing_assistant.id),
                internal_json=internal_json,
                conversation=_serialize_conversation(safe_conversation),
                timestamp=datetime.now(UTC).isoformat(),
            )
        conversation.messages = await repository.get_recent_messages(conversation.id, count=20)

        llm_response = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=normalized,
            dispatcher=getattr(request.app.state, "tool_dispatcher", None),
            expected_language=detected_language,
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

        outbound_messages = _extract_user_message_parts(llm_response)
        if not outbound_messages:
            outbound_messages = [llm_response.user_message]
        reply_text = formatter.truncate(outbound_messages[0])
        assistant_internal = llm_response.internal_json.model_dump(mode="json")
        assistant_internal["client_message_id"] = normalized_client_message_id
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

        if assistant_message is None:
            raise HTTPException(status_code=500, detail="Assistant message was not created")

        return TestChatResponse(
            reply=reply_text,
            assistant_message_id=str(assistant_message.id),
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
    return {
        "messages": [_serialize_message(message) for message in messages],
        "conversation": _serialize_conversation(conversation),
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
    return {"status": "reset", "closed_conversation_id": str(conversation.id)}


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
    if body.source_type == "live_test_chat" and getattr(request.app.state, "db_pool", None) is None:
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
