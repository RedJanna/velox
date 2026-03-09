"""Unit tests for multilingual language detection heuristics."""

from velox.api.routes import whatsapp_webhook


def test_detect_message_language_for_english_sentence() -> None:
    """Language detector should classify English reservation text as EN."""
    detected = whatsapp_webhook._detect_message_language(
        "I need airport transfer + dinner reservation + late checkout in one package.",
        fallback="tr",
    )
    assert detected == "en"


def test_detect_message_language_for_russian_sentence() -> None:
    """Language detector should classify Cyrillic reservation text as RU."""
    detected = whatsapp_webhook._detect_message_language(
        "В вашем отеле есть лифт?",
        fallback="tr",
    )
    assert detected == "ru"


def test_detect_message_language_for_german_sentence() -> None:
    """Language detector should classify German reservation text as DE."""
    detected = whatsapp_webhook._detect_message_language(
        "Hallo, ich brauche einen Flughafentransfer und Frühstück.",
        fallback="tr",
    )
    assert detected == "de"


def test_detect_message_language_for_arabic_sentence() -> None:
    """Language detector should classify Arabic reservation text as AR."""
    detected = whatsapp_webhook._detect_message_language(
        "مرحبا، أحتاج حجز غرفة مع نقل من المطار.",
        fallback="tr",
    )
    assert detected == "ar"
