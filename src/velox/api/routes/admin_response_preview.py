"""Admin response-preview routes with no conversation history persistence."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import TokenData, check_permission, get_current_user, resolve_hotel_scope
from velox.core.response_preview import (
    MAX_PREVIEW_QUESTION_CHARS,
    PREVIEW_RESPONSE_STYLES,
    PREVIEW_PERMISSION,
    ResponsePreviewResult,
    generate_response_preview,
)
from velox.llm.client import LLMUnavailableError

router = APIRouter(prefix="/admin/response-preview", tags=["admin-response-preview"])
logger = structlog.get_logger(__name__)


class ResponsePreviewGenerateRequest(BaseModel):
    """Single-question response preview request."""

    hotel_id: int | None = Field(default=None, ge=1)
    question: str = Field(min_length=1, max_length=MAX_PREVIEW_QUESTION_CHARS)
    language: str = Field(default="auto", max_length=8)
    response_style: str = Field(default="professional", max_length=16)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Reject whitespace-only questions before any LLM call."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Question is required")
        return cleaned

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        """Normalize unsupported language selections to automatic detection."""
        normalized = str(value or "auto").strip().lower()
        if normalized in {"auto", "tr", "en", "ru", "de", "ar", "es", "fr", "zh", "hi", "pt"}:
            return normalized
        return "auto"

    @field_validator("response_style")
    @classmethod
    def validate_response_style(cls, value: str) -> str:
        """Normalize unsupported response style selections to the default style."""
        normalized = str(value or "professional").strip().lower()
        if normalized in PREVIEW_RESPONSE_STYLES:
            return normalized
        return "professional"


@router.post("/generate", response_model=ResponsePreviewResult)
async def generate_admin_response_preview(
    payload: ResponsePreviewGenerateRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
) -> ResponsePreviewResult:
    """Generate one isolated AI reply without creating conversation/message history."""
    check_permission(current_user, PREVIEW_PERMISSION)
    hotel_id = resolve_hotel_scope(current_user, payload.hotel_id)
    dispatcher = getattr(request.app.state, "tool_dispatcher", None)
    try:
        return await generate_response_preview(
            hotel_id=hotel_id,
            question=payload.question,
            language=payload.language,
            response_style=payload.response_style,
            dispatcher=dispatcher,
        )
    except LLMUnavailableError as exc:
        logger.warning("admin_response_preview_llm_unavailable", hotel_id=hotel_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yanıt üretimi şu anda kullanılamıyor. Lütfen kısa süre sonra tekrar deneyin.",
        ) from exc
