"""Meta WhatsApp Business Cloud API client."""

import asyncio
import time
from pathlib import Path
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

    async def download_media_bytes(self, media_id: str) -> tuple[bytes, str]:
        """Download incoming media bytes from WhatsApp and return payload + mime."""
        client = await self._get_client()
        metadata_path = f"/{media_id}"
        last_error: Exception | None = None
        media_url = ""
        mime_type = ""

        for attempt in range(MAX_RETRIES):
            try:
                meta_resp = await client.get(metadata_path)
                meta_resp.raise_for_status()
                metadata = cast(dict[str, Any], meta_resp.json())
                media_url = str(metadata.get("url") or "").strip()
                mime_type = str(metadata.get("mime_type") or "").strip()
                if media_url:
                    break
                raise RuntimeError("Missing media URL in WhatsApp metadata response.")
            except Exception as error:
                last_error = error
                logger.warning(
                    "whatsapp_media_metadata_error",
                    media_id=media_id[:12],
                    attempt=attempt + 1,
                    error_type=type(error).__name__,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])

        if not media_url:
            if last_error is not None:
                raise last_error
            raise RuntimeError("Failed to fetch WhatsApp media metadata.")

        for attempt in range(MAX_RETRIES):
            try:
                binary_resp = await client.get(media_url, headers={"Authorization": f"Bearer {self.access_token}"})
                binary_resp.raise_for_status()
                resolved_mime = mime_type or str(binary_resp.headers.get("content-type") or "").strip()
                logger.info(
                    "whatsapp_media_download_ok",
                    media_id=media_id[:12],
                    bytes=len(binary_resp.content),
                )
                return bytes(binary_resp.content), resolved_mime
            except Exception as error:
                last_error = error
                logger.warning(
                    "whatsapp_media_download_error",
                    media_id=media_id[:12],
                    attempt=attempt + 1,
                    error_type=type(error).__name__,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])

        if last_error is not None:
            raise last_error
        raise RuntimeError("Failed to download WhatsApp media bytes.")

    async def _upload_media(self, *, file_path: Path, mime_type: str) -> str:
        """Upload media binary to WhatsApp and return media id."""
        client = await self._get_client()
        path = f"/{self.phone_number_id}/media"
        file_bytes = await asyncio.to_thread(file_path.read_bytes)
        files = {
            "file": (file_path.name, file_bytes, mime_type),
        }
        data = {
            "messaging_product": "whatsapp",
            "type": mime_type,
        }

        response = await client.post(path, data=data, files=files)
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
        media_id = str(payload.get("id") or "").strip()
        if not media_id:
            raise RuntimeError("WhatsApp media id missing in upload response.")
        return media_id

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

    async def send_image_message(
        self,
        *,
        to: str,
        file_path: Path,
        mime_type: str,
        caption: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Send an image message using uploaded media id."""
        self._assert_send_allowed("send_image_message", to, force=force)
        normalized_to = _normalize_recipient_phone(to)
        media_id = await self._upload_media(file_path=file_path, mime_type=mime_type)
        image_payload: dict[str, Any] = {"id": media_id}
        if caption:
            image_payload["caption"] = caption[:1024]
        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "image",
            "image": image_payload,
        }
        logger.info("whatsapp_send_image", to=_mask_phone(normalized_to), media_id=media_id)
        return await self._request(payload)

    async def send_document_message(
        self,
        *,
        to: str,
        file_path: Path,
        mime_type: str,
        file_name: str | None = None,
        caption: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Send a document message using uploaded media id."""
        self._assert_send_allowed("send_document_message", to, force=force)
        normalized_to = _normalize_recipient_phone(to)
        media_id = await self._upload_media(file_path=file_path, mime_type=mime_type)
        document_payload: dict[str, Any] = {"id": media_id}
        if file_name:
            document_payload["filename"] = file_name[:240]
        if caption:
            document_payload["caption"] = caption[:1024]
        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "document",
            "document": document_payload,
        }
        logger.info("whatsapp_send_document", to=_mask_phone(normalized_to), media_id=media_id)
        return await self._request(payload)

    async def send_audio_message(
        self,
        *,
        to: str,
        file_path: Path,
        mime_type: str,
        force: bool = False,
    ) -> dict[str, Any]:
        """Send an audio message using uploaded media id."""
        self._assert_send_allowed("send_audio_message", to, force=force)
        normalized_to = _normalize_recipient_phone(to)
        media_id = await self._upload_media(file_path=file_path, mime_type=mime_type)
        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "audio",
            "audio": {"id": media_id},
        }
        logger.info("whatsapp_send_audio", to=_mask_phone(normalized_to), media_id=media_id)
        return await self._request(payload)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language: str,
        components: list[dict[str, Any]],
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        """Send a template message."""
        self._assert_send_allowed("send_template_message", to, force=force)
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
