"""Webhook endpoints for approval, payment, and transfer admin events."""

import hashlib
import hmac

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from velox.config.settings import settings
from velox.core.event_processor import EventProcessor
from velox.models.webhook_events import ApprovalEvent, PaymentEvent, TransferEvent

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["admin-webhooks"])


def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate HMAC-SHA256 signature for admin webhook payload."""
    if not secret or not signature:
        return False
    value = signature.removeprefix("sha256=")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, value)


def _extract_signature(request: Request) -> str:
    """Get signature from accepted header names."""
    return (
        request.headers.get("X-Webhook-Signature-256")
        or request.headers.get("X-Webhook-Signature")
        or ""
    )


def _get_event_processor(request: Request) -> EventProcessor:
    """Return app event processor or raise 503 if not initialized."""
    processor = getattr(request.app.state, "event_processor", None)
    if not isinstance(processor, EventProcessor):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Event processor unavailable")
    return processor


@router.post("/approval")
async def approval_webhook(request: Request) -> dict[str, object]:
    """Handle approval decision webhooks from admin panel."""
    payload = await request.body()
    signature = _extract_signature(request)
    if not validate_webhook_signature(payload, signature, settings.admin_webhook_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")

    try:
        event = ApprovalEvent.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        result = await _get_event_processor(request).process_approval_event(event)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("approval_webhook_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval webhook failed",
        ) from exc
    return {"ok": True, "result": result}


@router.post("/payment")
async def payment_webhook(request: Request) -> dict[str, object]:
    """Handle payment status webhooks from admin panel."""
    payload = await request.body()
    signature = _extract_signature(request)
    if not validate_webhook_signature(payload, signature, settings.admin_webhook_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")

    try:
        event = PaymentEvent.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        result = await _get_event_processor(request).process_payment_event(event)
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_400_BAD_REQUEST if detail == "invalid_payment_status" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except Exception as exc:
        logger.exception("payment_webhook_failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment webhook failed") from exc
    return {"ok": True, "result": result}


@router.post("/transfer")
async def transfer_webhook(request: Request) -> dict[str, object]:
    """Handle transfer status webhooks from admin panel."""
    payload = await request.body()
    signature = _extract_signature(request)
    if not validate_webhook_signature(payload, signature, settings.admin_webhook_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")

    try:
        event = TransferEvent.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        result = await _get_event_processor(request).process_transfer_event(event)
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_400_BAD_REQUEST if detail == "invalid_transfer_status" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except Exception as exc:
        logger.exception("transfer_webhook_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transfer webhook failed",
        ) from exc
    return {"ok": True, "result": result}
