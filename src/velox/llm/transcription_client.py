"""OpenAI audio transcription helper for inbound WhatsApp voice messages."""

from __future__ import annotations

import asyncio
import io
import time
from typing import Any, Literal

import structlog
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from velox.config.settings import settings
from velox.models.media import AudioTranscriptionResult

logger = structlog.get_logger(__name__)

TRANSCRIPTION_TIMEOUT_SECONDS = 25.0
TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
TRANSCRIPTION_RESPONSE_FORMAT: Literal["json"] = "json"
TRANSCRIPTION_RETRY_BACKOFF_SECONDS = (1.0, 3.0, 5.0)
TRANSCRIPTION_MAX_ATTEMPTS = 3


class TranscriptionUnavailableError(RuntimeError):
    """Raised when transcription service is unavailable."""


class TranscriptionClient:
    """Small wrapper around OpenAI transcription API."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = TRANSCRIPTION_MODEL

    async def close(self) -> None:
        """Close underlying HTTP resources."""
        await self._client.close()

    async def transcribe_audio(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
        file_name: str,
        prompt: str = "",
    ) -> AudioTranscriptionResult:
        """Transcribe audio and return normalized text + language metadata."""
        safe_name = file_name or "voice.ogg"
        buffer = io.BytesIO(audio_bytes)
        buffer.name = safe_name
        last_error: Exception | None = None

        for attempt in range(1, TRANSCRIPTION_MAX_ATTEMPTS + 1):
            started_at = time.perf_counter()
            try:
                request_payload: dict[str, Any] = {
                    "model": self._model,
                    "file": buffer,
                    "response_format": TRANSCRIPTION_RESPONSE_FORMAT,
                    "timeout": TRANSCRIPTION_TIMEOUT_SECONDS,
                }
                if prompt:
                    request_payload["prompt"] = prompt[:400]
                response = await self._client.audio.transcriptions.create(**request_payload)
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                payload = response.model_dump() if hasattr(response, "model_dump") else {"text": str(response)}
                logger.info(
                    "audio_transcription_ok",
                    model=self._model,
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                    response_format=TRANSCRIPTION_RESPONSE_FORMAT,
                )
                language = str(payload.get("language") or "").strip().lower()
                text = str(payload.get("text") or "").strip()
                duration_seconds = _safe_float(payload.get("duration"))
                confidence = _estimate_confidence(payload)
                return AudioTranscriptionResult(
                    text=text,
                    language=language,
                    duration_seconds=duration_seconds,
                    confidence=confidence,
                    model_name=self._model,
                    mime_type=mime_type,
                    raw_json=payload,
                )
            except (RateLimitError, APITimeoutError, APIConnectionError) as error:
                last_error = error
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                logger.warning(
                    "audio_transcription_retryable_error",
                    model=self._model,
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                    error_type=type(error).__name__,
                    error_message=str(error)[:240],
                )
            except Exception as error:  # pragma: no cover - defensive branch
                last_error = error
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                logger.warning(
                    "audio_transcription_non_retryable_error",
                    model=self._model,
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                    error_type=type(error).__name__,
                    error_message=str(error)[:240],
                )
                break

            if attempt < TRANSCRIPTION_MAX_ATTEMPTS:
                buffer.seek(0)
                backoff = TRANSCRIPTION_RETRY_BACKOFF_SECONDS[
                    min(attempt - 1, len(TRANSCRIPTION_RETRY_BACKOFF_SECONDS) - 1)
                ]
                await asyncio.sleep(backoff)

        raise TranscriptionUnavailableError("Audio transcription unavailable") from last_error


def _safe_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed >= 0 else 0.0


def _safe_logprob(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _estimate_confidence(payload: dict[str, Any]) -> float:
    segments = payload.get("segments")
    if not isinstance(segments, list) or not segments:
        text = str(payload.get("text") or "").strip()
        return 0.85 if text else 0.0

    values: list[float] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        logprob = segment.get("avg_logprob")
        if logprob in (None, ""):
            continue
        numeric = _safe_logprob(logprob)
        if numeric is None:
            continue
        confidence = max(0.0, min(1.0, 1.0 + (numeric / 5.0)))
        values.append(confidence)

    if not values:
        return 0.75
    return round(sum(values) / len(values), 4)


_transcription_client: TranscriptionClient | None = None


def get_transcription_client() -> TranscriptionClient:
    """Return singleton transcription client."""
    global _transcription_client
    if _transcription_client is None:
        _transcription_client = TranscriptionClient()
    return _transcription_client


async def close_transcription_client() -> None:
    """Close singleton transcription client."""
    global _transcription_client
    if _transcription_client is not None:
        await _transcription_client.close()
        _transcription_client = None
