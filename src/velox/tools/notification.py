"""Notification tool implementation."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

from velox.adapters.whatsapp.client import WhatsAppSendBlockedError, get_whatsapp_client
from velox.db.repositories.hotel import (
    NotificationPhoneRepository,
    NotificationRepository,
)
from velox.tools.base import BaseTool

logger = structlog.get_logger(__name__)

_WHATSAPP_SEND_TIMEOUT = 10.0
_SESSION_REOPEN_TEMPLATE_NAME = "hello_world"
_SESSION_REOPEN_TEMPLATE_LANGUAGE = "en_US"
_SESSION_REOPEN_META_CODES = {470, 131047, 131051}


def _mask_phone(phone: str) -> str:
    """Mask phone for internal notifications."""
    value = phone.strip()
    if len(value) < 4:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def format_notification_message(
    *,
    level: str,
    role: str,
    intent: str,
    hotel_name: str,
    hotel_id: int,
    guest_name: str,
    phone: str,
    transcript_summary: str,
    requested_action: str,
    reference_id: str,
    risk_flags: list[str],
    priority: str,
) -> str:
    """Format notification according to A11.8 internal template."""
    return (
        f"[VELOX-{level}] {role} | {intent}\n"
        f"Hotel: {hotel_name} (#{hotel_id})\n"
        f"Misafir: {guest_name} | {_mask_phone(phone)}\n"
        f"Ozet: {transcript_summary}\n"
        f"Aksiyon: {requested_action}\n"
        f"Ref: {reference_id}\n"
        f"Risk: {risk_flags}\n"
        f"Oncelik: {priority}"
    )


def _format_message_for_delivery(
    *,
    hotel_id: int,
    to_role: str,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Convert notification payload into final delivery text."""
    payload = dict(metadata or {})
    if payload.get("format_standard") != "A11.8":
        return message

    return format_notification_message(
        level=str(payload.get("level", "L1")),
        role=to_role,
        intent=str(payload.get("intent", "other")),
        hotel_name=str(payload.get("hotel_name", "Unknown")),
        hotel_id=hotel_id,
        guest_name=str(payload.get("guest_name", "Unknown")),
        phone=str(payload.get("phone", "***")),
        transcript_summary=str(payload.get("transcript_summary", "")),
        requested_action=str(payload.get("requested_action", "")),
        reference_id=str(payload.get("reference_id", "")),
        risk_flags=list(payload.get("risk_flags", [])),
        priority=str(payload.get("priority", "medium")),
    )


async def _send_alert_with_fallback(whatsapp: Any, *, phone: str, message: str) -> None:
    """Send WhatsApp text and reopen the session window if Meta requires it."""
    try:
        await whatsapp.send_text_message(to=phone, body=message, force=True)
        return
    except httpx.HTTPStatusError as error:
        if not _is_session_reopen_error(error):
            raise

    logger.info("notification_whatsapp_session_reopen_attempt", phone=_mask_phone(phone))
    await whatsapp.send_template_message(
        to=phone,
        template_name=_SESSION_REOPEN_TEMPLATE_NAME,
        language=_SESSION_REOPEN_TEMPLATE_LANGUAGE,
        components=[],
        force=True,
    )
    await whatsapp.send_text_message(to=phone, body=message, force=True)


def _is_session_reopen_error(error: httpx.HTTPStatusError) -> bool:
    """Return True when Meta rejects free-form message because session is closed."""
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


async def send_whatsapp_to_phone(
    *,
    phone: str,
    message: str,
    hotel_id: int | None = None,
) -> bool:
    """Send one WhatsApp alert to a specific phone with session reopen fallback."""
    whatsapp = get_whatsapp_client()
    try:
        await asyncio.wait_for(
            _send_alert_with_fallback(whatsapp, phone=phone, message=message),
            timeout=_WHATSAPP_SEND_TIMEOUT,
        )
        logger.info(
            "notification_whatsapp_sent",
            hotel_id=hotel_id,
            phone=_mask_phone(phone),
        )
        return True
    except WhatsAppSendBlockedError:
        logger.info(
            "notification_whatsapp_blocked_by_mode",
            hotel_id=hotel_id,
            phone=_mask_phone(phone),
        )
        return False
    except Exception:
        logger.warning(
            "notification_whatsapp_failed",
            hotel_id=hotel_id,
            phone=_mask_phone(phone),
            exc_info=True,
        )
        return False


async def send_admin_whatsapp_alerts(
    *,
    hotel_id: int,
    message: str,
    phone_repo: NotificationPhoneRepository | None = None,
) -> list[str]:
    """Send one WhatsApp alert to all active admin notification phones."""
    repository = phone_repo or NotificationPhoneRepository()
    try:
        phones = await repository.get_active_phones(hotel_id)
    except Exception:
        logger.warning("notification_phone_list_failed", hotel_id=hotel_id, exc_info=True)
        phones = [NotificationPhoneRepository.DEFAULT_PHONE]

    delivered: list[str] = []
    seen: set[str] = set()
    for phone in phones:
        normalized = str(phone).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if await send_whatsapp_to_phone(phone=normalized, message=message, hotel_id=hotel_id):
            delivered.append(normalized)
    return delivered


class NotifySendTool(BaseTool):
    """Create notifications across panel and optional channels."""

    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notification_repository = notification_repository

    @staticmethod
    def _format_message_for_delivery(
        *,
        hotel_id: int,
        to_role: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Expose delivery formatter for callers that send outside repository flow."""
        return _format_message_for_delivery(
            hotel_id=hotel_id,
            to_role=to_role,
            message=message,
            metadata=metadata,
        )

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "to_role", "channel", "message"])
        hotel_id = int(kwargs["hotel_id"])
        to_role = str(kwargs["to_role"])
        channel = str(kwargs["channel"]).lower()
        metadata = dict(kwargs.get("metadata") or {})
        message = self._format_message_for_delivery(
            hotel_id=hotel_id,
            to_role=to_role,
            message=str(kwargs["message"]),
            metadata=metadata,
        )

        panel_entry = await self._notification_repository.create(
            hotel_id=hotel_id,
            to_role=to_role,
            channel="panel",
            message=message,
            metadata_json=metadata,
        )
        created_entries = [panel_entry]

        if channel in {"whatsapp", "email"}:
            created_entries.append(
                await self._notification_repository.create(
                    hotel_id=hotel_id,
                    to_role=to_role,
                    channel=channel,
                    message=message,
                    metadata_json=metadata,
                )
            )

        return {
            "notification_id": panel_entry["notification_id"],
            "status": panel_entry["status"],
            "channels_created": [entry["notification_id"] for entry in created_entries],
        }
