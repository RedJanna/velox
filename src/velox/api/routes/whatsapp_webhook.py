"""WhatsApp webhook routes for verification and incoming messages."""

from collections import defaultdict, deque
import hashlib
import re
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
import orjson
import structlog

from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.adapters.whatsapp.webhook import IncomingMessage, WhatsAppWebhook
from velox.adapters.elektraweb.endpoints import CHILD_OCCUPANCY_UNVERIFIED
from velox.config.settings import settings
from velox.core.hotel_profile_loader import get_profile
from velox.core.pipeline import post_process_escalation
from velox.db.repositories.conversation import ConversationRepository
from velox.llm.client import LLMUnavailableError, get_llm_client
from velox.llm.function_registry import get_tool_definitions
from velox.llm.mock_tool_executor import mock_tool_executor
from velox.llm.prompt_builder import get_prompt_builder
from velox.llm.response_parser import ResponseParser
from velox.models.conversation import Conversation, InternalJSON, LLMResponse, Message

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

DEDUPE_TTL_SECONDS = 3600
MAX_TEXT_LENGTH = 4096

PAYMENT_DATA_PATTERN = re.compile(
    r"(\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b)|(\bcvv\b)|(\botp\b)",
    flags=re.IGNORECASE,
)

TR_FREE_CANCEL_NOTE = (
    "Ücretsiz iptal seçeneği ile yapılan rezervasyonlarda girişten 5 gün öncesine kadar "
    "iptal olması halinde %100 geri ödeme alabilirsiniz."
)
TR_NON_REFUNDABLE_NOTE = (
    "Rezervasyon onayı için iptal edilemez rezervasyonlarda 1 gecelik ödeme tahsil edilmektedir. "
    "Kalan ödemeyi giriş günündeki güncel döviz kuruna göre TL veya döviz olarak yapabilirsiniz."
)
TR_ROOM_NUMBER_NOTE = (
    "Nazik bilgilendirme: Oda numarası için önceden garanti veremiyoruz; ancak girişiniz sırasında "
    "uygunluk doğrultusunda size memnuniyetle yardımcı oluruz."
)
TR_CHILD_OCCUPANCY_NOTE = (
    "Çocuklu konaklamalarda yanlış fiyat vermemek için resmi fiyatınızı manuel olarak "
    "kontrol edip size ileteceğiz."
)


class SlidingWindowRateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, max_calls: int, window_seconds: int) -> bool:
        """Return True if key is under limit for given window."""
        now = time.time()
        queue = self._events[key]

        while queue and queue[0] <= now - window_seconds:
            queue.popleft()

        if len(queue) >= max_calls:
            return False

        queue.append(now)
        return True


class MessageDeduplicator:
    """In-memory deduplication for incoming Meta message ids."""

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, float] = {}

    def is_duplicate(self, message_id: str) -> bool:
        """Check if message id exists within dedupe window."""
        self._cleanup()
        if message_id in self._entries:
            return True
        self._entries[message_id] = time.time()
        return False

    def _cleanup(self) -> None:
        """Remove expired dedupe entries."""
        now = time.time()
        expired_keys = [key for key, created_at in self._entries.items() if now - created_at > self.ttl_seconds]
        for key in expired_keys:
            del self._entries[key]


webhook_handler = WhatsAppWebhook(
    verify_token=settings.whatsapp_verify_token,
    app_secret=settings.whatsapp_app_secret,
)
formatter = WhatsAppFormatter()
phone_minute_limiter = SlidingWindowRateLimiter()
phone_hour_limiter = SlidingWindowRateLimiter()
ip_limiter = SlidingWindowRateLimiter()
deduplicator = MessageDeduplicator(ttl_seconds=DEDUPE_TTL_SECONDS)


def _mask_phone(phone: str) -> str:
    """Mask phone number for safe logs."""
    if len(phone) < 4:
        return "***"
    return f"{phone[:3]}***{phone[-2:]}"


def _hash_phone(phone: str) -> str:
    """Hash phone for storage and lookup."""
    return hashlib.sha256(phone.encode()).hexdigest()


def _normalize_text(text: str) -> str:
    """Normalize incoming text to safe bounded plain text."""
    sanitized = text.replace("\x00", " ").strip()
    return formatter.truncate(sanitized, MAX_TEXT_LENGTH)


def _payment_warning_message() -> str:
    """Security warning for card/OTP data sharing."""
    return (
        "Guvenliginiz icin lutfen kart/OTP gibi odeme bilgilerinizi buradan paylasmayiniz. "
        "Sizi ilgili ekibe yonlendiriyorum."
    )


def _default_reply_message() -> str:
    """Fallback response before LLM pipeline is integrated."""
    return (
        "Mesajinizi aldim. Talebiniz ilgili ekibe iletildi; en kisa surede yardimci olacagiz.\n\n"
        + formatter.format_options(
            [
                "Konaklama",
                "Restoran",
                "Transfer",
            ]
        )
    )


def _wants_prepayment_timing(user_text: str) -> bool:
    """Return True when the guest explicitly asks when prepayment is taken."""
    normalized = user_text.casefold()
    keywords = ("ön ödeme", "on odeme", "prepayment", "ne zaman", "kaç gün", "kac gun")
    return any(keyword in normalized for keyword in keywords)


def _canonical_text(value: str) -> str:
    """Normalize text for fuzzy duplicate checks."""
    lowered = value.casefold()
    return re.sub(r"[^a-z0-9çğıöşü]+", "", lowered)


def _ensure_single_note(text: str, note: str) -> str:
    """Keep at most one note variant; append once if missing."""
    canonical_note = _canonical_text(note)
    lines = text.splitlines()
    output_lines: list[str] = []
    found = False

    for line in lines:
        line_canonical = _canonical_text(line)
        if canonical_note and canonical_note in line_canonical:
            if found:
                continue
            found = True
        output_lines.append(line)

    merged = "\n".join(output_lines).strip()
    if found:
        return merged
    return f"{merged}\n\n{note}".strip()


def _loads_tool_payload(value: Any) -> dict[str, Any]:
    """Parse a tool result/arguments payload into a dict when possible."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            loaded = orjson.loads(value)
        except orjson.JSONDecodeError:
            return {}
        if isinstance(loaded, dict):
            return loaded
    return {}


def _extract_requested_occupancy(executed_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract stay quote occupancy from executed booking tool arguments."""
    for call in executed_calls:
        if str(call.get("name") or "") not in {"booking_quote", "booking_availability"}:
            continue
        args = _loads_tool_payload(call.get("arguments"))
        if args:
            return {
                "checkin_date": args.get("checkin_date"),
                "checkout_date": args.get("checkout_date"),
                "adults": args.get("adults"),
                "chd_count": args.get("chd_count", 0),
                "chd_ages": args.get("chd_ages", []),
                "currency": args.get("currency", "EUR"),
                "nationality": args.get("nationality", "TR"),
            }
    return {}


def _has_child_quote_mismatch(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when booking quote failed because child occupancy was ignored."""
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_quote":
            continue
        result = _loads_tool_payload(call.get("result"))
        error_text = str(result.get("error") or "")
        if CHILD_OCCUPANCY_UNVERIFIED in error_text:
            return True
    return False


def _build_child_quote_handoff_response(executed_calls: list[dict[str, Any]]) -> LLMResponse:
    """Create a deterministic fallback when PMS ignores requested child occupancy."""
    entities = _extract_requested_occupancy(executed_calls)
    return LLMResponse(
        user_message=TR_CHILD_OCCUPANCY_NOTE,
        internal_json=InternalJSON(
            language="tr",
            intent="stay_quote",
            state="HANDOFF",
            entities=entities,
            handoff={"needed": True, "reason": "child_quote_manual_verification"},
            next_step="manual_child_quote_verification",
        ),
    )


def _is_child_bedding_question(user_text: str, entities: dict[str, Any]) -> bool:
    """Return True when the guest asks about bedding for multiple children."""
    normalized = user_text.casefold()
    bed_keywords = ("ek yatak", "ekstra yatak", "yatak", "sofa", "extra bed")
    child_keywords = ("2 çocuk", "2 cocuk", "iki çocuk", "iki cocuk")
    child_count = int(entities.get("chd_count", 0) or 0)
    return any(keyword in normalized for keyword in bed_keywords) and (
        child_count >= 2 or any(keyword in normalized for keyword in child_keywords)
    )


def _is_parking_question(user_text: str) -> bool:
    """Return True when the guest asks about parking or valet availability."""
    normalized = user_text.casefold()
    keywords = ("otopark", "park yeri", "vale", "parking", "aracımızla", "aracimizla", "arabamızla", "arabamizla")
    return any(_contains_keyword(normalized, keyword) for keyword in keywords)


def _is_payment_method_question(user_text: str) -> bool:
    """Return True when the guest asks which payment methods are accepted."""
    normalized = user_text.casefold()
    keywords = (
        "nakit",
        "havale",
        "banka havalesi",
        "bank transfer",
        "ödeme yöntemi",
        "odeme yontemi",
        "kredi kartı dışında",
        "kredi karti disinda",
        "mail order",
        "pos",
    )
    return any(_contains_keyword(normalized, keyword) for keyword in keywords)


def _contains_keyword(text: str, keyword: str) -> bool:
    """Match single words by boundary and phrases by substring."""
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def _build_turkish_parking_reply(hotel_id: int) -> str:
    """Build deterministic Turkish parking guidance from HOTEL_PROFILE."""
    profile = get_profile(hotel_id)
    if profile is None:
        return (
            "Aracınız için park yeri ayarlayabiliriz. Ücretsiz cadde park yerleri mevcuttur, "
            "ayrıca otelin karşısında özel bir otopark da bulunmaktadır. Varışınızda sizi park "
            "alanına yönlendireceğiz."
        )

    parking_policy = profile.facility_policies.get("parking", {})
    reply = parking_policy.get("reply_tr")
    if isinstance(reply, str) and reply.strip():
        return reply.strip()
    return (
        "Aracınız için park yeri ayarlayabiliriz. Ücretsiz cadde park yerleri mevcuttur, "
        "ayrıca otelin karşısında özel bir otopark da bulunmaktadır. Varışınızda sizi park "
        "alanına yönlendireceğiz."
    )


def _build_turkish_payment_methods_reply(hotel_id: int) -> str:
    """Build deterministic Turkish payment-method guidance from HOTEL_PROFILE."""
    profile = get_profile(hotel_id)
    if profile is None:
        return (
            "Evet, kredi kartı dışında nakit ve havale kabul ediyoruz. İsterseniz rezervasyon "
            "aşamasında size uygun ödeme yöntemini birlikte netleştirebiliriz."
        )

    payment_policy = profile.model_dump().get("payment", {})
    reply = payment_policy.get("reply_tr")
    if isinstance(reply, str) and reply.strip():
        return reply.strip()
    return (
        "Evet, kredi kartı dışında nakit ve havale kabul ediyoruz. İsterseniz rezervasyon "
        "aşamasında size uygun ödeme yöntemini birlikte netleştirebiliriz."
    )


def _build_turkish_child_bedding_reply(hotel_id: int, entities: dict[str, Any]) -> str:
    """Build deterministic Turkish guidance for 2-child bedding questions."""
    profile = get_profile(hotel_id)
    if profile is None:
        return (
            "2 çocuklu konaklamalarda oda tipine ve uygunluğa göre 2 ek yatak veya "
            "1 ek yatak + 1 sofa hazırlanabilir."
        )

    adults = int(entities.get("adults", 2) or 2)
    child_count = max(int(entities.get("chd_count", 0) or 0), 2)
    total_guests = adults + child_count
    suitable_rooms = [
        room_type.name.tr
        for room_type in profile.room_types
        if room_type.max_pax >= total_guests and room_type.extra_bed
    ]
    children_policy = profile.facility_policies.get("children", {})
    bedding_note = str(
        children_policy.get(
            "bedding_note_tr",
            "2 çocuklu konaklamalarda oda tipine ve uygunluğa göre 2 ek yatak veya "
            "1 ek yatak + 1 sofa hazırlanabilir.",
        )
    )

    lines = [
        "2 çocuk için tek ek yatak bilgisi doğru değildir.",
        bedding_note,
    ]
    if suitable_rooms:
        room_names = ", ".join(f"**{room_name}**" for room_name in suitable_rooms)
        lines.append(f"{adults} yetişkin + {child_count} çocuk için uygun oda tiplerimiz: {room_names}.")
    if not entities.get("chd_ages"):
        lines.append("Çocukların yaşlarını paylaşırsanız size en uygun oda tipini netleştirebilirim.")
    return "\n\n".join(lines).strip()


def _normalize_turkish_stay_quote_reply(reply_text: str, user_text: str) -> str:
    """Apply deterministic Turkish pricing wording and required notes."""
    normalized_reply = (
        reply_text.replace("Non-Refundable", "İptal edilemez")
        .replace("Non‑Refundable", "İptal edilemez")
        .replace("Non refundable", "İptal edilemez")
        .replace("FREE CANCEL", "Ücretsiz İptal")
        .replace("Free Cancel", "Ücretsiz İptal")
        .replace("free cancel", "ücretsiz iptal")
        .replace("İptal Edilemez", "İptal edilemez")
        .replace("Ücretsiz iptal", "Ücretsiz İptal")
    )

    keep_seven_day_info = _wants_prepayment_timing(user_text)
    filtered_lines: list[str] = []
    for raw_line in normalized_reply.splitlines():
        line = raw_line.strip()
        lowered = line.casefold()
        if "eur baz" in lowered:
            continue
        if ("7 gün" in lowered or "7 gun" in lowered) and not keep_seven_day_info:
            continue
        filtered_lines.append(raw_line)

    text = "\n".join(filtered_lines).strip()
    text = _ensure_single_note(text, TR_FREE_CANCEL_NOTE)
    text = _ensure_single_note(text, TR_NON_REFUNDABLE_NOTE)
    text = _ensure_single_note(text, TR_ROOM_NUMBER_NOTE)
    return text.strip()


def _executed_booking_quote(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when the pipeline actually fetched stay pricing."""
    return any(str(call.get("name") or "") == "booking_quote" for call in executed_calls)


async def _run_message_pipeline(
    conversation: Conversation,
    normalized_text: str,
    dispatcher: Any | None = None,
) -> LLMResponse:
    """Run message pipeline and return structured LLM response."""
    if PAYMENT_DATA_PATTERN.search(normalized_text):
        return LLMResponse(
            user_message=_payment_warning_message(),
            internal_json=InternalJSON(
                intent="payment_inquiry",
                state="HANDOFF",
                risk_flags=["PAYMENT_CONFUSION"],
                next_step="handoff_to_sales",
            ),
        )

    try:
        prompt_builder = get_prompt_builder()
        llm_client = get_llm_client()
        messages = prompt_builder.build_messages(conversation, normalized_text)
        tools = get_tool_definitions()
        tool_executor = mock_tool_executor
        if dispatcher is not None:
            tool_executor = _build_dispatcher_executor(dispatcher)
        else:
            logger.warning("tool_dispatcher_missing_fallback_to_mock")

        content, executed_calls = await llm_client.run_tool_call_loop(
            messages=messages,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=5,
        )

        if executed_calls:
            logger.info(
                "llm_tool_calls_executed",
                tools=[c["name"] for c in executed_calls],
                count=len(executed_calls),
            )

        if _has_child_quote_mismatch(executed_calls):
            logger.warning("stay_quote_child_occupancy_manual_verification")
            return _build_child_quote_handoff_response(executed_calls)

        parsed = ResponseParser.parse(content)
        intent = str(parsed.internal_json.intent or "").lower()
        language = str(parsed.internal_json.language or "tr").lower()
        entities = parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else {}
        if language == "tr" and _is_payment_method_question(normalized_text):
            parsed.user_message = _build_turkish_payment_methods_reply(conversation.hotel_id)
            return parsed
        if language == "tr" and _is_parking_question(normalized_text):
            parsed.user_message = _build_turkish_parking_reply(conversation.hotel_id)
            return parsed
        if language == "tr" and _is_child_bedding_question(normalized_text, entities):
            parsed.user_message = _build_turkish_child_bedding_reply(conversation.hotel_id, entities)
            return parsed
        if intent == "stay_quote" and language == "tr" and _executed_booking_quote(executed_calls):
            parsed.user_message = _normalize_turkish_stay_quote_reply(parsed.user_message, normalized_text)
        return parsed
    except LLMUnavailableError:
        logger.warning("llm_unavailable_fallback")
        return LLMResponse(
            user_message=_default_reply_message(),
            internal_json=InternalJSON(
                intent="other",
                state="INTENT_DETECTED",
                risk_flags=[],
                next_step="await_user_input",
            ),
        )


def _build_dispatcher_executor(dispatcher: Any) -> Any:
    """Wrap ToolDispatcher into the executor signature expected by LLMClient."""

    async def _execute(tool_name: str, tool_args: str | dict[str, Any]) -> str:
        if isinstance(tool_args, str):
            try:
                parsed_args: dict[str, Any] = orjson.loads(tool_args)
            except orjson.JSONDecodeError:
                parsed_args = {}
        elif isinstance(tool_args, dict):
            parsed_args = tool_args
        else:
            parsed_args = {}

        result = await dispatcher.dispatch(tool_name, **parsed_args)
        return orjson.dumps(result).decode()

    return _execute


class _HandoffToolAdapter:
    """Adapter exposing create_ticket method for escalation engine."""

    def __init__(self, dispatcher: Any) -> None:
        self._dispatcher = dispatcher

    async def create_ticket(self, **kwargs: Any) -> dict[str, Any]:
        """Dispatch handoff ticket tool call."""
        return await self._dispatcher.dispatch("handoff_create_ticket", **kwargs)


class _NotifyToolAdapter:
    """Adapter exposing send method for escalation engine."""

    def __init__(self, dispatcher: Any) -> None:
        self._dispatcher = dispatcher

    async def send(self, **kwargs: Any) -> dict[str, Any]:
        """Dispatch notification tool call."""
        return await self._dispatcher.dispatch("notify_send", **kwargs)


async def _create_or_get_conversation(repository: ConversationRepository, incoming: IncomingMessage) -> Conversation:
    """Get active conversation by phone hash or create one."""
    phone_hash = _hash_phone(incoming.phone)
    conversation = await repository.get_active_by_phone(settings.elektra_hotel_id, phone_hash)
    if conversation is not None:
        return conversation

    new_conversation = Conversation(
        hotel_id=settings.elektra_hotel_id,
        phone_hash=phone_hash,
        phone_display=_mask_phone(incoming.phone),
        language="tr",
    )
    return await repository.create(new_conversation)


async def _process_incoming_message(
    incoming: IncomingMessage,
    dispatcher: Any,
    escalation_engine: Any,
    tools: dict[str, Any],
    db_pool: Any,
) -> None:
    """Background pipeline: log message, generate response, and send via WhatsApp."""
    conversation_repository = ConversationRepository()
    whatsapp_client = get_whatsapp_client()

    try:
        conversation = await _create_or_get_conversation(conversation_repository, incoming)
        if conversation.id is None:
            raise RuntimeError("Conversation id is missing.")

        normalized_text = _normalize_text(incoming.text)

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=normalized_text,
        )
        await conversation_repository.add_message(user_msg)
        conversation.messages.append(user_msg)

        await whatsapp_client.mark_as_read(incoming.message_id)

        llm_response = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=normalized_text,
            dispatcher=dispatcher,
        )
        reply_text = formatter.truncate(llm_response.user_message)
        await whatsapp_client.send_text_message(to=incoming.phone, body=reply_text)

        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply_text,
            internal_json=llm_response.internal_json.model_dump(mode="json"),
        )
        await conversation_repository.add_message(assistant_msg)
        conversation.messages.append(assistant_msg)

        if escalation_engine is not None and db_pool is not None and "handoff" in tools and "notify" in tools:
            escalation_result = await post_process_escalation(
                user_message_text=normalized_text,
                llm_response=llm_response,
                conversation=conversation,
                escalation_engine=escalation_engine,
                tools=tools,
                db_pool=db_pool,
            )
            if escalation_result.level.value != "L0" or escalation_result.risk_flags_matched:
                logger.info(
                    "escalation_check",
                    conversation_id=str(conversation.id),
                    level=escalation_result.level.value,
                    flags=escalation_result.risk_flags_matched,
                    actions=escalation_result.actions,
                )
    except Exception:
        logger.exception(
            "whatsapp_background_processing_failed",
            message_id=incoming.message_id,
            phone=_mask_phone(incoming.phone),
        )


def _schedule_background_task(
    background_tasks: BackgroundTasks,
    incoming: IncomingMessage,
    dispatcher: Any,
    escalation_engine: Any,
    tools: dict[str, Any],
    db_pool: Any,
) -> None:
    """Add incoming message task to FastAPI background worker."""
    background_tasks.add_task(_process_incoming_message, incoming, dispatcher, escalation_engine, tools, db_pool)


@router.get("", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> PlainTextResponse:
    """Meta webhook verification endpoint."""
    challenge = webhook_handler.verify_subscription(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return PlainTextResponse(content=challenge)


@router.post("")
async def receive_message(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Handle incoming WhatsApp webhook events."""
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not webhook_handler.validate_signature(payload, signature):
        logger.warning("whatsapp_invalid_signature")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        body = orjson.loads(payload)
    except orjson.JSONDecodeError:
        logger.warning("whatsapp_invalid_payload")
        return {"status": "ok"}

    incoming = webhook_handler.parse_message(body)

    if incoming is None:
        logger.info("whatsapp_webhook_status_event")
        return {"status": "ok"}

    if deduplicator.is_duplicate(incoming.message_id):
        logger.info("whatsapp_webhook_duplicate", message_id=incoming.message_id)
        return {"status": "ok"}

    phone_hash = _hash_phone(incoming.phone)
    webhook_ip = request.client.host if request.client is not None else "unknown"

    if not ip_limiter.allow(webhook_ip, settings.rate_limit_webhook_per_minute, 60):
        logger.warning("whatsapp_webhook_ip_limited", ip=webhook_ip)
        return {"status": "ok"}

    per_minute_allowed = phone_minute_limiter.allow(phone_hash, settings.rate_limit_per_phone_per_minute, 60)
    per_hour_allowed = phone_hour_limiter.allow(phone_hash, settings.rate_limit_per_phone_per_hour, 3600)
    if not per_minute_allowed or not per_hour_allowed:
        logger.warning("whatsapp_phone_rate_limited", phone=_mask_phone(incoming.phone))
        return {"status": "ok"}

    dispatcher = getattr(request.app.state, "tool_dispatcher", None)
    escalation_engine = getattr(request.app.state, "escalation_engine", None)
    db_pool = getattr(request.app.state, "db_pool", None)

    tools = {
        "handoff": _HandoffToolAdapter(dispatcher) if dispatcher is not None else None,
        "notify": _NotifyToolAdapter(dispatcher) if dispatcher is not None else None,
    }
    if tools["handoff"] is None or tools["notify"] is None:
        tools = {}

    _schedule_background_task(background_tasks, incoming, dispatcher, escalation_engine, tools, db_pool)
    logger.info(
        "whatsapp_webhook_message_accepted",
        phone=_mask_phone(incoming.phone),
        message_type=incoming.message_type,
    )
    return {"status": "accepted"}
