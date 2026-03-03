"""Unit tests for local intent detection helpers."""

from velox.config.constants import Intent
from velox.core.intent_engine import detect_intent


def test_turkish_reservation_detected_as_stay_availability() -> None:
    """Turkish reservation text should map to stay availability intent."""
    message = "Merhaba, 15-18 Temmuz icin oda musaitligi ogrenmek istiyorum."
    assert detect_intent(message) == Intent.STAY_AVAILABILITY


def test_english_faq_detected_as_faq_info() -> None:
    """English FAQ text should map to FAQ intent."""
    message = "What time is breakfast and do you have wifi?"
    assert detect_intent(message) == Intent.FAQ_INFO


def test_transfer_query_detected_as_transfer_info() -> None:
    """Airport transfer question should map to transfer intent."""
    message = "Dalaman airport transfer for 4 people please."
    assert detect_intent(message) == Intent.TRANSFER_INFO


def test_complaint_detected_as_complaint() -> None:
    """Complaint language should map to complaint intent."""
    message = "Bu deneyim berbat, sikayet etmek istiyorum."
    assert detect_intent(message) == Intent.COMPLAINT


def test_handoff_request_detected_as_human_handoff() -> None:
    """Direct request for human support should map to handoff intent."""
    message = "Beni insan yetkiliye baglar misiniz?"
    assert detect_intent(message) == Intent.HUMAN_HANDOFF
