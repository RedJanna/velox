"""Unit tests for media analysis pipeline."""

from __future__ import annotations

from typing import Any

import pytest

from velox.core.media_pipeline import MediaPipelineService
from velox.models.media import InboundMediaItem, VisionAnalysisResult


class _FakeWhatsAppClient:
    async def download_media_bytes(self, _media_id: str) -> tuple[bytes, str]:
        return b"fake-image-bytes", "image/webp"


class _FakeVisionClient:
    async def analyze_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        caption: str,
        language: str,
    ) -> VisionAnalysisResult:
        _ = (image_bytes, mime_type, caption, language)
        return VisionAnalysisResult(
            intent="general_photo_info",
            confidence=0.88,
            summary="pool area",
            detected_text="",
            risk_flags=[],
            requires_handoff=False,
        )


@pytest.mark.asyncio
async def test_process_first_image_webp_with_normalization(monkeypatch: pytest.MonkeyPatch) -> None:
    """WEBP should be accepted when normalization returns a supported output."""
    from velox.core import media_pipeline

    async def _noop(*_args: Any, **_kwargs: Any) -> None:
        return None

    class _Normalized:
        ok = True
        image_bytes = b"normalized-jpeg"
        mime_type = "image/jpeg"
        reason = ""
        transformed = True

    monkeypatch.setattr(media_pipeline.settings, "media_supported_mime_types", "image/jpeg,image/webp")
    monkeypatch.setattr(media_pipeline.settings, "media_max_bytes", 8 * 1024 * 1024)
    monkeypatch.setattr(media_pipeline.settings, "media_max_image_dimension", 2048)
    monkeypatch.setattr(media_pipeline.settings, "media_retention_hours", 24)
    monkeypatch.setattr(media_pipeline, "get_vision_client", lambda: _FakeVisionClient())
    monkeypatch.setattr(media_pipeline, "normalize_image_for_vision", lambda **_kwargs: _Normalized())
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "create_pending", _noop)
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "mark_analyzed", _noop)
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "mark_failed", _noop)

    service = MediaPipelineService(_FakeWhatsAppClient())
    result = await service.process_first_image(
        hotel_id=21966,
        conversation_id="conv-1",
        language="tr",
        media_items=[
            InboundMediaItem(
                media_id="mid-1",
                media_type="image",
                mime_type="image/webp",
                whatsapp_message_id="wamid.1",
            )
        ],
    )
    assert result.analyzed is True
    assert result.analysis is not None
    assert result.analysis.confidence == 0.88


@pytest.mark.asyncio
async def test_process_first_image_normalization_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normalization failure should produce safe non-analyzed result."""
    from velox.core import media_pipeline

    async def _noop(*_args: Any, **_kwargs: Any) -> None:
        return None

    class _NormalizedFail:
        ok = False
        image_bytes = b""
        mime_type = ""
        reason = "IMAGE_NORMALIZER_UNAVAILABLE"
        transformed = False

    monkeypatch.setattr(media_pipeline.settings, "media_supported_mime_types", "image/jpeg,image/webp")
    monkeypatch.setattr(media_pipeline.settings, "media_max_bytes", 8 * 1024 * 1024)
    monkeypatch.setattr(media_pipeline.settings, "media_max_image_dimension", 2048)
    monkeypatch.setattr(media_pipeline.settings, "media_retention_hours", 24)
    monkeypatch.setattr(media_pipeline, "normalize_image_for_vision", lambda **_kwargs: _NormalizedFail())
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "create_pending", _noop)
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "mark_analyzed", _noop)
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "mark_failed", _noop)

    service = MediaPipelineService(_FakeWhatsAppClient())
    result = await service.process_first_image(
        hotel_id=21966,
        conversation_id="conv-2",
        language="tr",
        media_items=[
            InboundMediaItem(
                media_id="mid-2",
                media_type="image",
                mime_type="image/webp",
                whatsapp_message_id="wamid.2",
            )
        ],
    )
    assert result.analyzed is False
    assert result.failure_reason == "IMAGE_NORMALIZER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_process_first_image_does_not_crash_when_pending_persist_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistence errors before analysis must not break guest-facing media reply flow."""
    from velox.core import media_pipeline

    async def _raise_pending(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("relation inbound_media does not exist")

    async def _noop(*_args: Any, **_kwargs: Any) -> None:
        return None

    class _Normalized:
        ok = True
        image_bytes = b"normalized-jpeg"
        mime_type = "image/jpeg"
        reason = ""
        transformed = True

    monkeypatch.setattr(media_pipeline.settings, "media_supported_mime_types", "image/jpeg,image/webp")
    monkeypatch.setattr(media_pipeline.settings, "media_max_bytes", 8 * 1024 * 1024)
    monkeypatch.setattr(media_pipeline.settings, "media_max_image_dimension", 2048)
    monkeypatch.setattr(media_pipeline.settings, "media_retention_hours", 24)
    monkeypatch.setattr(media_pipeline, "get_vision_client", lambda: _FakeVisionClient())
    monkeypatch.setattr(media_pipeline, "normalize_image_for_vision", lambda **_kwargs: _Normalized())
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "create_pending", _raise_pending)
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "mark_analyzed", _noop)
    monkeypatch.setattr(media_pipeline.InboundMediaRepository, "mark_failed", _noop)

    service = MediaPipelineService(_FakeWhatsAppClient())
    result = await service.process_first_image(
        hotel_id=21966,
        conversation_id="conv-3",
        language="tr",
        media_items=[
            InboundMediaItem(
                media_id="mid-3",
                media_type="image",
                mime_type="image/webp",
                whatsapp_message_id="wamid.3",
            )
        ],
    )
    assert result.analyzed is True
    assert result.analysis is not None
    assert result.analysis.intent == "general_photo_info"
