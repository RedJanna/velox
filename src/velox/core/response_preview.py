"""Stateless single-question response preview flow for the admin panel."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast

import orjson
import structlog
from pydantic import BaseModel, Field

from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.core.hotel_information_responses import try_build_structured_hotel_information_response
from velox.core.response_validator import validate_guest_response
from velox.core.stay_quote_availability_guard import (
    backfill_availability_for_quote,
    build_guarded_stay_quote,
    executed_booking_tool_names,
)
from velox.llm.client import LLMClient, LLMUnavailableError, get_llm_client
from velox.llm.function_registry import get_tool_definitions
from velox.llm.prompt_builder import PromptBuilder, get_prompt_builder
from velox.llm.response_parser import ResponseParser
from velox.models.conversation import InternalJSON, LLMResponse
from velox.tools.base import ToolDispatcher

logger = structlog.get_logger(__name__)

MAX_PREVIEW_QUESTION_CHARS = 4000
PREVIEW_TOOL_LOOP_ITERATIONS = 4
PREVIEW_PERMISSION = "conversations:read"
PREVIEW_RESPONSE_STYLES = frozenset({"professional", "warm", "concise"})
READ_ONLY_PREVIEW_TOOLS = frozenset(
    {
        "booking_availability",
        "booking_quote",
        "restaurant_availability",
        "transfer_get_info",
        "faq_lookup",
        "hotel_info_lookup",
    }
)
_REDACTED_ARGUMENT_KEYS = {
    "phone",
    "contact_phone",
    "email",
    "guest_name",
    "name",
    "full_name",
}
_SIDE_EFFECT_COMMITMENT_PATTERN = re.compile(
    r"("
    r"rezervasyon(?:unuzu| talebinizi)?\s*(olu[sş]tur|tamamla|onaya\s*ilet|i[sş]leme\s*al)|"
    r"talebinizi\s*(olu[sş]tur|ilettim|kayda\s*ald[ıi]m)|"
    r"bildirim\s*(g[oö]nderdim|ilettim)|"
    r"ticket\s*(a[çc]t[ıi]m|olu[sş]turdum)|"
    r"creating\s*your\s*reservation|created\s*your\s*reservation|"
    r"sent\s*(a\s*)?notification|created\s*(a\s*)?(ticket|request)"
    r")",
    re.IGNORECASE,
)

_PREVIEW_MODE_PROMPT = """
RESPONSE_PREVIEW_MODE (STRICT)
- This is an isolated admin response preview, not Chat Lab and not a live WhatsApp conversation.
- Treat the next user message as the only guest question.
- Do not use, infer, summarize, or request previous messages, customer history, session memory, or chat context.
- Use only HOTEL_CONTEXT and executed read-only tool results for hotel facts.
- Read-only tools may be used for hotel information, FAQ, transfer information,
  room availability/quote, and restaurant availability.
- For stay price or room availability, booking_quote alone is not enough:
  use booking_availability as the sellable-room authority and remove any quote offer
  whose room type is not sellable for every requested stay night.
- Never create, claim, or imply a reservation, hold, payment request, ticket,
  CRM log, notification, handoff task, or message record.
- If the guest request would require an operational action or human follow-up,
  explain that the hotel team must confirm it; mark handoff in INTERNAL_JSON only.
- Do not ask for card numbers, CVV, OTP, bank passwords, or unnecessary PII.
- Keep the guest-facing answer professional, natural, clear, and WhatsApp-friendly.
- Detect the reply language from the single question unless the admin explicitly requested another language.
- When the reply language is English, use British English spelling, phrasing, and hospitality tone.
""".strip()

_PREVIEW_STYLE_GUIDANCE = {
    "professional": "Use a polished, professional hotel-reception tone with clear customer-facing wording.",
    "warm": "Use a warmer hospitality tone while staying concise, accurate, and professional.",
    "concise": "Use the shortest clear answer that still covers the customer's question and required caveats.",
}

_PREVIEW_OUTPUT_CONTRACT = """
Your response must contain exactly two parts.
Part 1 must start with USER_MESSAGE: followed by one guest-facing reply.
Part 2 must be a new line with the literal header INTERNAL_JSON: followed by exactly one valid JSON object.

INTERNAL_JSON rules:
- keys required: language, intent, state, entities, required_questions,
  tool_calls, notifications, handoff, risk_flags, escalation, next_step
- entities must be an object
- required_questions, tool_calls, notifications, risk_flags must be arrays
- handoff and escalation must be objects
- set entities.response_preview.mode to "stateless_single_question"
- set entities.response_preview.history_used to false
- set entities.response_preview.history_created to false
- do not wrap JSON in markdown or code fences
- do not add commentary after the JSON object
""".strip()

_PREVIEW_TRANSLATION_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "velox_response_preview_translation",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "source_language": {"type": "string"},
                "target_language": {"type": "string"},
                "translated_reply": {"type": "string"},
            },
            "required": ["source_language", "target_language", "translated_reply"],
        },
    },
}


class ResponsePreviewToolCall(BaseModel):
    """Tool-call metadata safe to expose in the admin preview UI."""

    name: str
    status: str
    blocked: bool = False
    reason: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)


class ResponsePreviewTranslation(BaseModel):
    """Admin-only translation metadata for non-Turkish preview replies."""

    available: bool = False
    source_language: str = "auto"
    target_language: str = "tr"
    translated_reply: str = ""
    model: str | None = None


class ResponsePreviewResult(BaseModel):
    """Result object returned by the stateless response preview service."""

    hotel_id: int
    question_chars: int
    reply: str
    internal_json: InternalJSON
    model: str
    duration_ms: int
    requested_language: str = "auto"
    response_style: str = "professional"
    history_used: bool = False
    history_created: bool = False
    persisted: bool = False
    created_records: list[str] = Field(default_factory=list)
    tool_calls: list[ResponsePreviewToolCall] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    translation: ResponsePreviewTranslation = Field(default_factory=ResponsePreviewTranslation)


class PreviewToolExecutor:
    """Execute only read-only tools and record safe metadata for the preview."""

    def __init__(self, *, dispatcher: ToolDispatcher | None, hotel_id: int) -> None:
        self.dispatcher = dispatcher
        self.hotel_id = hotel_id
        self.tool_calls: list[ResponsePreviewToolCall] = []

    async def __call__(self, tool_name: str, tool_args: Any) -> str:
        """Run one preview-safe tool call and return a JSON string for the LLM."""
        normalized_name = str(tool_name or "").strip()
        normalized_args = _normalize_tool_args(tool_args)
        normalized_args["hotel_id"] = self.hotel_id

        if normalized_name not in READ_ONLY_PREVIEW_TOOLS:
            return self._block_tool(
                normalized_name,
                normalized_args,
                "side_effects_not_allowed_in_response_preview",
            )
        if self.dispatcher is None:
            return self._block_tool(normalized_name, normalized_args, "tool_dispatcher_unavailable")

        result = await self.dispatcher.dispatch(normalized_name, **normalized_args)
        status = "error" if isinstance(result, dict) and result.get("error") else "ok"
        self.tool_calls.append(
            ResponsePreviewToolCall(
                name=normalized_name,
                status=status,
                arguments=_redact_tool_args(normalized_args),
            )
        )
        return _to_json_string(result)

    def _block_tool(self, tool_name: str, tool_args: dict[str, Any], reason: str) -> str:
        """Record and return a deterministic blocked-tool result."""
        safe_name = tool_name or "unknown"
        self.tool_calls.append(
            ResponsePreviewToolCall(
                name=safe_name,
                status="blocked",
                blocked=True,
                reason=reason,
                arguments=_redact_tool_args(tool_args),
            )
        )
        return _to_json_string(
            {
                "error": "PREVIEW_TOOL_BLOCKED",
                "tool": safe_name,
                "reason": reason,
                "side_effects_allowed": False,
            }
        )


def build_response_preview_messages(
    *,
    hotel_id: int,
    question: str,
    language: str = "auto",
    response_style: str = "professional",
    prompt_builder: PromptBuilder | None = None,
    current_date: str | None = None,
) -> list[dict[str, Any]]:
    """Build a stateless OpenAI message list for one independent question."""
    builder = prompt_builder or get_prompt_builder()
    cleaned_question = _clean_question(question)
    date_value = current_date or datetime.now(UTC).date().isoformat()
    requested_language = _normalize_language(language)
    selected_style = _normalize_response_style(response_style)
    return [
        {"role": "system", "content": builder.build_system_prompt(hotel_id)},
        {
            "role": "system",
            "content": (
                f"{_PREVIEW_MODE_PROMPT}\n\n"
                f"CURRENT_DATE: {date_value}\n"
                f"RESPONSE_LANGUAGE_REQUEST: {requested_language}\n"
                f"RESPONSE_STYLE_REQUEST: {selected_style}\n"
                f"RESPONSE_STYLE_GUIDANCE: {_PREVIEW_STYLE_GUIDANCE[selected_style]}"
            ),
        },
        {"role": "user", "content": cleaned_question},
        {"role": "system", "content": _PREVIEW_OUTPUT_CONTRACT},
    ]


async def generate_response_preview(
    *,
    hotel_id: int,
    question: str,
    language: str = "auto",
    response_style: str = "professional",
    dispatcher: ToolDispatcher | None = None,
    llm_client: LLMClient | None = None,
    prompt_builder: PromptBuilder | None = None,
) -> ResponsePreviewResult:
    """Generate a customer-facing reply without reading or writing message history."""
    started = perf_counter()
    cleaned_question = _clean_question(question)
    requested_language = _normalize_language(language)
    selected_style = _normalize_response_style(response_style)
    selected_llm = llm_client or get_llm_client()
    preview_executor = PreviewToolExecutor(dispatcher=dispatcher, hotel_id=hotel_id)
    structured_response, _structured_calls = await try_build_structured_hotel_information_response(
        hotel_id=hotel_id,
        query=cleaned_question,
        language=_default_language(requested_language),
        tool_runner=preview_executor,
    )
    if structured_response is not None:
        parsed = _normalize_preview_internal_json(structured_response, preview_executor.tool_calls)
        parsed = validate_guest_response(
            parsed,
            default_language=_default_language(requested_language),
            hotel_id=hotel_id,
        )
        parsed.user_message = WhatsAppFormatter.truncate(parsed.user_message)
        parsed = _normalize_preview_internal_json(parsed, preview_executor.tool_calls)
        response_language = _response_language(parsed, requested_language)
        translation = await _build_admin_translation(
            llm_client=selected_llm,
            reply=parsed.user_message,
            source_language=response_language,
            hotel_id=hotel_id,
        )
        parsed = _attach_translation_metadata(parsed, translation)
        duration_ms = int((perf_counter() - started) * 1000)
        logger.info(
            "admin_response_preview_generated",
            hotel_id=hotel_id,
            question_chars=len(cleaned_question),
            response_chars=len(parsed.user_message),
            tool_names=[item.name for item in preview_executor.tool_calls],
            duration_ms=duration_ms,
            model=selected_llm.primary_model,
            requested_language=requested_language,
            response_style=selected_style,
            translation_available=translation.available,
            translation_source_language=translation.source_language,
            translation_target_language=translation.target_language,
            history_used=False,
            history_created=False,
            deterministic_source="HOTEL_INFORMATION_JSON",
        )
        return ResponsePreviewResult(
            hotel_id=hotel_id,
            question_chars=len(cleaned_question),
            reply=parsed.user_message,
            internal_json=parsed.internal_json,
            model=selected_llm.primary_model,
            duration_ms=duration_ms,
            requested_language=requested_language,
            response_style=selected_style,
            tool_calls=preview_executor.tool_calls,
            safety_notes=[
                "single_question_only",
                "conversation_history_not_loaded",
                "message_history_not_created",
                "side_effect_tools_blocked",
                "structured_hotel_information_preflight",
                f"response_style_{selected_style}",
            ],
            translation=translation,
        )

    messages = build_response_preview_messages(
        hotel_id=hotel_id,
        question=cleaned_question,
        language=requested_language,
        response_style=selected_style,
        prompt_builder=prompt_builder,
    )
    tools = filter_preview_tool_definitions(get_tool_definitions())

    raw_content, executed_calls = await selected_llm.run_tool_call_loop(
        messages=messages,
        tools=tools,
        tool_executor=preview_executor,
        max_iterations=PREVIEW_TOOL_LOOP_ITERATIONS,
        trace_context={"flow": "admin_response_preview", "hotel_id": hotel_id},
    )
    parsed = await _parse_or_repair_preview_output(
        llm_client=selected_llm,
        raw_content=raw_content,
        executed_calls=executed_calls,
        language=requested_language,
    )
    if _requires_stay_quote_guard(parsed, executed_calls):
        await backfill_availability_for_quote(
            hotel_id=hotel_id,
            executed_calls=executed_calls,
            tool_executor=preview_executor,
        )
        parsed = _apply_guarded_stay_quote_preview(
            parsed,
            hotel_id=hotel_id,
            executed_calls=executed_calls,
            requested_language=requested_language,
        )
    parsed = _normalize_preview_internal_json(parsed, preview_executor.tool_calls)
    parsed = _enforce_no_preview_side_effect_claims(parsed)
    parsed = validate_guest_response(
        parsed,
        default_language=_default_language(requested_language),
        hotel_id=hotel_id,
    )
    parsed.user_message = WhatsAppFormatter.truncate(parsed.user_message)
    parsed = _normalize_preview_internal_json(parsed, preview_executor.tool_calls)
    response_language = _response_language(parsed, requested_language)
    translation = await _build_admin_translation(
        llm_client=selected_llm,
        reply=parsed.user_message,
        source_language=response_language,
        hotel_id=hotel_id,
    )
    parsed = _attach_translation_metadata(parsed, translation)

    duration_ms = int((perf_counter() - started) * 1000)
    logger.info(
        "admin_response_preview_generated",
        hotel_id=hotel_id,
        question_chars=len(cleaned_question),
        response_chars=len(parsed.user_message),
        tool_names=[item.name for item in preview_executor.tool_calls],
        duration_ms=duration_ms,
        model=selected_llm.primary_model,
        requested_language=requested_language,
        response_style=selected_style,
        translation_available=translation.available,
        translation_source_language=translation.source_language,
        translation_target_language=translation.target_language,
        history_used=False,
        history_created=False,
    )
    return ResponsePreviewResult(
        hotel_id=hotel_id,
        question_chars=len(cleaned_question),
        reply=parsed.user_message,
        internal_json=parsed.internal_json,
        model=selected_llm.primary_model,
        duration_ms=duration_ms,
        requested_language=requested_language,
        response_style=selected_style,
        tool_calls=preview_executor.tool_calls,
        safety_notes=[
            "single_question_only",
            "conversation_history_not_loaded",
            "message_history_not_created",
            "side_effect_tools_blocked",
            f"response_style_{selected_style}",
        ],
        translation=translation,
    )


def filter_preview_tool_definitions(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only read-only tool schemas allowed in response preview mode."""
    filtered: list[dict[str, Any]] = []
    for tool in tools:
        function_block = tool.get("function")
        if not isinstance(function_block, dict):
            continue
        if str(function_block.get("name") or "") in READ_ONLY_PREVIEW_TOOLS:
            filtered.append(tool)
    return filtered


async def _build_admin_translation(
    *,
    llm_client: LLMClient,
    reply: str,
    source_language: str,
    hotel_id: int,
) -> ResponsePreviewTranslation:
    """Translate non-Turkish preview replies for the admin overlay without history."""
    normalized_source = _normalize_language(source_language)
    if normalized_source in {"auto", "tr"} or not str(reply or "").strip():
        return ResponsePreviewTranslation(source_language=normalized_source, target_language="tr")

    messages = [
        {
            "role": "system",
            "content": (
                "You translate Velox admin response-preview replies. "
                "Use only the single reply text provided in this request; do not use previous messages, "
                "conversation history, customer profiles, session memory, tools, or external knowledge. "
                "Do not add, remove, soften, or strengthen hotel facts, dates, prices, "
                "policy caveats, or operational promises. "
                "Return JSON only. If translating into English, use British English spelling and phrasing."
            ),
        },
        {
            "role": "user",
            "content": _to_json_string(
                {
                    "source_language": normalized_source,
                    "target_language": "tr",
                    "reply": str(reply or "").strip(),
                }
            ),
        },
    ]
    try:
        response = await llm_client.chat_completion(
            messages=messages,
            response_format=_PREVIEW_TRANSLATION_FORMAT,
        )
    except LLMUnavailableError as exc:  # pragma: no cover - concrete client failures are integration-level.
        logger.warning(
            "admin_response_preview_translation_unavailable",
            hotel_id=hotel_id,
            source_language=normalized_source,
            target_language="tr",
            error_type=type(exc).__name__,
        )
        return ResponsePreviewTranslation(source_language=normalized_source, target_language="tr")

    content = _extract_chat_message_content(response).strip()
    try:
        payload = orjson.loads(content)
    except orjson.JSONDecodeError:
        logger.warning(
            "admin_response_preview_translation_invalid_json",
            hotel_id=hotel_id,
            source_language=normalized_source,
            target_language="tr",
            content_chars=len(content),
        )
        return ResponsePreviewTranslation(source_language=normalized_source, target_language="tr")
    if not isinstance(payload, dict):
        return ResponsePreviewTranslation(source_language=normalized_source, target_language="tr")

    translated_reply = str(payload.get("translated_reply") or "").strip()
    if not translated_reply:
        return ResponsePreviewTranslation(source_language=normalized_source, target_language="tr")
    payload_source = _normalize_language(str(payload.get("source_language") or normalized_source))
    return ResponsePreviewTranslation(
        available=True,
        source_language=payload_source if payload_source != "auto" else normalized_source,
        target_language="tr",
        translated_reply=WhatsAppFormatter.truncate(translated_reply),
        model=llm_client.primary_model,
    )


async def _parse_or_repair_preview_output(
    *,
    llm_client: LLMClient,
    raw_content: str,
    executed_calls: list[dict[str, Any]],
    language: str,
) -> LLMResponse:
    parsed = ResponseParser.parse(raw_content)
    parser_error = ResponseParser.extract_parser_error(parsed.internal_json)
    if not parser_error:
        return parsed

    repaired = await llm_client.repair_structured_output(
        raw_content=raw_content,
        language=_default_language(language),
        parser_error_reason=parser_error,
        executed_calls=executed_calls,
    )
    if not repaired:
        return parsed
    internal_json = repaired.get("internal_json")
    if not isinstance(internal_json, dict):
        return parsed
    return LLMResponse(
        user_message=str(repaired.get("user_message") or parsed.user_message),
        internal_json=ResponseParser.validate_internal_json(cast(dict[str, Any], internal_json)),
    )


def _normalize_preview_internal_json(
    response: LLMResponse,
    tool_calls: list[ResponsePreviewToolCall],
) -> LLMResponse:
    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    response.internal_json.entities = entities
    response.internal_json.tool_calls = [
        {
            "tool": item.name,
            "status": item.status,
            "blocked": item.blocked,
            **({"reason": item.reason} if item.reason else {}),
        }
        for item in tool_calls
    ]
    response.internal_json.notifications = []
    preview_meta = entities.get("response_preview")
    if not isinstance(preview_meta, dict):
        preview_meta = {}
    preview_meta.update(
        {
            "mode": "stateless_single_question",
            "history_used": False,
            "history_created": False,
            "persisted": False,
            "created_records": [],
            "allowed_tool_names": sorted(READ_ONLY_PREVIEW_TOOLS),
        }
    )
    if any(item.blocked for item in tool_calls):
        preview_meta["blocked_tool_names"] = [item.name for item in tool_calls if item.blocked]
    entities["response_preview"] = preview_meta
    return response


def _requires_stay_quote_guard(response: LLMResponse, executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when a preview stay-price answer needs availability grounding."""
    intent = str(response.internal_json.intent or "").strip().lower()
    if intent == "stay_quote":
        return True
    return "booking_quote" in executed_booking_tool_names(executed_calls)


def _apply_guarded_stay_quote_preview(
    response: LLMResponse,
    *,
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
    requested_language: str,
) -> LLMResponse:
    """Replace model-composed stay quote text with availability-filtered deterministic text."""
    language = _response_language(response, requested_language)
    guarded = build_guarded_stay_quote(
        hotel_id=hotel_id,
        executed_calls=executed_calls,
        language=language,
    )
    if guarded is None or not guarded.messages:
        return response

    response.user_message = guarded.messages[0]
    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    preview_meta = entities.get("response_preview")
    if not isinstance(preview_meta, dict):
        preview_meta = {}
    preview_meta["stay_quote_availability_guard"] = {
        "applied": True,
        "available_room_type_ids": guarded.available_room_type_ids,
        "handoff_reason": guarded.handoff_reason,
    }
    entities["response_preview"] = preview_meta
    if len(guarded.messages) > 1:
        entities["user_message_parts"] = guarded.messages
    response.internal_json.entities = entities

    if guarded.handoff_reason is not None:
        response.internal_json.state = "HANDOFF"
        response.internal_json.handoff = {"needed": True, "reason": guarded.handoff_reason}
        response.internal_json.next_step = "handoff_to_live_price_team"
        risk_flags = list(response.internal_json.risk_flags or [])
        if "UNRESOLVED_CASE" not in risk_flags:
            risk_flags.append("UNRESOLVED_CASE")
        response.internal_json.risk_flags = risk_flags
    return response


def _attach_translation_metadata(
    response: LLMResponse,
    translation: ResponsePreviewTranslation,
) -> LLMResponse:
    """Expose admin translation state in preview metadata only."""
    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    response.internal_json.entities = entities
    preview_meta = entities.get("response_preview")
    if not isinstance(preview_meta, dict):
        preview_meta = {}
    preview_meta["admin_translation"] = {
        "available": translation.available,
        "source_language": translation.source_language,
        "target_language": translation.target_language,
        "history_used": False,
        "history_created": False,
        "persisted": False,
    }
    entities["response_preview"] = preview_meta
    return response


def _enforce_no_preview_side_effect_claims(response: LLMResponse) -> LLMResponse:
    if not _SIDE_EFFECT_COMMITMENT_PATTERN.search(response.user_message or ""):
        return response
    language = str(response.internal_json.language or "tr").lower()
    if language == "en":
        response.user_message = (
            "I can share the information available in the hotel data, but I cannot create or submit a request from "
            "this preview screen. The hotel team would need to confirm this in the live flow."
        )
    else:
        response.user_message = (
            "Otel verilerindeki bilgileri paylaşabilirim, ancak bu önizleme ekranından talep veya kayıt "
            "oluşturamam. Bu işlem canlı akışta otel ekibi tarafından doğrulanmalıdır."
        )
    response.internal_json.state = "HANDOFF"
    response.internal_json.handoff = {
        "needed": True,
        "reason": "response_preview_side_effect_claim_blocked",
    }
    response.internal_json.next_step = "preview_requires_live_flow_or_admin_confirmation"
    risk_flags = list(response.internal_json.risk_flags or [])
    if "UNRESOLVED_CASE" not in risk_flags:
        risk_flags.append("UNRESOLVED_CASE")
    response.internal_json.risk_flags = risk_flags
    return response


def _clean_question(question: str) -> str:
    value = str(question or "").strip()
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value)
    return value[:MAX_PREVIEW_QUESTION_CHARS]


def _normalize_language(language: str) -> str:
    value = str(language or "auto").strip().lower()
    if value in {"tr", "en", "ru", "de", "ar", "es", "fr", "zh", "hi", "pt"}:
        return value
    return "auto"


def _response_language(response: LLMResponse, requested_language: str) -> str:
    detected = _normalize_language(str(response.internal_json.language or "auto"))
    if detected != "auto":
        return detected
    requested = _normalize_language(requested_language)
    if requested != "auto":
        return requested
    return "tr"


def _normalize_response_style(response_style: str) -> str:
    value = str(response_style or "professional").strip().lower()
    if value in PREVIEW_RESPONSE_STYLES:
        return value
    return "professional"


def _default_language(language: str) -> str:
    normalized = _normalize_language(language)
    return "tr" if normalized == "auto" else normalized


def _normalize_tool_args(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            loaded = orjson.loads(value)
        except orjson.JSONDecodeError:
            return {}
        if isinstance(loaded, dict):
            return cast(dict[str, Any], loaded)
    return {}


def _redact_tool_args(args: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in args.items():
        normalized_key = str(key).lower()
        redacted[key] = "[redacted]" if normalized_key in _REDACTED_ARGUMENT_KEYS else value
    return redacted


def _to_json_string(value: Any) -> str:
    try:
        return orjson.dumps(value).decode()
    except TypeError:
        return orjson.dumps({"error": "tool_result_not_serializable"}).decode()


def _extract_chat_message_content(response: dict[str, Any]) -> str:
    choices = response.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [str(item.get("text") or "") for item in content if isinstance(item, dict)]
        return "".join(parts)
    return ""
