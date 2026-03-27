from velox.core.voice_response_policy import build_voice_policy_response
from velox.models.media import AudioTranscriptionResult


def test_voice_policy_returns_none_for_high_confidence_transcript() -> None:
    response = build_voice_policy_response(
        language="en",
        transcription=AudioTranscriptionResult(
            text="I need airport transfer tomorrow morning.",
            language="en",
            confidence=0.91,
        ),
    )

    assert response is None


def test_voice_policy_returns_written_fallback_for_low_confidence() -> None:
    response = build_voice_policy_response(
        language="tr",
        transcription=AudioTranscriptionResult(
            text="yarin havaalani",
            language="tr",
            confidence=0.31,
        ),
    )

    assert response is not None
    assert response.internal_json.state == "NEEDS_VERIFICATION"
    assert "VOICE_LOW_CONFIDENCE" in response.internal_json.risk_flags
    assert "yazili" in response.user_message.lower() or "mesaj" in response.user_message.lower()


def test_voice_policy_returns_failure_message_when_transcription_unavailable() -> None:
    response = build_voice_policy_response(
        language="en",
        transcription=None,
        failure_reason="TRANSCRIPTION_ERROR",
    )

    assert response is not None
    assert response.internal_json.next_step == "ask_written_followup"
    assert "written" in response.user_message.lower() or "message" in response.user_message.lower()
