"""Central fallback and refusal messages for guest-facing safety paths."""

from __future__ import annotations


def response_validation_fallback(language: str) -> str:
    """Return safe fallback reply used when response validation fails."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I want to help you accurately. Could you share your request in one short message "
            "about your stay or hotel services?"
        )
    if lang == "ru":
        return (
            "Я хочу помочь вам максимально точно. Пожалуйста, напишите ваш запрос "
            "одним коротким сообщением о проживании или услугах отеля."
        )
    return (
        "Size en dogru sekilde yardimci olmak istiyorum. "
        "Talebinizi konaklama veya otel hizmetleriyle ilgili tek kisa mesajla paylasir misiniz?"
    )


def out_of_scope_refusal(language: str) -> str:
    """Return consistent, polite refusal for out-of-scope requests."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I cannot support that topic directly, but I can gladly help with your stay, "
            "reservation, room, or hotel services."
        )
    if lang == "ru":
        return (
            "Я не могу напрямую помочь по этой теме, но с удовольствием помогу с вашим проживанием, "
            "бронированием, номером или услугами отеля."
        )
    return (
        "Bu konuda dogrudan destek saglayamiyorum; ancak konaklamaniz, rezervasyonunuz, "
        "odaniz veya otel hizmetlerimizle ilgili memnuniyetle yardimci olabilirim."
    )
