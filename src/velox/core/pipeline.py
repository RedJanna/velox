"""Core pipeline post-processing helpers."""

from typing import Any

import asyncpg

from velox.escalation.engine import EscalationEngine
from velox.escalation.risk_detector import detect_all_risk_flags
from velox.models.conversation import Conversation, LLMResponse
from velox.models.escalation import EscalationResult


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
