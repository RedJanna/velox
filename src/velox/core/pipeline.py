"""Core pipeline post-processing helpers."""

import re
from typing import Any

import asyncpg

from velox.config.constants import RiskFlag
from velox.escalation.engine import EscalationEngine
from velox.escalation.risk_detector import detect_all_risk_flags
from velox.models.conversation import Conversation, LLMResponse
from velox.models.escalation import EscalationResult

_SUPPORTED_SPECIAL_OCCASION_PATTERN = re.compile(
    r"\b(d[oö][gğ]um\s*g[uü]n[uü]|birthday|balayı|honeymoon|y[ıi]ld[oö]n[uü]m[uü]|anniversary|"
    r"evlilik\s*teklifi|marriage\s*proposal|proposal)\b",
    re.IGNORECASE,
)

_DIRECT_HANDOFF_SPECIAL_OCCASION_PATTERN = re.compile(
    r"\b(ni[sş]an|engagement|mezuniyet|graduation|d[uü][gğ][uü]n|wedding|kurumsal|corporate|"
    r"business\s*dinner|i[sş]\s*yeme[gğ]i|terfi|promotion|team\s*organization|ekip\s*organizasyon|"
    r"[cç]ocuk\s*d[oö][gğ]um\s*g[uü]n[uü]|children'?s\s*birthday|group\s*celebration|grup\s*kutlama)\b",
    re.IGNORECASE,
)

_SPECIAL_OCCASION_PAYMENT_PATTERN = re.compile(
    r"\b(fiyat|ucret|ücret|price|cost|deposit|depozito|prepayment|[oö]n\s*[oö]deme|payment|"
    r"[oö]deme|iptal|cancellation)\b",
    re.IGNORECASE,
)

_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\d{4}-\d{2}-\d{2}|bug[uü]n|yar[ıi]n|tomorrow|today)\b",
    re.IGNORECASE,
)

_RESERVATION_PATTERN = re.compile(
    r"\b(rezervasyon\s*(no|numara|kod)|reservation\s*(number|no|code)|voucher|booking\s*(id|number)|"
    r"\b[A-Z]{1,4}[-_]?\d{3,}\b|\b\d{5,}\b)",
    re.IGNORECASE,
)

_PARTY_SIZE_PATTERN = re.compile(r"\b(\d+)\s*(ki[sş]i|person|people|pax)\b", re.IGNORECASE)

_ALLERGY_PATTERN = re.compile(
    r"\b(alerji|allergy|allergic|gl[uü]ten|lakto|lactose|f[ıi]st[ıi]k|peanut|vegan|vegetarian|"
    r"yok|none|hay[ıi]r)\b",
    re.IGNORECASE,
)


async def post_process_escalation(
    user_message_text: str,
    llm_response: LLMResponse,
    conversation: Conversation,
    escalation_engine: EscalationEngine,
    tools: dict[str, Any],
    db_pool: asyncpg.Pool,
) -> EscalationResult:
    """Run escalation checks and actions after each LLM response."""
    risk_flags = detect_all_risk_flags(
        user_message=user_message_text,
        internal_json=llm_response.internal_json,
    )
    risk_flags = _filter_special_occasion_intake_flags(
        user_message_text=user_message_text,
        llm_response=llm_response,
        risk_flags=risk_flags,
    )
    if not risk_flags:
        return EscalationResult()

    reference_id = str(
        conversation.entities_json.get("hold_id")
        or conversation.entities_json.get("reservation_id")
        or conversation.phone_hash
    )

    result = escalation_engine.evaluate(
        risk_flags=[flag.value for flag in risk_flags],
        intent=llm_response.internal_json.intent,
        reference_id=reference_id,
        conversation_id=str(conversation.id),
    )

    if result.actions:
        transcript_summary = _build_transcript_summary(conversation.messages[-5:])
        await escalation_engine.execute_actions(
            result=result,
            conversation_id=str(conversation.id),
            hotel_id=conversation.hotel_id,
            phone_hash=conversation.phone_hash,
            transcript_summary=transcript_summary,
            tools=tools,
            db_pool=db_pool,
        )

    await _update_conversation_risk_flags(
        conversation_id=str(conversation.id),
        risk_flags=[flag.value for flag in risk_flags],
        db_pool=db_pool,
    )
    return result


def _filter_special_occasion_intake_flags(
    user_message_text: str,
    llm_response: LLMResponse,
    risk_flags: list[RiskFlag],
) -> list[RiskFlag]:
    """Avoid terminal handoff while supported special-occasion intake is incomplete."""
    if RiskFlag.SPECIAL_EVENT not in risk_flags:
        return risk_flags

    if _DIRECT_HANDOFF_SPECIAL_OCCASION_PATTERN.search(user_message_text):
        return risk_flags

    if _SPECIAL_OCCASION_PAYMENT_PATTERN.search(user_message_text):
        return risk_flags

    if not _SUPPORTED_SPECIAL_OCCASION_PATTERN.search(user_message_text):
        return risk_flags

    if _has_minimum_special_occasion_intake(user_message_text, llm_response):
        return risk_flags

    return [flag for flag in risk_flags if flag != RiskFlag.SPECIAL_EVENT]


def _has_minimum_special_occasion_intake(user_message_text: str, llm_response: LLMResponse) -> bool:
    """Return True when supported special-occasion details are ready for approval handoff."""
    entities = llm_response.internal_json.entities or {}
    text = user_message_text.strip()

    has_reservation = any(
        _has_value(entities.get(key))
        for key in (
            "reservation_number",
            "reservation_id",
            "voucher_no",
            "booking_number",
            "restaurant_reservation_number",
            "accommodation_reservation_number",
        )
    ) or bool(_RESERVATION_PATTERN.search(text))
    has_date = any(
        _has_value(entities.get(key))
        for key in ("special_occasion_date", "date", "reservation_date", "occasion_date")
    ) or bool(_DATE_PATTERN.search(text))
    has_party_size = any(
        _has_value(entities.get(key))
        for key in ("number_of_people", "party_size", "pax", "adults")
    ) or bool(_PARTY_SIZE_PATTERN.search(text))
    has_request_details = any(
        _has_value(entities.get(key))
        for key in ("request_details", "notes", "special_request", "additional_requests")
    )
    has_surprise_info = any(
        _has_value(entities.get(key))
        for key in ("is_surprise", "surprise", "surprise_info")
    ) or "sürpriz" in text.lower() or "surprise" in text.lower()
    has_allergy_info = any(
        _has_value(entities.get(key))
        for key in ("allergy_or_food_sensitivity", "allergy", "food_sensitivity")
    ) or bool(_ALLERGY_PATTERN.search(text))

    return all(
        (
            has_reservation,
            has_date,
            has_party_size,
            has_request_details,
            has_surprise_info,
            has_allergy_info,
        )
    )


def _has_value(value: Any) -> bool:
    """Return whether an extracted entity carries a meaningful value."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (bool, int, float)):
        return True
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _build_transcript_summary(messages: list[Any]) -> str:
    """Create compact transcript summary for ticket context."""
    lines: list[str] = []
    for message in messages:
        role = str(getattr(message, "role", "unknown")).upper()
        content = str(getattr(message, "content", ""))[:200]
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)


async def _update_conversation_risk_flags(
    conversation_id: str,
    risk_flags: list[str],
    db_pool: asyncpg.Pool,
) -> None:
    """Merge detected risk flags into conversation.risk_flags without duplicates."""
    deduped_query = """
        UPDATE conversations
        SET risk_flags = (
            SELECT array_agg(DISTINCT flag)
            FROM unnest(array_cat(risk_flags, $2::text[])) AS flag
        ),
        updated_at = now()
        WHERE id = $1
    """
    async with db_pool.acquire() as conn:
        await conn.execute(deduped_query, conversation_id, risk_flags)
