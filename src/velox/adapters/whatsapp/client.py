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


def _mask_phone(phone: str) -> str:
    """Return masked phone for safe logs."""
    if len(phone) < 4:
        return "***"
    return f"{phone[:3]}***{phone[-2:]}"


class WhatsAppClient:
    """Meta WhatsApp Business Cloud API client."""

    def __init__(self, app_settings: Settings) -> None:
        self.base_url = f"{app_settings.whatsapp_api_base_url}/{app_settings.whatsapp_api_version}"
        self.phone_number_id = app_settings.whatsapp_phone_number_id
        self.access_token = app_settings.whatsapp_access_token
        self._client: httpx.AsyncClient | None = None

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

    async def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        """Send a plain text message."""
        truncated = body if len(body) <= MAX_MESSAGE_LENGTH else f"{body[: MAX_MESSAGE_LENGTH - 3]}..."
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": truncated},
        }
        logger.info("whatsapp_send_text", to=_mask_phone(to))
        return await self._request(payload)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language: str,
        components: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Send a template message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components,
            },
        }
        logger.info("whatsapp_send_template", to=_mask_phone(to), template_name=template_name)
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
