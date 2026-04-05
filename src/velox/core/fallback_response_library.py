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


def menu_not_available_fallback(language: str) -> str:
    """Return safe fallback when menu catalogue is not configured."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I'd love to help with menu options! Our current menu details are best "
            "confirmed directly with our restaurant team. Would you like me to forward "
            "your request to them, or would you prefer to contact them directly?"
        )
    if lang == "ru":
        return (
            "С удовольствием помогу с меню! Актуальные блюда лучше уточнить "
            "непосредственно у команды нашего ресторана. Хотите, чтобы я передал "
            "ваш запрос, или предпочитаете связаться с ними напрямую?"
        )
    return (
        "Menu konusunda size yardimci olmak isterim! Guncel menumuz hakkinda "
        "en dogru bilgiyi restoranımız veya resepsiyon ekibimizden alabilirsiniz. "
        "Dilerseniz talebinizi onlara hemen iletebilirim."
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
