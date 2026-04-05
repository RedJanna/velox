"""Deterministic guest-facing response policy for inbound voice messages."""

from __future__ import annotations

from velox.config.settings import settings
from velox.models.conversation import InternalJSON, LLMResponse
from velox.models.media import AudioTranscriptionResult


def build_voice_policy_response(
    *,
    language: str,
    transcription: AudioTranscriptionResult | None,
    failure_reason: str | None = None,
) -> LLMResponse | None:
    """Create a safe response for voice turns when auto-transcription cannot continue."""
    normalized_language = (language or settings.audio_transcription_fallback_language or "en").lower()

    if failure_reason:
        return LLMResponse(
            user_message=_failure_message(normalized_language),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="faq_info",
                state="NEEDS_VERIFICATION",
                handoff={"needed": False},
                risk_flags=["TOOL_UNAVAILABLE"],
                next_step="ask_written_followup",
            ),
        )

    if transcription is None:
        return None

    confidence = transcription.confidence
    text = transcription.text.strip()
    detected_language = (transcription.language or normalized_language).lower()
    safe_language = detected_language if detected_language else normalized_language

    if not text:
        return LLMResponse(
            user_message=_empty_message(safe_language),
            internal_json=InternalJSON(
                language=safe_language,
                intent="faq_info",
                state="NEEDS_VERIFICATION",
                handoff={"needed": False},
                risk_flags=["TOOL_UNAVAILABLE"],
                next_step="ask_written_followup",
            ),
        )

    if confidence < settings.audio_transcription_min_confidence:
        return LLMResponse(
            user_message=_low_confidence_message(safe_language),
            internal_json=InternalJSON(
                language=safe_language,
                intent="faq_info",
                state="NEEDS_VERIFICATION",
                entities={
                    "voice_transcription": {
                        "confidence": confidence,
                        "language": safe_language,
                    }
                },
                handoff={"needed": False},
                risk_flags=["VOICE_LOW_CONFIDENCE"],
                next_step="ask_written_followup",
            ),
        )

    return None


def _failure_message(language: str) -> str:
    if language == "tr":
        return (
            "Sesli mesajinizi aldim ancak su anda tam olarak cozumleyemedim. "
            "Hizli yardimci olabilmem icin ayni talebi kisa bir yazili mesaj olarak paylasir misiniz?"
        )
    return (
        "I received your voice message, but I could not process it clearly right now. "
        "To help you faster, could you please send the same request as a short written message?"
    )


def _empty_message(language: str) -> str:
    if language == "tr":
        return (
            "Sesli mesajinizi aldim fakat net bir icerik ayiklayamadim. "
            "Kisa bir yazili mesaj gonderebilir misiniz?"
        )
    return (
        "I received your voice message, but I could not extract a clear request. "
        "Could you send a short written message?"
    )


def _low_confidence_message(language: str) -> str:
    if language == "tr":
        return (
            "Sesli mesajinizi aldim, ancak yanlis yonlendirme yapmamak icin "
            "bir noktayi yazili olarak netlestirmenizi rica edecegim. "
            "Lutfen talebinizi kisa bir mesajla paylasir misiniz?"
        )
    return (
        "I received your voice message, but to avoid any misunderstanding I’d like to confirm it in writing. "
        "Could you please send your request as a short message?"
    )
