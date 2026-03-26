"""Inbound media processing pipeline for WhatsApp guest images."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import structlog

from velox.adapters.whatsapp.client import WhatsAppClient
from velox.config.settings import settings
from velox.core.media_image_processor import normalize_image_for_vision
from velox.db.repositories.inbound_media import InboundMediaRepository
from velox.llm.vision_client import get_vision_client
from velox.models.media import InboundMediaItem, VisionAnalysisResult

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class MediaPipelineResult:
    """Pipeline result for one media message."""

    analyzed: bool
    analysis: VisionAnalysisResult | None = None
    failure_reason: str | None = None


class MediaPipelineService:
    """Coordinates media download, analysis, and DB persistence."""

    def __init__(self, whatsapp_client: WhatsAppClient) -> None:
        self._whatsapp_client = whatsapp_client
        self._repository = InboundMediaRepository()

    async def _safe_create_pending(
        self,
        *,
        hotel_id: int,
        conversation_id: Any,
        image_item: InboundMediaItem,
        safe_mime: str,
    ) -> None:
        """Persist pending media row without breaking guest-facing flow."""
        try:
            await self._repository.create_pending(
                hotel_id=hotel_id,
                conversation_id=conversation_id,
                whatsapp_message_id=image_item.whatsapp_message_id,
                whatsapp_media_id=image_item.media_id,
                media_type=image_item.media_type,
                mime_type=safe_mime,
                caption=image_item.caption,
                sha256=image_item.sha256 or None,
                expires_hours=settings.media_retention_hours,
            )
        except Exception as error:
            logger.warning(
                "media_persist_pending_failed",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                error_type=type(error).__name__,
            )

    async def _safe_mark_failed(
        self,
        *,
        image_item: InboundMediaItem,
        error_type: str,
        error_detail: str,
        status: str = "FAILED",
    ) -> None:
        """Persist failed status without raising secondary errors."""
        try:
            await self._repository.mark_failed(
                whatsapp_message_id=image_item.whatsapp_message_id,
                whatsapp_media_id=image_item.media_id,
                status=status,
                error_type=error_type,
                error_detail=error_detail,
            )
        except Exception as persist_error:
            logger.warning(
                "media_persist_failed_status_failed",
                whatsapp_message_id=image_item.whatsapp_message_id,
                whatsapp_media_id=image_item.media_id,
                error_type=type(persist_error).__name__,
            )

    async def _safe_mark_analyzed(
        self,
        *,
        image_item: InboundMediaItem,
        analysis: VisionAnalysisResult,
        file_size_bytes: int,
        sha256: str,
    ) -> None:
        """Persist successful analysis without affecting guest reply."""
        try:
            await self._repository.mark_analyzed(
                whatsapp_message_id=image_item.whatsapp_message_id,
                whatsapp_media_id=image_item.media_id,
                analysis_json=analysis.model_dump(mode="json"),
                confidence=analysis.confidence,
                model_name="gpt-4o-mini",
                risk_flags=analysis.risk_flags,
                file_size_bytes=file_size_bytes,
                sha256=sha256,
            )
        except Exception as error:
            logger.warning(
                "media_persist_analyzed_failed",
                whatsapp_message_id=image_item.whatsapp_message_id,
                whatsapp_media_id=image_item.media_id,
                error_type=type(error).__name__,
            )

    async def process_first_image(
        self,
        *,
        hotel_id: int,
        conversation_id: Any,
        language: str,
        media_items: list[InboundMediaItem],
    ) -> MediaPipelineResult:
        """Process the first image item and return a policy-ready result."""
        image_item = next((item for item in media_items if item.media_type == "image"), None)
        if image_item is None:
            return MediaPipelineResult(analyzed=False, failure_reason="NO_IMAGE_FOUND")

        safe_mime = image_item.mime_type.lower().strip()
        await self._safe_create_pending(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            image_item=image_item,
            safe_mime=safe_mime,
        )

        supported_mime_types = set(settings.media_supported_mime_type_list)
        if safe_mime not in supported_mime_types:
            await self._safe_mark_failed(
                image_item=image_item,
                status="UNSUPPORTED",
                error_type="UNSUPPORTED_MIME",
                error_detail=safe_mime or "missing mime_type",
            )
            return MediaPipelineResult(analyzed=False, failure_reason="UNSUPPORTED_MIME")

        try:
            raw_bytes, resolved_mime = await self._whatsapp_client.download_media_bytes(image_item.media_id)
            if not raw_bytes:
                raise RuntimeError("EMPTY_MEDIA")
            if len(raw_bytes) > settings.media_max_bytes:
                await self._safe_mark_failed(
                    image_item=image_item,
                    status="FAILED",
                    error_type="MEDIA_TOO_LARGE",
                    error_detail=f"bytes={len(raw_bytes)}",
                )
                return MediaPipelineResult(analyzed=False, failure_reason="MEDIA_TOO_LARGE")

            normalized = normalize_image_for_vision(
                image_bytes=raw_bytes,
                mime_type=resolved_mime or safe_mime,
                max_dimension=settings.media_max_image_dimension,
            )
            if not normalized.ok:
                await self._safe_mark_failed(
                    image_item=image_item,
                    status="UNSUPPORTED",
                    error_type=normalized.reason or "IMAGE_NORMALIZER_FAILED",
                    error_detail=resolved_mime or safe_mime,
                )
                return MediaPipelineResult(analyzed=False, failure_reason=normalized.reason or "NORMALIZE_FAILED")

            media_hash = hashlib.sha256(raw_bytes).hexdigest()
            vision_client = get_vision_client()
            analysis = await vision_client.analyze_image(
                image_bytes=normalized.image_bytes,
                mime_type=normalized.mime_type,
                caption=image_item.caption,
                language=language,
            )
            await self._safe_mark_analyzed(
                image_item=image_item,
                analysis=analysis,
                file_size_bytes=len(raw_bytes),
                sha256=media_hash,
            )
            logger.info(
                "media_analysis_completed",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                media_type=image_item.media_type,
                confidence=analysis.confidence,
                intent=analysis.intent,
            )
            return MediaPipelineResult(analyzed=True, analysis=analysis)
        except Exception as error:
            await self._safe_mark_failed(
                image_item=image_item,
                error_type=type(error).__name__,
                error_detail=str(error),
            )
            logger.warning(
                "media_analysis_failed",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                error_type=type(error).__name__,
            )
            return MediaPipelineResult(analyzed=False, failure_reason="ANALYSIS_ERROR")
