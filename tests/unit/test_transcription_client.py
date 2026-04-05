from __future__ import annotations

from types import SimpleNamespace

import pytest

from velox.llm import transcription_client
from velox.llm.transcription_client import _estimate_confidence


def test_estimate_confidence_from_segments() -> None:
    payload = {
        "segments": [
            {"avg_logprob": -0.2},
            {"avg_logprob": -1.0},
        ]
    }

    confidence = _estimate_confidence(payload)

    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.5


def test_estimate_confidence_without_segments_uses_text_presence() -> None:
    with_text = _estimate_confidence({"text": "hello"})
    without_text = _estimate_confidence({"text": ""})

    assert with_text == 0.85
    assert without_text == 0.0


def test_estimate_confidence_preserves_negative_logprobs() -> None:
    payload = {
        "segments": [
            {"avg_logprob": -5.0},
            {"avg_logprob": -4.0},
        ]
    }

    confidence = _estimate_confidence(payload)

    assert confidence == 0.1


@pytest.mark.asyncio
async def test_transcribe_audio_uses_json_response_format(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict[str, object]:
            return {"text": "Merhabalar.", "logprobs": None}

    class _FakeTranscriptions:
        async def create(self, **kwargs: object) -> _FakeResponse:
            captured.update(kwargs)
            return _FakeResponse()

    class _FakeAsyncOpenAI:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.audio = SimpleNamespace(transcriptions=_FakeTranscriptions())

        async def close(self) -> None:
            return None

    monkeypatch.setattr(transcription_client, "AsyncOpenAI", _FakeAsyncOpenAI)

    client = transcription_client.TranscriptionClient()
    result = await client.transcribe_audio(
        audio_bytes=b"fake-audio",
        mime_type="audio/ogg",
        file_name="voice.ogg",
    )

    assert captured["response_format"] == "json"
    assert result.text == "Merhabalar."
    assert result.mime_type == "audio/ogg"
    assert result.confidence == 0.85
