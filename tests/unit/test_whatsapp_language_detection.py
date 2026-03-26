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


def test_detect_message_language_ignores_link_only_message() -> None:
    """Link-only payloads should not force a language switch."""
    detected = whatsapp_webhook._detect_message_language(
        "https://kassandra-butik-otel.rezervasyonal.com/?Checkin=2026-09-01&Checkout=2026-09-05&Adult=2&child=0&language=tr",
        fallback="tr",
        sticky_mode=True,
    )
    assert detected == "tr"


def test_detect_message_language_sticky_mode_blocks_weak_switch() -> None:
    """Sticky mode should keep current language on weak single-token signals."""
    detected = whatsapp_webhook._detect_message_language(
        "hello",
        fallback="tr",
        sticky_mode=True,
    )
    assert detected == "tr"


def test_detect_message_language_sticky_mode_allows_clear_switch() -> None:
    """Sticky mode should switch language when message carries strong evidence."""
    detected = whatsapp_webhook._detect_message_language(
        "Hello, I need room prices for 3 nights.",
        fallback="tr",
        sticky_mode=True,
    )
    assert detected == "en"


def test_detect_message_language_keeps_turkish_when_link_has_turkish_context() -> None:
    """Link plus Turkish natural-language context should remain Turkish."""
    detected = whatsapp_webhook._detect_message_language(
        "https://kassandra-butik-otel.rezervasyonal.com/?Checkin=2026-09-01&Checkout=2026-09-05 Bu fiyatlar doğru mu?",
        fallback="tr",
        sticky_mode=True,
    )
    assert detected == "tr"
