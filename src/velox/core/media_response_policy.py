"""Deterministic guest-facing response policy for analyzed inbound images."""

from __future__ import annotations

from typing import Any

from velox.models.conversation import InternalJSON, LLMResponse
from velox.models.media import VisionAnalysisResult

_PRICE_CHECK_HINTS = (
    "fiyat",
    "fiyatlar",
    "price",
    "prices",
    "rate",
    "rates",
    "ucret",
    "tariff",
    "tarife",
    "dogru mu",
    "doğru mu",
    "correct",
    "accurate",
    "eur",
    "usd",
    "try",
)

_META_SUMMARY_MARKERS = (
    "the guest",
    "the user",
    "is inquiring",
    "is asking",
    "wants to know",
)


def build_media_policy_response(
    *,
    language: str,
    analysis: VisionAnalysisResult | None,
    failure_reason: str | None = None,
    user_text: str = "",
) -> LLMResponse:
    """Create a safe response for media turns with deterministic routing."""
    normalized_language = (language or "tr").lower()

    if failure_reason:
        return LLMResponse(
            user_message=_failure_message(normalized_language, failure_reason),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="human_handoff",
                state="HANDOFF",
                handoff={"needed": True, "reason": "media_analysis_failed"},
                risk_flags=["TOOL_UNAVAILABLE"],
                next_step="handoff_to_ops",
            ),
        )

    if analysis is None:
        return LLMResponse(
            user_message=_fallback_message(normalized_language),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="human_handoff",
                state="HANDOFF",
                handoff={"needed": True, "reason": "media_analysis_missing"},
                risk_flags=["TOOL_UNAVAILABLE"],
                next_step="handoff_to_ops",
            ),
        )

    if analysis.intent == "payment_proof_photo":
        return LLMResponse(
            user_message=_payment_proof_message(normalized_language),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="payment_inquiry",
                state="HANDOFF",
                entities=_analysis_entities(analysis),
                handoff={"needed": True, "reason": "payment_proof_review"},
                risk_flags=list(dict.fromkeys(["PAYMENT_CONFUSION", *analysis.risk_flags])),
                next_step="handoff_to_sales",
            ),
        )

    if analysis.intent == "room_issue_photo":
        return LLMResponse(
            user_message=_room_issue_message(normalized_language, analysis.summary),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="complaint",
                state="HANDOFF",
                entities=_analysis_entities(analysis),
                handoff={"needed": True, "reason": "room_issue_photo"},
                risk_flags=list(dict.fromkeys(["ANGRY_COMPLAINT", *analysis.risk_flags])),
                next_step="handoff_to_ops",
            ),
        )

    if analysis.confidence < 0.60:
        return LLMResponse(
            user_message=_low_confidence_message(normalized_language),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="faq_info",
                state="NEEDS_VERIFICATION",
                entities=_analysis_entities(analysis),
                required_questions=["image_context"],
                handoff={"needed": False},
                risk_flags=list(dict.fromkeys(analysis.risk_flags)),
                next_step="ask_clarifying_question",
            ),
        )

    if _is_price_check_request(analysis, user_text):
        return LLMResponse(
            user_message=_price_check_message(normalized_language),
            internal_json=InternalJSON(
                language=normalized_language,
                intent="stay_quote",
                state="NEEDS_VERIFICATION",
                entities=_analysis_entities(analysis),
                required_questions=["checkin_date", "checkout_date", "adults"],
                handoff={"needed": False},
                risk_flags=list(dict.fromkeys(analysis.risk_flags)),
                next_step="ask_clarifying_question",
            ),
        )

    return LLMResponse(
        user_message=_general_media_message(normalized_language, analysis.summary),
        internal_json=InternalJSON(
            language=normalized_language,
            intent="faq_info",
            state="INTENT_DETECTED",
            entities=_analysis_entities(analysis),
            handoff={"needed": bool(analysis.requires_handoff)},
            risk_flags=list(dict.fromkeys(analysis.risk_flags)),
            next_step="await_user_input",
        ),
    )


def _analysis_entities(analysis: VisionAnalysisResult) -> dict[str, Any]:
    return {
        "media_analysis": {
            "intent": analysis.intent,
            "confidence": analysis.confidence,
            "summary": analysis.summary,
            "detected_text": analysis.detected_text,
        }
    }


def _failure_message(language: str, _reason: str) -> str:
    if language == "en":
        return "I received your image, but I could not process it right now. I am forwarding it to our team."
    if language == "ru":
        return (
            "Я получил(а) ваше изображение, но сейчас не могу его обработать. "
            "Передаю запрос нашей команде для ручной проверки."
        )
    return (
        "Gorselinizi aldim ancak su anda otomatik olarak isleyemedim. "
        "Talebinizi ekibimize manuel inceleme icin iletiyorum."
    )


def _fallback_message(language: str) -> str:
    if language == "en":
        return "I received your image. I am forwarding it to our team for review."
    if language == "ru":
        return "Я получил(а) ваше изображение. Передаю его нашей команде на проверку."
    return "Gorselinizi aldim. Inceleme icin ilgili ekibe iletiyorum."


def _payment_proof_message(language: str) -> str:
    if language == "en":
        return (
            "Thank you, I received your payment proof image. "
            "I am forwarding it to our payment team and they will contact you shortly."
        )
    if language == "ru":
        return (
            "Спасибо, я получил(а) изображение подтверждения оплаты. "
            "Передаю его платежной команде, с вами свяжутся в ближайшее время."
        )
    return (
        "Tesekkur ederim, odeme belgesi gorselinizi aldim. "
        "Odeme ekibimize iletiyorum, en kisa surede sizinle iletisime gececekler."
    )


def _room_issue_message(language: str, summary: str) -> str:
    summary_text = summary.strip()
    if language == "en":
        base = "I received your room-related image and forwarded it to our operations team."
        if summary_text:
            return f"{base} I can see: {summary_text}. They will assist you shortly."
        return f"{base} They will assist you shortly."
    if language == "ru":
        base = "Я получил(а) ваше фото по номеру и передал(а) его операционной команде."
        if summary_text:
            return f"{base} Похоже на: {summary_text}. С вами свяжутся в ближайшее время."
        return f"{base} С вами свяжутся в ближайшее время."
    base = "Oda ile ilgili gorselinizi aldim ve operasyon ekibimize ilettim."
    if summary_text:
        return f"{base} Gordugum durum: {summary_text}. Ekibimiz en kisa surede yardimci olacak."
    return f"{base} Ekibimiz en kisa surede yardimci olacak."


def _low_confidence_message(language: str) -> str:
    if language == "en":
        return (
            "I received your image but I need one short clarification to help correctly. "
            "Could you briefly describe what you want us to check in the image?"
        )
    if language == "ru":
        return (
            "Я получил(а) изображение, но для точной помощи нужен короткий комментарий. "
            "Пожалуйста, укажите, что именно нужно проверить на фото."
        )
    return (
        "Gorselinizi aldim, dogru yardimci olabilmem icin kisa bir netlestirme rica edecegim. "
        "Fotografta hangi konuyu kontrol etmemizi istiyorsunuz?"
    )


def _price_check_message(language: str) -> str:
    if language == "en":
        return (
            "I reviewed your screenshot. I cannot confirm prices only from the image, "
            "but I can verify the live rate for you now. "
            "Please share check-in/check-out dates and number of guests."
        )
    if language == "ru":
        return (
            "Я просмотрел(а) скриншот. Точную цену по изображению подтвердить нельзя, "
            "но я могу сразу проверить актуальный тариф. "
            "Пожалуйста, укажите даты заезда/выезда и количество гостей."
        )
    return (
        "Gorseli inceledim. Fiyati sadece ekran goruntusunden kesin onaylayamam, "
        "ancak sizin icin canli fiyati hemen kontrol edebilirim. "
        "Lutfen giris-cikis tarihini ve kisi sayisini paylasin."
    )


def _is_price_check_request(analysis: VisionAnalysisResult, user_text: str) -> bool:
    haystack = " ".join(
        [
            str(user_text or ""),
            str(analysis.summary or ""),
            str(analysis.detected_text or ""),
        ]
    ).lower()
    return any(hint in haystack for hint in _PRICE_CHECK_HINTS)


def _sanitize_summary(summary: str) -> str:
    text = summary.strip()
    lowered = text.lower()
    if any(marker in lowered for marker in _META_SUMMARY_MARKERS):
        return ""
    return text


def _general_media_message(language: str, summary: str) -> str:
    summary_text = _sanitize_summary(summary)
    if language == "en":
        if summary_text:
            return (
                f"I received your image. It seems related to: {summary_text}. "
                "If this matches your request, I can continue from here."
            )
        return "I received your image. Please share one short note about what you want me to help with."
    if language == "ru":
        if summary_text:
            return (
                f"Я получил(а) изображение. Похоже, что это связано с: {summary_text}. "
                "Если верно, я продолжу отсюда."
            )
        return "Я получил(а) изображение. Напишите, пожалуйста, коротко, с чем вам помочь."
    if summary_text:
        return (
            f"Gorselinizi aldim ve inceledim. Gordugum konu: {summary_text}. "
            "Bu gorselle ilgili nasil yardim etmemi istersiniz?"
        )
    return "Gorselinizi aldim ve inceledim. Bu gorselle ilgili hangi konuda yardim istersiniz?"
