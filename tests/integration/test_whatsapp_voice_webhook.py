"""Integration-style tests for WhatsApp voice message handling helpers."""

from __future__ import annotations

from velox.api.routes import whatsapp_webhook
from velox.models.media import AudioTranscriptionResult, InboundMediaItem


class _FakeVoicePipelineService:
    def __init__(self, _client: object) -> None:
        self._client = _client

    async def process_first_audio(self, **_kwargs: object):
        from types import SimpleNamespace

        return SimpleNamespace(
            analyzed=True,
            transcription=AudioTranscriptionResult(
                text="I need a transfer from the airport tonight.",
                language="en",
                confidence=0.92,
                model_name="gpt-4o-mini-transcribe",
                mime_type="audio/ogg",
            ),
            failure_reason=None,
        )


class _FakeVoicePipelineFailureService:
    def __init__(self, _client: object) -> None:
        self._client = _client

    async def process_first_audio(self, **_kwargs: object):
        from types import SimpleNamespace

        return SimpleNamespace(analyzed=False, transcription=None, failure_reason="TRANSCRIPTION_ERROR")


def test_extract_media_items_from_incoming_audio() -> None:
    incoming = whatsapp_webhook.IncomingMessage(
        message_id="wamid.voice.10",
        phone="905551112233",
        display_name="Guest",
        text="audio",
        timestamp=123,
        message_type="audio",
        media_id="media-audio-1",
        media_mime_type="audio/ogg",
        media_sha256="abc",
    )

    items = whatsapp_webhook._extract_media_items_from_incoming(incoming)

    assert len(items) == 1
    assert items[0].media_type == "audio"
    assert items[0].mime_type == "audio/ogg"


async def test_process_voice_message_returns_transcript(monkeypatch) -> None:
    monkeypatch.setattr(whatsapp_webhook.settings, "audio_transcription_enabled", True)
    monkeypatch.setattr(whatsapp_webhook, "VoicePipelineService", _FakeVoicePipelineService)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: object())

    transcript, language, fallback = await whatsapp_webhook._process_voice_message(
        hotel_id=21966,
        conversation_id="conv-voice-helper-1",
        media_items=[InboundMediaItem(media_id="aud-1", media_type="audio", mime_type="audio/ogg")],
    )

    assert transcript == "I need a transfer from the airport tonight."
    assert language == "en"
    assert fallback is None


async def test_process_voice_message_returns_fallback_when_transcription_fails(monkeypatch) -> None:
    monkeypatch.setattr(whatsapp_webhook.settings, "audio_transcription_enabled", True)
    monkeypatch.setattr(whatsapp_webhook, "VoicePipelineService", _FakeVoicePipelineFailureService)
    monkeypatch.setattr(whatsapp_webhook, "get_whatsapp_client", lambda: object())

    transcript, language, fallback = await whatsapp_webhook._process_voice_message(
        hotel_id=21966,
        conversation_id="conv-voice-helper-2",
        media_items=[InboundMediaItem(media_id="aud-2", media_type="audio", mime_type="audio/ogg")],
        preferred_language="tr",
    )

    assert transcript is None
    assert fallback is not None
    assert fallback.internal_json.language == "tr"
    assert fallback.internal_json.next_step == "ask_written_followup"
