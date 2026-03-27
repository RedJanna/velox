from __future__ import annotations

from typing import Any

import pytest

from velox.core.voice_pipeline import VoicePipelineService
from velox.models.media import AudioTranscriptionResult, InboundMediaItem


class _FakeWhatsAppClient:
    async def download_media_bytes(self, _media_id: str) -> tuple[bytes, str]:
        return b"fake-audio-bytes", "audio/ogg"


class _FakeTranscriptionClient:
    async def transcribe_audio(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
        file_name: str,
        prompt: str = "",
    ) -> AudioTranscriptionResult:
        _ = (audio_bytes, mime_type, file_name, prompt)
        return AudioTranscriptionResult(
            text="Merhaba, yarin icin havaalani transferi istiyorum.",
            language="tr",
            confidence=0.93,
            duration_seconds=4.2,
            model_name="gpt-4o-mini-transcribe",
            mime_type="audio/ogg",
        )


@pytest.mark.asyncio
async def test_process_first_audio_transcribes_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    from velox.core import voice_pipeline

    async def _noop(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(voice_pipeline.settings, "audio_supported_mime_types", "audio/ogg,audio/mpeg")
    monkeypatch.setattr(voice_pipeline.settings, "audio_max_bytes", 16 * 1024 * 1024)
    monkeypatch.setattr(voice_pipeline.settings, "media_retention_hours", 24)
    monkeypatch.setattr(voice_pipeline, "get_transcription_client", lambda: _FakeTranscriptionClient())
    monkeypatch.setattr(voice_pipeline.InboundMediaRepository, "create_pending", _noop)
    monkeypatch.setattr(voice_pipeline.InboundMediaRepository, "mark_analyzed", _noop)
    monkeypatch.setattr(voice_pipeline.InboundMediaRepository, "mark_failed", _noop)

    service = VoicePipelineService(_FakeWhatsAppClient())
    result = await service.process_first_audio(
        hotel_id=21966,
        conversation_id="conv-voice-1",
        media_items=[
            InboundMediaItem(
                media_id="aud-1",
                media_type="audio",
                mime_type="audio/ogg",
                whatsapp_message_id="wamid.voice.1",
            )
        ],
    )

    assert result.analyzed is True
    assert result.transcription is not None
    assert result.transcription.language == "tr"
    assert "havaalani transferi" in result.transcription.text.lower()


@pytest.mark.asyncio
async def test_process_first_audio_rejects_unsupported_mime(monkeypatch: pytest.MonkeyPatch) -> None:
    from velox.core import voice_pipeline

    async def _noop(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(voice_pipeline.settings, "audio_supported_mime_types", "audio/ogg")
    monkeypatch.setattr(voice_pipeline.InboundMediaRepository, "create_pending", _noop)
    monkeypatch.setattr(voice_pipeline.InboundMediaRepository, "mark_failed", _noop)

    service = VoicePipelineService(_FakeWhatsAppClient())
    result = await service.process_first_audio(
        hotel_id=21966,
        conversation_id="conv-voice-2",
        media_items=[
            InboundMediaItem(
                media_id="aud-2",
                media_type="audio",
                mime_type="audio/amr",
                whatsapp_message_id="wamid.voice.2",
            )
        ],
    )

    assert result.analyzed is False
    assert result.failure_reason == "UNSUPPORTED_AUDIO_MIME"
