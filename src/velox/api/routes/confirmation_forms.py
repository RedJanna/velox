"""Reservation confirmation form preview, generation, and public HTML routes."""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Annotated, Any

import asyncpg
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from velox.adapters.whatsapp.client import WhatsAppSendBlockedError, get_whatsapp_client
from velox.api.middleware.auth import (
    TokenData,
    check_permission,
    ensure_hotel_access,
    get_current_user,
)
from velox.config.constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from velox.config.settings import settings
from velox.core.confirmation_forms import (
    APPROVAL_TYPE_FROM_FORM,
    ConfirmationFormType,
    build_context_from_hold,
    build_context_from_manual_payload,
    build_preview,
    create_confirmation_form,
    hash_public_token,
    load_hold_for_form,
    mark_confirmation_sent,
    normalize_language,
    token_is_valid,
)
from velox.db.database import fetchrow
from velox.utils.json import decode_json_object

logger = structlog.get_logger(__name__)

admin_router = APIRouter(prefix="/admin/confirmation-forms", tags=["admin-confirmation-forms"])
public_router = APIRouter(tags=["confirmation-forms"])

CUSTOMER_SEND_TIMEOUT_SECONDS = 10.0
PUBLIC_CONFIRMATION_HEADERS = {
    "Cache-Control": "private, no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Robots-Tag": "noindex, nofollow",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
}


class ConfirmationPreviewRequest(BaseModel):
    """Admin request for previewing a reservation confirmation form."""

    hotel_id: int
    form_type: ConfirmationFormType
    language: str = DEFAULT_LANGUAGE
    reference_id: str | None = Field(default=None, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        """Normalize unsupported language values to the default language."""
        return normalize_language(value)


class ConfirmationGenerateRequest(ConfirmationPreviewRequest):
    """Admin request for generating a persisted public confirmation form."""

    send_to_customer: bool = False


def _mask_phone_for_log(phone: str) -> str:
    value = phone.strip()
    if len(value) < 4:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def _raw_phone_from_payload(payload: dict[str, Any]) -> str:
    customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}
    return str(customer.get("phone") or payload.get("phone") or "").strip()


def _raw_phone_from_hold(form_type: ConfirmationFormType, hold: asyncpg.Record) -> str:
    row = dict(hold)
    if form_type == "accommodation":
        draft = decode_json_object(row.get("draft_json"))
        return str(draft.get("phone") or "").strip()
    return str(row.get("phone") or "").strip()


async def _build_context(
    conn: asyncpg.Connection,
    body: ConfirmationPreviewRequest,
) -> tuple[Any, asyncpg.Record | None]:
    """Build form context from a hold reference or manual payload."""
    if body.reference_id:
        hold = await load_hold_for_form(
            conn,
            hotel_id=body.hotel_id,
            form_type=body.form_type,
            reference_id=body.reference_id,
        )
        context = build_context_from_hold(
            approval_type=APPROVAL_TYPE_FROM_FORM[body.form_type],
            hold=hold,
            hotel_id=body.hotel_id,
            language=body.language,
        )
        return context, hold
    context = build_context_from_manual_payload(
        form_type=body.form_type,
        hotel_id=body.hotel_id,
        language=body.language,
        payload=body.payload,
    )
    return context, None


async def _send_customer_confirmation(phone: str, message: str, hotel_id: int) -> str | None:
    """Send a confirmation WhatsApp message when operation mode allows it."""
    if not phone or "*" in phone:
        logger.warning("confirmation_form_send_skipped_no_phone", hotel_id=hotel_id)
        return None
    if settings.operation_mode != "ai":
        logger.info(
            "confirmation_form_send_blocked_by_mode",
            hotel_id=hotel_id,
            phone=_mask_phone_for_log(phone),
            operation_mode=settings.operation_mode,
        )
        return None
    whatsapp = get_whatsapp_client()
    started = perf_counter()
    try:
        result = await asyncio.wait_for(
            whatsapp.send_text_message(to=phone, body=message),
            timeout=CUSTOMER_SEND_TIMEOUT_SECONDS,
        )
    except WhatsAppSendBlockedError:
        logger.info("confirmation_form_send_blocked_by_client", hotel_id=hotel_id, phone=_mask_phone_for_log(phone))
        return None
    except Exception:
        logger.warning(
            "confirmation_form_send_failed",
            hotel_id=hotel_id,
            phone=_mask_phone_for_log(phone),
            duration_ms=int((perf_counter() - started) * 1000),
            exc_info=True,
        )
        return None
    if isinstance(result, dict):
        messages = result.get("messages")
        if isinstance(messages, list) and messages and isinstance(messages[0], dict):
            return str(messages[0].get("id") or "").strip() or None
    return None


@admin_router.get("/languages")
async def get_confirmation_form_languages(
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return active language codes available to confirmation forms."""
    check_permission(user, "holds:read")
    return {"items": SUPPORTED_LANGUAGES, "default": DEFAULT_LANGUAGE}


@admin_router.post("/preview")
async def preview_confirmation_form(
    body: ConfirmationPreviewRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Render an HTML confirmation form preview without creating a public URL."""
    check_permission(user, "holds:read")
    ensure_hotel_access(user, body.hotel_id)
    db = request.app.state.db_pool
    try:
        async with db.acquire() as conn:
            context, _hold = await _build_context(conn, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    preview = build_preview(context)
    return {
        "form_type": context.form_type,
        "language": context.language,
        "reference_id": context.reference_id,
        "html": preview.html,
        "whatsapp_message": preview.whatsapp_message,
    }


@admin_router.post("/generate")
async def generate_confirmation_form(
    body: ConfirmationGenerateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a persisted secure confirmation form and optionally send it to the customer."""
    check_permission(user, "holds:approve")
    ensure_hotel_access(user, body.hotel_id)
    db = request.app.state.db_pool
    try:
        async with db.acquire() as conn:
            context, hold = await _build_context(conn, body)
            delivery = await create_confirmation_form(
                conn,
                context=context,
                generated_by=user.display_name or user.username,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    phone = _raw_phone_from_hold(body.form_type, hold) if hold is not None else _raw_phone_from_payload(body.payload)
    whatsapp_message_id: str | None = None
    delivered = False
    delivery_status = "not_requested"
    if body.send_to_customer:
        whatsapp_message_id = await _send_customer_confirmation(phone, delivery.whatsapp_message, body.hotel_id)
        delivered = bool(whatsapp_message_id)
        delivery_status = "sent" if delivered else "not_sent"
        async with db.acquire() as conn:
            await mark_confirmation_sent(
                conn,
                form_id=delivery.form_id,
                whatsapp_message_id=whatsapp_message_id,
                delivered=delivered,
            )

    return {
        "status": "generated",
        "delivery_status": delivery_status,
        "form_id": delivery.form_id,
        "form_type": context.form_type,
        "language": context.language,
        "reference_id": context.reference_id,
        "public_url": delivery.public_url,
        "token_prefix": delivery.token_prefix,
        "whatsapp_message": delivery.whatsapp_message,
    }


@public_router.get("/confirmations/{token}", response_class=HTMLResponse)
async def view_confirmation_form(token: str) -> HTMLResponse:
    """Serve a secure public HTML confirmation form by opaque token."""
    if not token_is_valid(token):
        raise HTTPException(status_code=404, detail="Confirmation form not found")
    row = await fetchrow(
        """
        SELECT html_snapshot
        FROM reservation_confirmation_forms
        WHERE token_hash = $1
          AND revoked_at IS NULL
          AND expires_at > now()
          AND status IN ('ACTIVE', 'SENT', 'DELIVERY_FAILED')
        LIMIT 1
        """,
        hash_public_token(token),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Confirmation form not found")
    return HTMLResponse(
        content=str(row["html_snapshot"]),
        headers=PUBLIC_CONFIRMATION_HEADERS,
    )
