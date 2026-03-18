"""Meta WhatsApp Business Cloud API client."""

import asyncio
import time
from typing import Any, cast

import httpx
import structlog

from velox.config.settings import Settings, settings

logger = structlog.get_logger(__name__)

REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 5]
MAX_MESSAGE_LENGTH = 4096


def _normalize_recipient_phone(phone: str) -> str:
    """Normalize recipient phone into WhatsApp Cloud API accepted format."""
    raw = phone.strip()
    if not raw:
        return raw

    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return raw

    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        # Local Turkish mobile format (05xx...) -> international.
        digits = f"90{digits[1:]}"

    return digits


def _mask_phone(phone: str) -> str:
    """Return masked phone for safe logs."""
    if len(phone) < 4:
        return "***"
    return f"{phone[:3]}***{phone[-2:]}"


class WhatsAppSendBlockedError(Exception):
    """Raised when outbound messaging is blocked by the current operation mode."""


class WhatsAppClient:
    """Meta WhatsApp Business Cloud API client."""

    def __init__(self, app_settings: Settings) -> None:
        self.base_url = f"{app_settings.whatsapp_api_base_url}/{app_settings.whatsapp_api_version}"
        self.phone_number_id = app_settings.whatsapp_phone_number_id
        self.access_token = app_settings.whatsapp_access_token
        self._settings = app_settings
        self._client: httpx.AsyncClient | None = None

    def _assert_send_allowed(self, action: str, to: str, *, force: bool = False) -> None:
        """Block outbound messages unless operation_mode is 'ai' or force is True."""
        if force:
            return
        mode = self._settings.operation_mode
        if mode == "ai":
            return
        logger.warning(
            "whatsapp_send_blocked",
            operation_mode=mode,
            action=action,
            to=_mask_phone(to),
        )
        raise WhatsAppSendBlockedError(
            f"Outbound WhatsApp messaging is blocked in '{mode}' mode. "
            f"Switch to 'ai' mode to enable sending."
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST message request with retry/backoff."""
        client = await self._get_client()
        path = f"/{self.phone_number_id}/messages"
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            start_time = time.perf_counter()
            try:
                response = await client.post(path, json=payload)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                response.raise_for_status()
                logger.info("whatsapp_send_ok", response_code=response.status_code, duration_ms=duration_ms)
                return cast(dict[str, Any], response.json())
            except httpx.TimeoutException as error:
                last_error = error
                logger.warning("whatsapp_timeout", attempt=attempt + 1, response_code=0)
            except httpx.HTTPStatusError as error:
                last_error = error
                status_code = error.response.status_code
                logger.warning("whatsapp_http_error", attempt=attempt + 1, response_code=status_code)
                if 400 <= status_code < 500:
                    raise
            except httpx.RequestError as error:
                last_error = error
                logger.warning("whatsapp_request_error", attempt=attempt + 1, error_type=type(error).__name__)

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])

        if last_error is not None:
            raise last_error
        raise RuntimeError("WhatsApp request failed.")

    async def send_text_message(self, to: str, body: str, *, force: bool = False) -> dict[str, Any]:
        """Send a plain text message."""
        self._assert_send_allowed("send_text_message", to, force=force)
        normalized_to = _normalize_recipient_phone(to)
        truncated = body if len(body) <= MAX_MESSAGE_LENGTH else f"{body[: MAX_MESSAGE_LENGTH - 3]}..."
        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "text",
            "text": {"body": truncated},
        }
        logger.info("whatsapp_send_text", to=_mask_phone(normalized_to))
        return await self._request(payload)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language: str,
        components: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Send a template message."""
        self._assert_send_allowed("send_template_message", to)
        normalized_to = _normalize_recipient_phone(to)
        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components,
            },
        }
        logger.info("whatsapp_send_template", to=_mask_phone(normalized_to), template_name=template_name)
        return await self._request(payload)

    async def mark_as_read(self, message_id: str) -> None:
        """Mark an incoming message as read."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        await self._request(payload)


_whatsapp_client: WhatsAppClient | None = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create singleton WhatsApp client."""
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppClient(settings)
    return _whatsapp_client


async def close_whatsapp_client() -> None:
    """Close singleton WhatsApp client."""
    global _whatsapp_client
    if _whatsapp_client is not None:
        await _whatsapp_client.close()
        _whatsapp_client = None
