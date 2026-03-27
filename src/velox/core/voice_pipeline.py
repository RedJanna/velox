"""Inbound voice message processing pipeline for WhatsApp guest audio."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import structlog

from velox.adapters.whatsapp.client import WhatsAppClient
from velox.config.settings import settings
from velox.db.repositories.inbound_media import InboundMediaRepository
from velox.llm.transcription_client import get_transcription_client
from velox.models.media import AudioTranscriptionResult, InboundMediaItem

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class VoicePipelineResult:
    """Pipeline result for one inbound voice message."""

    analyzed: bool
    transcription: AudioTranscriptionResult | None = None
    failure_reason: str | None = None


class VoicePipelineService:
    """Coordinates audio download, transcription, and DB persistence."""

    def __init__(self, whatsapp_client: WhatsAppClient) -> None:
        self._whatsapp_client = whatsapp_client
        self._repository = InboundMediaRepository()

    async def process_first_audio(
        self,
        *,
        hotel_id: int,
        conversation_id: Any,
        media_items: list[InboundMediaItem],
    ) -> VoicePipelineResult:
        """Process the first audio item and return a policy-ready result."""
        audio_item = next((item for item in media_items if item.media_type == "audio"), None)
        if audio_item is None:
            return VoicePipelineResult(analyzed=False, failure_reason="NO_AUDIO_FOUND")

        safe_mime = audio_item.mime_type.lower().strip()
        await self._safe_create_pending(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            audio_item=audio_item,
            safe_mime=safe_mime,
        )

        supported_mime_types = set(settings.audio_supported_mime_type_list)
        if safe_mime and safe_mime not in supported_mime_types:
            await self._safe_mark_failed(
                audio_item=audio_item,
                status="UNSUPPORTED",
                error_type="UNSUPPORTED_AUDIO_MIME",
                error_detail=safe_mime,
            )
            return VoicePipelineResult(analyzed=False, failure_reason="UNSUPPORTED_AUDIO_MIME")

        try:
            raw_bytes, resolved_mime = await self._whatsapp_client.download_media_bytes(audio_item.media_id)
            if not raw_bytes:
                raise RuntimeError("EMPTY_AUDIO")
            if len(raw_bytes) > settings.audio_max_bytes:
                await self._safe_mark_failed(
                    audio_item=audio_item,
                    status="FAILED",
                    error_type="AUDIO_TOO_LARGE",
                    error_detail=f"bytes={len(raw_bytes)}",
                )
                return VoicePipelineResult(analyzed=False, failure_reason="AUDIO_TOO_LARGE")

            media_hash = hashlib.sha256(raw_bytes).hexdigest()
            transcription_client = get_transcription_client()
            transcription = await transcription_client.transcribe_audio(
                audio_bytes=raw_bytes,
                mime_type=resolved_mime or safe_mime,
                file_name=_resolve_audio_filename(resolved_mime or safe_mime),
            )
            await self._safe_mark_transcribed(
                audio_item=audio_item,
                transcription=transcription,
                file_size_bytes=len(raw_bytes),
                sha256=media_hash,
            )
            logger.info(
                "voice_transcription_completed",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                confidence=transcription.confidence,
                detected_language=transcription.language,
            )
            return VoicePipelineResult(analyzed=True, transcription=transcription)
        except Exception as error:
            await self._safe_mark_failed(
                audio_item=audio_item,
                error_type=type(error).__name__,
                error_detail=str(error),
            )
            logger.warning(
                "voice_transcription_failed",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                error_type=type(error).__name__,
            )
            return VoicePipelineResult(analyzed=False, failure_reason="TRANSCRIPTION_ERROR")

    async def _safe_create_pending(
        self,
        *,
        hotel_id: int,
        conversation_id: Any,
        audio_item: InboundMediaItem,
        safe_mime: str,
    ) -> None:
        try:
            await self._repository.create_pending(
                hotel_id=hotel_id,
                conversation_id=conversation_id,
                whatsapp_message_id=audio_item.whatsapp_message_id,
                whatsapp_media_id=audio_item.media_id,
                media_type=audio_item.media_type,
                mime_type=safe_mime,
                caption=audio_item.caption,
                sha256=audio_item.sha256 or None,
                expires_hours=settings.media_retention_hours,
            )
        except Exception as error:
            logger.warning(
                "voice_persist_pending_failed",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                error_type=type(error).__name__,
            )

    async def _safe_mark_failed(
        self,
        *,
        audio_item: InboundMediaItem,
        error_type: str,
        error_detail: str,
        status: str = "FAILED",
    ) -> None:
        try:
            await self._repository.mark_failed(
                whatsapp_message_id=audio_item.whatsapp_message_id,
                whatsapp_media_id=audio_item.media_id,
                status=status,
                error_type=error_type,
                error_detail=error_detail,
            )
        except Exception as persist_error:
            logger.warning(
                "voice_persist_failed_status_failed",
                whatsapp_message_id=audio_item.whatsapp_message_id,
                whatsapp_media_id=audio_item.media_id,
                error_type=type(persist_error).__name__,
            )

    async def _safe_mark_transcribed(
        self,
        *,
        audio_item: InboundMediaItem,
        transcription: AudioTranscriptionResult,
        file_size_bytes: int,
        sha256: str,
    ) -> None:
        try:
            await self._repository.mark_analyzed(
                whatsapp_message_id=audio_item.whatsapp_message_id,
                whatsapp_media_id=audio_item.media_id,
                analysis_json={
                    "kind": "audio_transcription",
                    "text": transcription.text,
                    "language": transcription.language,
                    "duration_seconds": transcription.duration_seconds,
                    "confidence": transcription.confidence,
                    "mime_type": transcription.mime_type,
                    "raw": transcription.raw_json,
                },
                confidence=transcription.confidence,
                model_name=transcription.model_name,
                risk_flags=[],
                file_size_bytes=file_size_bytes,
                sha256=sha256,
            )
        except Exception as error:
            logger.warning(
                "voice_persist_transcribed_failed",
                whatsapp_message_id=audio_item.whatsapp_message_id,
                whatsapp_media_id=audio_item.media_id,
                error_type=type(error).__name__,
            )


def _resolve_audio_filename(mime_type: str) -> str:
    safe_mime = (mime_type or "audio/ogg").lower()
    if "mpeg" in safe_mime or safe_mime.endswith("/mp3"):
        return "voice.mp3"
    if "wav" in safe_mime:
        return "voice.wav"
    if "webm" in safe_mime:
        return "voice.webm"
    if "mp4" in safe_mime or "aac" in safe_mime:
        return "voice.m4a"
    if "amr" in safe_mime:
        return "voice.amr"
    return "voice.ogg"
