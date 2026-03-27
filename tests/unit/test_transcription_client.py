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
