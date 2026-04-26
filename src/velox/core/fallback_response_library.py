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


def unresolved_handoff_fallback(language: str) -> str:
    """Return safe handoff text when the assistant cannot resolve reliably."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I cannot complete your request reliably right now. "
            "I am forwarding it to our team and they will contact you as soon as possible."
        )
    if lang == "ru":
        return (
            "Сейчас я не могу надежно завершить ваш запрос. "
            "Я передаю его нашей команде, и они свяжутся с вами как можно скорее."
        )
    return (
        "Talebinizi su an guvenilir sekilde tamamlayamiyorum. "
        "Konuyu ekibimize iletiyorum; en kisa surede sizinle iletisime gececekler."
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


def menu_not_available_fallback(language: str) -> str:
    """Return safe fallback when menu catalogue is not configured."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I'd love to help with menu options! Our current menu details are best "
            "confirmed directly with our restaurant team. I am forwarding your request "
            "to them now."
        )
    if lang == "ru":
        return (
            "С удовольствием помогу с меню! Актуальные блюда лучше уточнить "
            "непосредственно у команды нашего ресторана. Я передаю ваш запрос "
            "нашей команде."
        )
    return (
        "Menu konusunda size yardimci olmak isterim! Guncel menumuz hakkinda "
        "en dogru bilgiyi restoranımız veya resepsiyon ekibimizden alabilirsiniz. "
        "Talebinizi simdi ilgili ekibimize iletiyorum."
    )


def order_commitment_fallback(language: str) -> str:
    """Return safe fallback when an order commitment is made without tool backing."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I'm forwarding your request to our team right away. "
            "They will take care of it and get back to you as soon as possible."
        )
    if lang == "ru":
        return (
            "Я передаю ваш запрос нашей команде. "
            "Они позаботятся об этом и свяжутся с вами в ближайшее время."
        )
    return (
        "Talebinizi hemen ilgili ekibimize iletiyorum. "
        "En kisa surede sizinle ilgileneceklerdir."
    )
