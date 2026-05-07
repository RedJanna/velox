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
    """Return safe self-service fallback when menu catalogue is not configured."""
    lang = (language or "tr").lower()
    if lang == "en":
        return (
            "I can help with menu information within this chat. I do not have a verified "
            "menu match for that item right now. You can review the available menu options "
            "from the ordering screen and continue your order there."
        )
    if lang == "ru":
        return (
            "Я могу помочь с информацией о меню в этом чате. Сейчас у меня нет "
            "подтвержденного совпадения по этому блюду. Вы можете посмотреть доступные "
            "позиции на экране заказа и продолжить заказ там."
        )
    return (
        "Menu konusunda size bu akis icinde yardimci olabilirim. Bu urun icin su an "
        "dogrulanmis bir menu eslesmesi bulamadim. Siparis ekranindan mevcut menu "
        "seceneklerini inceleyip siparise devam edebilirsiniz."
    )


def hotel_fact_conflict_fallback(language: str, board_summary: str = "") -> str:
    """Return safe fallback when a guest claim conflicts with hotel profile facts."""
    lang = (language or "tr").lower()
    board = board_summary.strip()
    if lang == "en":
        concept = f" Our current accommodation concept is {board}." if board else ""
        return (
            f"I cannot confirm that information from our current hotel details.{concept} "
            "I am forwarding this to our team so they can check the advertisement or package details "
            "and contact you as soon as possible."
        )
    if lang == "ru":
        concept = f" Текущая концепция проживания: {board}." if board else ""
        return (
            f"Я не могу подтвердить эту информацию по актуальным данным отеля.{concept} "
            "Я передаю запрос нашей команде, чтобы они проверили детали акции или пакета "
            "и связались с вами как можно скорее."
        )
    concept = f" Guncel konaklama konseptimiz {board}." if board else ""
    return (
        f"Bu bilgiyi guncel otel bilgilerimizden dogrulayamiyorum.{concept} "
        "Reklam veya paket detayini ekibimize iletiyorum; en kisa surede size net donus yapacaklar."
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
