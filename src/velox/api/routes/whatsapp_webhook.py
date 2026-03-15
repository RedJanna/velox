"""WhatsApp webhook routes for verification and incoming messages."""

import re
import time
import unicodedata
from collections import defaultdict, deque
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, cast

import orjson
import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from velox.adapters.elektraweb.endpoints import CHILD_OCCUPANCY_UNVERIFIED
from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.adapters.whatsapp.webhook import IncomingMessage, WhatsAppWebhook
from velox.config.constants import CONTEXT_WINDOW_MAX_MESSAGES, SUPPORTED_LANGUAGES
from velox.config.settings import settings
from velox.core.hotel_profile_loader import get_profile
from velox.core.pipeline import post_process_escalation
from velox.db.repositories.conversation import ConversationRepository
from velox.db.repositories.whatsapp_number import WhatsAppNumberRepository
from velox.llm.client import LLMUnavailableError, get_llm_client
from velox.llm.function_registry import get_tool_definitions
from velox.llm.prompt_builder import get_prompt_builder
from velox.llm.response_parser import ResponseParser
from velox.models.conversation import Conversation, InternalJSON, LLMResponse, Message
from velox.utils.privacy import hash_phone

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

DEDUPE_TTL_SECONDS = 3600
MAX_TEXT_LENGTH = 4096
WEBHOOK_MAX_AGE_SECONDS = 300

PAYMENT_DATA_PATTERN = re.compile(
    r"(\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b)|(\bcvv\b)|(\botp\b)",
    flags=re.IGNORECASE,
)
PAYMENT_TOPIC_PATTERN = re.compile(
    r"(odeme|ödeme|payment|havale|banka|iban|kart|mail order|pos|charge|refund)",
    flags=re.IGNORECASE,
)
PAYMENT_REFERENCE_PATTERN = re.compile(
    r"\b(?:S_HOLD_[A-Z0-9_]+|APR_[A-Z0-9_]+|PAY_[A-Z0-9_]+|[A-Z]{1,4}\d{4,})\b"
)
EXPLICIT_YEAR_PATTERN = re.compile(r"\b20\d{2}\b")
YEAR_KEYWORD_PATTERN = re.compile(r"\b(y[ıi]l|year)\b", flags=re.IGNORECASE)

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
TR_ROOM_SPLIT_REQUIRED_NOTE = (
    "Toplam kişi sayınız oda başı kapasiteyi aştığı için konaklamayı 2 oda olarak planlamamız gerekiyor. "
    "Oda dağılımını (ör. 3+3 veya 4+2) paylaşırsanız her iki iptal politikası için toplam fiyatı iletebilirim."
)
TR_NO_AVAILABLE_ROOM_FOR_QUOTE = (
    "Paylaştığınız tarihlerde şu an müsait görünen oda tipi bulunmuyor. "
    "İsterseniz farklı tarih veya alternatif oda ile hemen tekrar kontrol edebilirim."
)
PRICE_ROUNDING_INCREMENT = Decimal("5")
SUPPORTED_LANGUAGE_CODES = set(SUPPORTED_LANGUAGES)
TURKISH_LANGUAGE_HINTS = (
    "ve",
    "icin",
    "lutfen",
    "merhaba",
    "rezervasyon",
    "otel",
    "fiyat",
    "kisi",
    "kişi",
)
ENGLISH_LANGUAGE_HINTS = (
    "i",
    "need",
    "please",
    "hotel",
    "booking",
    "price",
    "checkin",
    "checkout",
    "airport",
    "transfer",
)
GERMAN_LANGUAGE_HINTS = (
    "hallo",
    "bitte",
    "zimmer",
    "preis",
    "buchung",
    "flughafen",
    "transfer",
    "fruhstuck",
)
ARABIC_LANGUAGE_HINTS = (
    "حجز",
    "غرفة",
    "سعر",
    "مطار",
    "نقل",
)
SPANISH_LANGUAGE_HINTS = (
    "hola",
    "por favor",
    "habitacion",
    "precio",
    "reserva",
    "aeropuerto",
    "traslado",
    "desayuno",
)
FRENCH_LANGUAGE_HINTS = (
    "bonjour",
    "chambre",
    "prix",
    "reservation",
    "aeroport",
    "transfert",
    "petit dejeuner",
)
CHINESE_LANGUAGE_HINTS = (
    "酒店",
    "房间",
    "价格",
    "机场",
    "接送",
)
HINDI_LANGUAGE_HINTS = (
    "होटल",
    "कमरा",
    "कीमत",
    "बुकिंग",
    "एयरपोर्ट",
)
PORTUGUESE_LANGUAGE_HINTS = (
    "ola",
    "por favor",
    "quarto",
    "preco",
    "reserva",
    "aeroporto",
    "transfer",
    "cafe da manha",
)
LANGUAGE_HINTS = {
    "tr": TURKISH_LANGUAGE_HINTS,
    "en": ENGLISH_LANGUAGE_HINTS,
    "de": GERMAN_LANGUAGE_HINTS,
    "ar": ARABIC_LANGUAGE_HINTS,
    "es": SPANISH_LANGUAGE_HINTS,
    "fr": FRENCH_LANGUAGE_HINTS,
    "zh": CHINESE_LANGUAGE_HINTS,
    "hi": HINDI_LANGUAGE_HINTS,
    "pt": PORTUGUESE_LANGUAGE_HINTS,
}
SCRIPT_LANGUAGE_PATTERNS = (
    (re.compile(r"[\u0400-\u04FF]"), "ru"),
    (re.compile(r"[\u0600-\u06FF]"), "ar"),
    (re.compile(r"[\u0900-\u097F]"), "hi"),
    (re.compile(r"[\u4E00-\u9FFF]"), "zh"),
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
    return hash_phone(phone)


async def _resolve_hotel_id_for_incoming(incoming: IncomingMessage, db_pool: Any) -> int | None:
    """Resolve target hotel for incoming webhook message."""
    if db_pool is None:
        logger.warning(
            "whatsapp_hotel_resolution_db_unavailable",
            fallback_hotel_id=settings.elektra_hotel_id,
        )
        return settings.elektra_hotel_id

    if not incoming.phone_number_id and not incoming.display_phone_number:
        logger.warning(
            "whatsapp_hotel_resolution_metadata_missing",
            fallback_hotel_id=settings.elektra_hotel_id,
            message_id=incoming.message_id,
        )
        return settings.elektra_hotel_id

    repository = WhatsAppNumberRepository()
    if incoming.phone_number_id:
        hotel_id = await repository.get_hotel_id_by_phone_number_id(incoming.phone_number_id)
        if hotel_id is not None:
            return hotel_id

    if incoming.display_phone_number:
        hotel_id = await repository.get_hotel_id_by_display_phone_number(incoming.display_phone_number)
        if hotel_id is not None:
            return hotel_id

    logger.warning(
        "whatsapp_hotel_resolution_unmapped_destination",
        message_id=incoming.message_id,
        phone_number_id=incoming.phone_number_id,
        display_phone_number=incoming.display_phone_number,
    )
    return None


async def _redis_allow_rate_limit(
    redis_client: Any,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> bool:
    """Use Redis sliding window to enforce a distributed rate limit."""
    now = time.time()
    window_start = now - window_seconds
    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window_seconds + 1)
    results = await pipe.execute()
    current_count = int(results[1] or 0)
    return current_count < max_requests


async def _redis_is_duplicate_message(
    redis_client: Any,
    message_id: str,
) -> bool:
    """Use Redis key expiry to prevent duplicate webhook processing across replicas."""
    key = f"wa:dedupe:{message_id}"
    inserted = await redis_client.set(key, "1", ex=DEDUPE_TTL_SECONDS, nx=True)
    return not bool(inserted)


def _normalize_text(text: str) -> str:
    """Normalize incoming text to safe bounded plain text."""
    sanitized = text.replace("\x00", " ").strip()
    return formatter.truncate(sanitized, MAX_TEXT_LENGTH)


def _payment_warning_message(language: str = "tr") -> str:
    """Security warning for card/OTP data sharing."""
    if language == "en":
        return (
            "For your security, please do not share card/OTP payment details here. "
            "I am forwarding you to the relevant team."
        )
    if language == "ru":
        return (
            "В целях вашей безопасности, пожалуйста, не отправляйте здесь данные карты/OTP. "
            "Я передаю ваш запрос профильной команде."
        )
    return (
        "Guvenliginiz icin lutfen kart/OTP gibi odeme bilgilerinizi buradan paylasmayiniz. "
        "Sizi ilgili ekibe yonlendiriyorum."
    )


def _stay_pending_approval_message(language: str = "tr") -> str:
    """Guest-facing hold acknowledgement before admin approval."""
    if language == "en":
        return (
            "Your reservation request has been received. "
            "It is not finalized yet.\n\n"
            "After our guest relations team reviews and approves it, we will send your confirmation."
        )
    if language == "ru":
        return (
            "Мы получили ваш запрос на бронирование. "
            "Он пока не подтвержден.\n\n"
            "После проверки и подтверждения нашим представителем мы отправим вам уведомление."
        )
    return (
        "Rezervasyon talebinizi aldik. Talebiniz henuz kesinlesmedi.\n\n"
        "Musteri temsilcimiz kontrol edip onayladiktan sonra size onay bilgisini iletecegiz."
    )


def _payment_intake_prompt(language: str, missing_fields: list[str]) -> str:
    """Build payment handoff intake question based on missing fields."""
    missing_reference = "reference_id" in missing_fields
    missing_name = "full_name" in missing_fields

    if language == "en":
        if missing_reference and missing_name:
            return (
                "I can connect you to our payment team.\n\n"
                "To proceed, please share:\n"
                "1. Reservation/hold reference\n"
                "2. Full name"
            )
        if missing_reference:
            return "Please share your reservation/hold reference so I can connect you to the payment team."
        return "Please share your full name so I can forward your payment request to our team."

    if language == "ru":
        if missing_reference and missing_name:
            return (
                "Я могу передать ваш запрос платежной команде.\n\n"
                "Для продолжения, пожалуйста, укажите:\n"
                "1. Номер бронирования/холда\n"
                "2. Имя и фамилию"
            )
        if missing_reference:
            return "Пожалуйста, укажите номер бронирования/холда для передачи запроса платежной команде."
        return "Пожалуйста, укажите имя и фамилию для передачи вашего платежного запроса команде."

    if missing_reference and missing_name:
        return (
            "Odeme ekibimize yonlendirebilmem icin lutfen su bilgileri paylasin:\n"
            "1. Rezervasyon/hold referansi\n"
            "2. Ad soyad"
        )
    if missing_reference:
        return "Odeme surecini ekibe aktarabilmem icin lutfen rezervasyon/hold referansinizi paylasin."
    return "Odeme surecini ekibe aktarabilmem icin lutfen ad soyad bilginizi paylasin."


def _payment_intake_completed_message(language: str) -> str:
    """Acknowledgement after payment intake is complete."""
    if language == "en":
        return "Thank you. I have forwarded your payment request to our live team. They will contact you shortly."
    if language == "ru":
        return "Спасибо. Я передал(а) ваш платежный запрос нашей команде. С вами свяжутся в ближайшее время."
    return "Tesekkur ederim. Odeme talebinizi canli ekibimize aktardim. En kisa surede sizinle iletisime gececekler."


def _extract_payment_reference(text: str) -> str | None:
    """Extract reservation/hold reference from payment-related text."""
    match = PAYMENT_REFERENCE_PATTERN.search(text)
    if not match:
        return None
    return match.group(0).strip()


def _extract_payment_full_name(text: str) -> str | None:
    """Extract full name from simple self-identification patterns."""
    pattern = re.compile(
        r"(?:ad[ıi]m|ismim|ad soyad(?:im)?|name)\s*[:\-]\s*([a-zA-ZçğıöşüÇĞİÖŞÜ ]{3,80})",
        re.IGNORECASE,
    )
    match = pattern.search(text.strip())
    if match:
        candidate = " ".join(match.group(1).split())
        if len(candidate) >= 3:
            return candidate
    return None


def _has_payment_intake_state(conversation: Conversation) -> bool:
    """Return True when payment intake has already started in conversation entities."""
    entities = conversation.entities_json if isinstance(conversation.entities_json, dict) else {}
    payment_intake = entities.get("payment_intake")
    return isinstance(payment_intake, dict) and bool(payment_intake.get("in_progress"))


def _build_payment_intake_response(
    conversation: Conversation,
    normalized_text: str,
    target_language: str,
) -> LLMResponse | None:
    """Collect minimum payment handoff fields before routing to human team."""
    intake_active = _has_payment_intake_state(conversation)
    payment_related = PAYMENT_TOPIC_PATTERN.search(normalized_text) is not None
    if not payment_related and not intake_active:
        return None

    entities = conversation.entities_json if isinstance(conversation.entities_json, dict) else {}
    intake_state_raw = entities.get("payment_intake")
    intake_state = dict(intake_state_raw) if isinstance(intake_state_raw, dict) else {}
    intake_state["in_progress"] = True

    if not intake_state.get("reference_id"):
        extracted_reference = _extract_payment_reference(normalized_text)
        if extracted_reference:
            intake_state["reference_id"] = extracted_reference

    if not intake_state.get("full_name"):
        extracted_name = _extract_payment_full_name(normalized_text)
        if extracted_name:
            intake_state["full_name"] = extracted_name

    intake_state["last_guest_message"] = normalized_text
    missing_fields: list[str] = []
    if not intake_state.get("reference_id"):
        missing_fields.append("reference_id")
    if not intake_state.get("full_name"):
        missing_fields.append("full_name")

    if missing_fields:
        return LLMResponse(
            user_message=_payment_intake_prompt(target_language, missing_fields),
            internal_json=InternalJSON(
                language=target_language,
                intent="payment_inquiry",
                state="NEEDS_VERIFICATION",
                entities={"payment_intake": intake_state},
                required_questions=missing_fields,
                risk_flags=[],
                handoff={"needed": False, "reason": None},
                next_step="collect_payment_handoff_fields",
            ),
        )

    intake_state["in_progress"] = False
    return LLMResponse(
        user_message=_payment_intake_completed_message(target_language),
        internal_json=InternalJSON(
            language=target_language,
            intent="payment_inquiry",
            state="HANDOFF",
            entities={"payment_intake": intake_state},
            risk_flags=["PAYMENT_CONFUSION"],
            handoff={"needed": True, "reason": "payment_manual_handoff"},
            next_step="handoff_to_sales",
        ),
    )


def _default_reply_message(language: str = "tr") -> str:
    """Fallback response before LLM pipeline is integrated."""
    if language == "en":
        return (
            "I have received your message. Your request has been forwarded to the relevant team, "
            "and we will assist you as soon as possible.\n\n"
            + formatter.format_options(
                [
                    "Stay",
                    "Restaurant",
                    "Transfer",
                ]
            )
        )
    if language == "ru":
        return (
            "Я получил(а) ваше сообщение. Ваш запрос передан профильной команде, "
            "и мы поможем вам в кратчайшие сроки.\n\n"
            + formatter.format_options(
                [
                    "Проживание",
                    "Ресторан",
                    "Трансфер",
                ]
            )
        )
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


def _extract_quote_offers(executed_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return normalized booking quote offers from the latest executed tool result."""
    for call in reversed(executed_calls):
        if str(call.get("name") or "") != "booking_quote":
            continue
        result = _loads_tool_payload(call.get("result"))
        offers = result.get("offers")
        if isinstance(offers, list):
            return [item for item in offers if isinstance(item, dict)]
    return []


def _extract_quote_call_payloads(executed_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ordered booking_quote calls with parsed arguments and offers."""
    payloads: list[dict[str, Any]] = []
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_quote":
            continue
        result = _loads_tool_payload(call.get("result"))
        offers = result.get("offers")
        if not isinstance(offers, list):
            continue
        parsed_offers = [item for item in offers if isinstance(item, dict)]
        if not parsed_offers:
            continue
        payloads.append(
            {
                "arguments": _loads_tool_payload(call.get("arguments")),
                "offers": parsed_offers,
            }
        )
    return payloads


def _extract_available_room_type_ids(executed_calls: list[dict[str, Any]]) -> list[int]:
    """Collect unique available room_type_id values from booking_availability calls."""
    room_type_ids: list[int] = []
    seen: set[int] = set()
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_availability":
            continue
        result = _loads_tool_payload(call.get("result"))
        rows = result.get("rows")
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if bool(row.get("stop_sell")):
                continue
            if int(row.get("room_to_sell", 0) or 0) <= 0:
                continue
            room_type_id = int(row.get("room_type_id", 0) or 0)
            if room_type_id <= 0 or room_type_id in seen:
                continue
            seen.add(room_type_id)
            room_type_ids.append(room_type_id)
        derived = result.get("derived")
        if not isinstance(derived, dict):
            continue
        eligible_ids = derived.get("eligible_room_type_ids")
        if not isinstance(eligible_ids, list):
            continue
        for room_type_id_raw in eligible_ids:
            room_type_id = int(room_type_id_raw or 0)
            if room_type_id <= 0 or room_type_id in seen:
                continue
            seen.add(room_type_id)
            room_type_ids.append(room_type_id)
    return room_type_ids


def _filter_quote_payloads_by_available_room_types(
    payloads: list[dict[str, Any]],
    available_room_type_ids: list[int],
) -> list[dict[str, Any]]:
    """Keep only quote offers whose room_type_id is available."""
    if not available_room_type_ids:
        return payloads
    allowed = set(available_room_type_ids)
    filtered_payloads: list[dict[str, Any]] = []
    for payload in payloads:
        offers = payload.get("offers")
        if not isinstance(offers, list):
            continue
        filtered_offers = [
            offer
            for offer in offers
            if isinstance(offer, dict) and int(offer.get("room_type_id", 0) or 0) in allowed
        ]
        if not filtered_offers:
            continue
        filtered_payloads.append(
            {
                "arguments": payload.get("arguments", {}),
                "offers": filtered_offers,
            }
        )
    return filtered_payloads


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


def _max_room_capacity(hotel_id: int) -> int:
    """Return max room capacity from profile room types."""
    profile = get_profile(hotel_id)
    if profile is None:
        return 4
    capacities = [int(getattr(room_type, "max_pax", 0) or 0) for room_type in getattr(profile, "room_types", [])]
    valid_capacities = [capacity for capacity in capacities if capacity > 0]
    return max(valid_capacities) if valid_capacities else 4


def _format_available_room_names(hotel_id: int, room_type_ids: list[int]) -> list[str]:
    """Resolve available room_type_id values to profile-driven Turkish labels."""
    if not room_type_ids:
        return []
    profile = get_profile(hotel_id)
    if profile is None:
        return []
    room_names: list[str] = []
    for room_type in getattr(profile, "room_types", []):
        pms_room_type_id = int(getattr(room_type, "pms_room_type_id", 0) or 0)
        if pms_room_type_id in room_type_ids:
            room_names.append(str(getattr(getattr(room_type, "name", None), "tr", "") or "").strip())
    return [name for name in room_names if name]


def _requires_multi_room_split(hotel_id: int, entities: dict[str, Any]) -> bool:
    """Return True when requested party size exceeds single-room capacity."""
    adults = int(entities.get("adults", 0) or 0)
    children = int(entities.get("chd_count", 0) or 0)
    total_guests = adults + children
    return total_guests > _max_room_capacity(hotel_id)


def _build_room_split_verification_response(hotel_id: int, executed_calls: list[dict[str, Any]]) -> LLMResponse:
    """Create deterministic room-split follow-up when pricing needs room distribution first."""
    entities = _extract_requested_occupancy(executed_calls)
    available_names = _format_available_room_names(hotel_id, _extract_available_room_type_ids(executed_calls))

    lines = [TR_ROOM_SPLIT_REQUIRED_NOTE]
    if available_names:
        room_lines = "\n".join(f"• {name}" for name in available_names)
        lines.append(f"Müsait görünen oda tipleri:\n{room_lines}")
    lines.append("2 oda konaklamayı kabul ediyor musunuz ve oda dağılımınız nasıl olsun?")

    return LLMResponse(
        user_message="\n\n".join(lines),
        internal_json=InternalJSON(
            language="tr",
            intent="stay_availability",
            state="NEEDS_VERIFICATION",
            entities=entities,
            required_questions=["Oda dağılım tercihiniz nedir? (3+3, 4+2 vb.)"],
            handoff={"needed": False, "reason": None},
            next_step="collect_room_split_then_quote",
        ),
    )


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


def _build_child_quote_handoff_response(
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
) -> LLMResponse:
    """Create a deterministic fallback when PMS ignores requested child occupancy."""
    entities = _extract_requested_occupancy(executed_calls)
    if _requires_multi_room_split(hotel_id, entities):
        return _build_room_split_verification_response(hotel_id, executed_calls)
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


def _is_elevator_question(user_text: str) -> bool:
    """Return True when the guest asks whether the hotel has an elevator/lift."""
    normalized = user_text.casefold()
    keywords = (
        "asansör",
        "asansor",
        "elevator",
        "lift",
        "лифт",
    )
    return any(_contains_keyword(normalized, keyword) for keyword in keywords)


def _contains_keyword(text: str, keyword: str) -> bool:
    """Match single words by boundary and phrases by substring."""
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def _normalize_language_text(text: str) -> str:
    """Normalize free text for lightweight language hint matching."""
    folded = text.casefold().strip().replace("ı", "i")
    decomposed = unicodedata.normalize("NFKD", folded)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(stripped.split())


def _detect_message_language(text: str, fallback: str = "tr") -> str:
    """Detect guest message language with lightweight heuristics."""
    normalized = _normalize_language_text(text)
    if not normalized:
        return fallback if fallback in SUPPORTED_LANGUAGE_CODES else "tr"

    for pattern, language_code in SCRIPT_LANGUAGE_PATTERNS:
        if pattern.search(text):
            return language_code

    scores = {
        language_code: sum(1 for keyword in keywords if _contains_keyword(normalized, keyword))
        for language_code, keywords in LANGUAGE_HINTS.items()
    }
    if re.search(r"[çğış]", text.casefold()):
        scores["tr"] += 2

    best_language = max(scores, key=lambda language_code: scores[language_code])
    best_score = scores[best_language]
    if best_score > 0:
        top_languages = [language_code for language_code, score in scores.items() if score == best_score]
        if len(top_languages) == 1:
            return best_language
    if fallback in SUPPORTED_LANGUAGE_CODES:
        return fallback
    return "tr"


def _build_elevator_reply(hotel_id: int, language: str) -> str:
    """Build deterministic elevator reply from HOTEL_PROFILE accessibility policy."""
    language_code = language if language in {"tr", "en", "ru"} else "en"
    profile = get_profile(hotel_id)
    if profile is not None:
        accessibility = profile.facility_policies.get("accessibility", {})
        reply = accessibility.get(f"reply_{language_code}")
        if isinstance(reply, str) and reply.strip():
            return reply.strip()

        elevator_available = accessibility.get("elevator_available")
        if isinstance(elevator_available, bool):
            if language_code == "tr":
                return (
                    "Evet, otelimizde asansör bulunmaktadır."
                    if elevator_available
                    else "Otelimizde asansör bulunmamaktadır."
                )
            if language_code == "ru":
                return (
                    "Да, в нашем отеле есть лифт."
                    if elevator_available
                    else "В нашем отеле лифта нет."
                )
            return (
                "Yes, our hotel has an elevator."
                if elevator_available
                else "Our hotel does not have an elevator."
            )

    if language_code == "tr":
        return "Asansör bilgisi için hızlıca kontrol edip size net bilgi paylaşayım."
    if language_code == "ru":
        return "Сейчас быстро уточню информацию по лифту и вернусь к вам с точным ответом."
    return "I will quickly verify the elevator information and get back to you with the exact answer."


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


def _decimal_from_value(value: Any) -> Decimal:
    """Convert arbitrary numeric payload values into Decimal safely."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _round_price_for_display(value: Any) -> int:
    """Round prices to the nearest 5 units for guest-facing display."""
    amount = _decimal_from_value(value)
    rounded = (amount / PRICE_ROUNDING_INCREMENT).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(rounded * PRICE_ROUNDING_INCREMENT)


def _profile_rate_type_id(profile: Any, policy_key: str) -> int:
    """Read configured PMS rate_type_id for a cancellation policy."""
    if profile is None:
        return 0
    mapping = getattr(profile, "rate_mapping", {}).get(policy_key)
    return int(getattr(mapping, "rate_type_id", 0) or 0)


def _resolve_quote_policy_key(offer: dict[str, Any], profile: Any) -> str | None:
    """Map an Elektra offer row to FREE_CANCEL or NON_REFUNDABLE."""
    rate_type_id = int(offer.get("rate_type_id", 0) or 0)
    free_cancel_rate_type_id = _profile_rate_type_id(profile, "FREE_CANCEL")
    non_refundable_rate_type_id = _profile_rate_type_id(profile, "NON_REFUNDABLE")
    normalized_rate = _canonical_text(str(offer.get("rate_type") or ""))
    cancel_possible = bool(offer.get("cancel_possible"))

    if rate_type_id and rate_type_id == free_cancel_rate_type_id:
        return "FREE_CANCEL"
    if rate_type_id and rate_type_id == non_refundable_rate_type_id:
        return "NON_REFUNDABLE"
    if normalized_rate in {"ucretsiziptal", "freecancel"} or cancel_possible:
        return "FREE_CANCEL"
    if normalized_rate in {"iptaledilemez", "iadeyapilmaz", "nonrefundable"}:
        return "NON_REFUNDABLE"
    return None


def _find_profile_room(profile: Any, offer: dict[str, Any]) -> Any | None:
    """Resolve a live PMS offer row to the configured hotel profile room."""
    if profile is None:
        return None

    room_type_id = int(offer.get("room_type_id", 0) or 0)
    for room in getattr(profile, "room_types", []):
        if room_type_id and int(getattr(room, "pms_room_type_id", 0) or 0) == room_type_id:
            return room

    offer_name = _canonical_text(str(offer.get("room_type") or ""))
    for room in getattr(profile, "room_types", []):
        localized_name = getattr(room, "name", None)
        candidates = {
            _canonical_text(getattr(localized_name, "tr", "")),
            _canonical_text(getattr(localized_name, "en", "")),
        }
        if any(
            candidate and (offer_name == candidate or offer_name in candidate or candidate in offer_name)
            for candidate in candidates
        ):
            return room
    return None


def _display_room_name(profile_room: Any | None, offer: dict[str, Any]) -> str:
    """Build the Turkish room label expected in guest-facing quote replies."""
    localized_name = getattr(profile_room, "name", None)
    base_name = str(
        getattr(localized_name, "tr", "")
        or offer.get("room_type")
        or ""
    ).strip()
    normalized_name = _canonical_text(base_name)
    mapped_names = {
        "deluxe": "Deluxe",
        "superior": "Superior",
        "exclusiveland": "Exclusive Sokak Manzaralı",
        "exclusivepool": "Exclusive Havuz Manzaralı",
        "penthouseland": "Penthouse Land - Jakuzili",
        "penthouse": "Penthouse - Jakuzili",
        "premium": "Premium - Jakuzili",
    }
    if normalized_name in mapped_names:
        return mapped_names[normalized_name]
    return base_name.title() if base_name else "Oda"


def _resolve_room_size(profile_room: Any | None, offer: dict[str, Any]) -> int | None:
    """Return room size using profile data first and PMS payload as fallback."""
    profile_size = int(getattr(profile_room, "size_m2", 0) or 0)
    if profile_size > 0:
        return profile_size
    offer_size = int(offer.get("room_area", 0) or 0)
    return offer_size or None


def _format_offer_price(offer: dict[str, Any]) -> str:
    """Format a single offer price for guest display."""
    price_value = offer.get("discounted_price")
    if price_value in (None, "", 0, "0"):
        price_value = offer.get("price", 0)
    rounded_amount = _round_price_for_display(price_value)
    currency_code = str(offer.get("currency_code") or offer.get("currency") or "EUR").upper()
    if currency_code == "EUR":
        return f"{rounded_amount} €"
    return f"{rounded_amount} {currency_code}"


def _occupancy_label(adults: int, children: int) -> str:
    """Render Turkish occupancy label."""
    label = f"{adults} yetişkin"
    if children > 0:
        label = f"{label} + {children} çocuk"
    return label


def _quote_group_key(arguments: dict[str, Any]) -> tuple[Any, ...]:
    """Build stable grouping key for quote payloads by occupancy/date."""
    raw_ages = arguments.get("chd_ages")
    ages: tuple[int, ...] = ()
    if isinstance(raw_ages, list):
        normalized = [_to_int(age, -1) for age in raw_ages]
        ages = tuple(age for age in normalized if age >= 0)
    return (
        str(arguments.get("checkin_date") or "").strip(),
        str(arguments.get("checkout_date") or "").strip(),
        _to_int(arguments.get("adults"), 0),
        _to_int(arguments.get("chd_count"), len(ages)),
        ages,
    )


def _group_quote_payloads(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge quote payloads that belong to the same room occupancy/date request."""
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for payload in payloads:
        arguments = payload.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}
        key = _quote_group_key(arguments)
        bucket = grouped.setdefault(
            key,
            {
                "arguments": arguments,
                "offers": [],
            },
        )
        offers = payload.get("offers")
        if isinstance(offers, list):
            bucket["offers"].extend(offer for offer in offers if isinstance(offer, dict))
    return list(grouped.values())


def _night_count_from_args(arguments: dict[str, Any]) -> int:
    """Compute stay night count from quote arguments."""
    checkin = str(arguments.get("checkin_date") or "").strip()
    checkout = str(arguments.get("checkout_date") or "").strip()
    try:
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
    except ValueError:
        return 0
    return max((checkout_date - checkin_date).days, 0)


def _build_offer_blocks_for_payload(
    offers_for_call: list[dict[str, Any]],
    profile: Any | None,
    room_order: dict[int, int],
) -> str | None:
    """Build deterministic room blocks from merged quote offers."""
    grouped_offers: dict[Any, dict[str, Any]] = {}
    for offer in offers_for_call:
        policy_key = _resolve_quote_policy_key(offer, profile)
        if policy_key is None:
            continue

        profile_room = _find_profile_room(profile, offer)
        room_key = int(offer.get("room_type_id", 0) or 0) or _canonical_text(str(offer.get("room_type") or ""))
        bucket = grouped_offers.setdefault(
            room_key,
            {"profile_room": profile_room, "offers": {}, "sample_offer": offer},
        )
        if bucket["profile_room"] is None and profile_room is not None:
            bucket["profile_room"] = profile_room

        current_offer = bucket["offers"].get(policy_key)
        if current_offer is None or (
            _decimal_from_value(offer.get("price"))
            < _decimal_from_value(current_offer.get("price"))
        ):
            bucket["offers"][policy_key] = offer
            bucket["sample_offer"] = offer

    if not grouped_offers:
        return None

    ordered_groups = sorted(
        grouped_offers.values(),
        key=lambda group: (
            room_order.get(int(group["sample_offer"].get("room_type_id", 0) or 0), 9999),
            _display_room_name(group.get("profile_room"), group["sample_offer"]),
        ),
    )

    blocks: list[str] = []
    for group in ordered_groups:
        sample_offer = group["sample_offer"]
        profile_room = group.get("profile_room")
        size_m2 = _resolve_room_size(profile_room, sample_offer)
        header = _display_room_name(profile_room, sample_offer)
        if size_m2 is not None:
            header = f"{header} ({size_m2}m2)"

        room_lines = [header]
        non_refundable_offer = group["offers"].get("NON_REFUNDABLE")
        free_cancel_offer = group["offers"].get("FREE_CANCEL")
        if non_refundable_offer is not None:
            room_lines.append(f"İptal edilemez: {_format_offer_price(non_refundable_offer)}")
        if free_cancel_offer is not None:
            room_lines.append(f"Ücretsiz İptal: {_format_offer_price(free_cancel_offer)}")
        if len(room_lines) > 1:
            blocks.append("\n".join(room_lines))

    if not blocks:
        return None
    return "\n\n".join(blocks)


def _build_stay_quote_message_for_payload(
    payload: dict[str, Any],
    profile: Any | None,
    room_order: dict[int, int],
    room_header: str | None = None,
) -> str | None:
    """Build one Turkish customer-facing quote message for one room occupancy."""
    arguments_raw = payload.get("arguments")
    arguments: dict[str, Any] = cast(dict[str, Any], arguments_raw) if isinstance(arguments_raw, dict) else {}
    offers = payload.get("offers")
    if not isinstance(offers, list):
        return None
    offer_blocks = _build_offer_blocks_for_payload(offers, profile=profile, room_order=room_order)
    if not offer_blocks:
        return None

    checkin = str(arguments.get("checkin_date") or "").strip()
    checkout = str(arguments.get("checkout_date") or "").strip()
    nights = _night_count_from_args(arguments)
    adults = _to_int(arguments.get("adults"), 0)
    children = _to_int(arguments.get("chd_count"), 0)

    lines: list[str] = []
    if room_header:
        lines.append(room_header)
        lines.append("")
    lines.append("Otelimize göstermiş olduğunuz ilgi için teşekkür ederiz.")
    lines.append("")
    if checkin and checkout and nights > 0 and adults > 0:
        lines.append(f"{checkin} - {checkout} tarihleri arasında {nights} gece")
        lines.append(f"kahvaltı dahil {_occupancy_label(adults, children)} fiyatlarımız aşağıdaki gibidir;")
        lines.append("")
    lines.append(offer_blocks)
    return "\n".join(lines).strip()


def _build_deterministic_turkish_stay_quote_messages(
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
) -> list[str]:
    """Format Turkish quote replies as one or multiple customer messages."""
    payloads = _extract_quote_call_payloads(executed_calls)
    if not payloads:
        offers = _extract_quote_offers(executed_calls)
        if not offers:
            return []
        payloads = [{"arguments": {}, "offers": offers}]
    available_room_type_ids = _extract_available_room_type_ids(executed_calls)
    payloads = _filter_quote_payloads_by_available_room_types(payloads, available_room_type_ids)
    if not payloads and available_room_type_ids:
        return [TR_NO_AVAILABLE_ROOM_FOR_QUOTE]
    grouped_payloads = _group_quote_payloads(payloads)

    profile = get_profile(hotel_id)
    room_order: dict[int, int] = {}
    if profile is not None:
        room_order = {
            int(getattr(room, "pms_room_type_id", 0) or 0): index
            for index, room in enumerate(getattr(profile, "room_types", []))
        }

    if len(grouped_payloads) == 1:
        single_message = _build_stay_quote_message_for_payload(
            grouped_payloads[0],
            profile=profile,
            room_order=room_order,
        )
        return [single_message] if single_message else []

    messages: list[str] = []
    for index, payload in enumerate(grouped_payloads, start=1):
        message = _build_stay_quote_message_for_payload(
            payload,
            profile=profile,
            room_order=room_order,
            room_header=f"{index}. Oda",
        )
        if message:
            messages.append(message)
    return messages


def _build_deterministic_turkish_stay_quote_reply(
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
) -> str | None:
    """Return the first deterministic Turkish quote message for compatibility."""
    messages = _build_deterministic_turkish_stay_quote_messages(hotel_id, executed_calls)
    if not messages:
        return None
    return messages[0]


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


def _booking_quote_failed_or_empty(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when the latest booking_quote attempt failed or returned no offers."""
    for call in reversed(executed_calls):
        if str(call.get("name") or "") != "booking_quote":
            continue
        result = _loads_tool_payload(call.get("result"))
        if result.get("error"):
            return True
        offers = result.get("offers")
        return not isinstance(offers, list) or not offers
    return False


def _guest_explicitly_referenced_year(user_text: str) -> bool:
    """Return True when guest explicitly asks/mentions year context."""
    if EXPLICIT_YEAR_PATTERN.search(user_text):
        return True
    return YEAR_KEYWORD_PATTERN.search(user_text) is not None


def _contains_year_clarification(text: str) -> bool:
    """Detect follow-up prompts that ask only year clarification."""
    if not text:
        return False
    lowered = text.casefold()
    if EXPLICIT_YEAR_PATTERN.search(lowered):
        return True
    return YEAR_KEYWORD_PATTERN.search(lowered) is not None


def _suppress_default_year_question(
    response: LLMResponse,
    user_text: str,
) -> None:
    """Remove default year clarification prompts unless guest explicitly requested year context."""
    intent = str(response.internal_json.intent or "").lower()
    if intent != "stay_quote":
        return
    if _guest_explicitly_referenced_year(user_text):
        return

    original_required = [
        str(item).strip()
        for item in response.internal_json.required_questions
        if isinstance(item, str) and str(item).strip()
    ]
    filtered_required = [question for question in original_required if not _contains_year_clarification(question)]
    response.internal_json.required_questions = filtered_required

    current_message = str(response.user_message or "").strip()
    if _contains_year_clarification(current_message):
        if filtered_required:
            language = str(response.internal_json.language or "tr").lower()
            response.user_message = _single_field_prompt(language, filtered_required[0])
            return
        response.user_message = (
            "Tarih aralığı ve kişi sayısını netleştirirseniz fiyatı hemen kontrol edebilirim."
        )


def _price_unavailable_message(language: str) -> str:
    """Build user-facing fallback when live quote cannot be retrieved from PMS."""
    if language == "en":
        return (
            "I cannot retrieve a live room rate from the PMS right now. "
            "If you want, I can forward your request to our team and share the confirmed price as soon as possible."
        )
    if language == "ru":
        return (
            "Сейчас не удаётся получить актуальную цену из PMS. "
            "При желании передам ваш запрос команде и мы сообщим подтверждённую стоимость как можно скорее."
        )
    return (
        "Şu an PMS üzerinden canlı fiyat çekemiyorum. "
        "İsterseniz talebinizi ekibe iletip net fiyatı en kısa sürede paylaşalım."
    )


def _executed_stay_hold_submission(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when stay hold + approval flow has been triggered."""
    saw_stay_hold = False
    saw_approval = False

    for call in executed_calls:
        name = str(call.get("name") or "")
        if name == "approval_request":
            saw_approval = True
            continue
        if name != "stay_create_hold":
            continue

        saw_stay_hold = True
        result = _loads_tool_payload(call.get("result"))
        approval_request_id = str(result.get("approval_request_id") or "").strip()
        if approval_request_id:
            saw_approval = True

    return saw_stay_hold and saw_approval


def _extract_user_message_parts(response: LLMResponse) -> list[str]:
    """Extract one or many outbound user messages from response payload."""
    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    raw_parts = entities.get("user_message_parts")
    if isinstance(raw_parts, list):
        parts = [str(item).strip() for item in raw_parts if isinstance(item, str) and item.strip()]
        if parts:
            return parts
    default_message = str(response.user_message or "").strip()
    return [default_message] if default_message else []


def _canonical_required_question_key(question: str) -> str:
    """Map free-form required question labels to a canonical field key."""
    normalized = _canonical_text(question)
    if any(token in normalized for token in ("checkin", "giris")):
        return "checkin_date"
    if any(token in normalized for token in ("checkout", "cikis")):
        return "checkout_date"
    if any(token in normalized for token in ("adult", "yetiskin", "kisicount", "kis sayisi", "pax")):
        return "adults"
    if any(token in normalized for token in ("chd", "cocuk", "child", "yas", "age")):
        return "chd_ages"
    if any(token in normalized for token in ("guestname", "fullname", "adsoyad", "isim")):
        return "guest_name"
    if "phone" in normalized or "telefon" in normalized:
        return "phone"
    if "email" in normalized or "eposta" in normalized:
        return "email"
    if any(token in normalized for token in ("cancelpolicy", "iptal", "refund")):
        return "cancel_policy_type"
    if "roomdistribution" in normalized or "odadagilim" in normalized:
        return "room_distribution"
    if any(token in normalized for token in ("route", "guzergah", "nereden", "nereye")):
        return "route"
    if "date" in normalized or "tarih" in normalized:
        return "date"
    if "time" in normalized or "saat" in normalized:
        return "time"
    if any(token in normalized for token in ("party", "paxcount", "kisisayisi")):
        return "party_size"
    if any(token in normalized for token in ("notes", "not", "specialrequest", "ozelistek")):
        return "notes"
    return question.strip()


def _single_field_prompt(language: str, required_question: str) -> str:
    """Build one-step follow-up prompt for a single missing reservation field."""
    key = _canonical_required_question_key(required_question)
    prompts = {
        "tr": {
            "checkin_date": "Rezervasyon için önce giriş tarihinizi paylaşır mısınız? (GG.AA.YYYY)",
            "checkout_date": "Çıkış tarihinizi paylaşır mısınız? (GG.AA.YYYY)",
            "adults": "Kaç yetişkin konaklayacaksınız?",
            "chd_ages": "Çocuk varsa yaşlarını tek tek paylaşır mısınız? (ör. 4, 9)",
            "guest_name": "Rezervasyon için ad soyad bilginizi paylaşır mısınız?",
            "phone": "İletişim için telefon numaranızı paylaşır mısınız? (+90 ile)",
            "email": "E-posta adresinizi paylaşır mısınız? (opsiyonel)",
            "cancel_policy_type": "Hangi iptal politikasıyla devam edelim: İptal edilemez mi, Ücretsiz İptal mi?",
            "room_distribution": "Oda dağılımını nasıl planlayalım? (ör. 3+3 veya 4+2)",
            "route": "Transfer için güzergâhı paylaşır mısınız? (nereden -> nereye)",
            "date": "Rezervasyon tarihi nedir?",
            "time": "Saat bilgisini paylaşır mısınız?",
            "party_size": "Kaç kişi için rezervasyon yapalım?",
            "notes": "Eklemek istediğiniz özel bir not var mı?",
        },
        "en": {
            "checkin_date": "Please share your check-in date first. (DD.MM.YYYY)",
            "checkout_date": "Please share your check-out date. (DD.MM.YYYY)",
            "adults": "How many adults will stay?",
            "chd_ages": "If there are children, please share each age. (e.g. 4, 9)",
            "guest_name": "Please share the full name for the reservation.",
            "phone": "Please share your phone number for contact. (+country code)",
            "email": "Please share your email address. (optional)",
            "cancel_policy_type": "Which cancellation policy do you prefer: Non-refundable or Free Cancellation?",
            "room_distribution": "How would you like to split the rooms? (e.g. 3+3 or 4+2)",
            "route": "Please share the transfer route. (from -> to)",
            "date": "What is the reservation date?",
            "time": "Please share the preferred time.",
            "party_size": "How many guests should I reserve for?",
            "notes": "Any special note you would like to add?",
        },
        "ru": {
            "checkin_date": "Пожалуйста, сначала укажите дату заезда. (ДД.ММ.ГГГГ)",
            "checkout_date": "Пожалуйста, укажите дату выезда. (ДД.ММ.ГГГГ)",
            "adults": "Сколько взрослых будет проживать?",
            "chd_ages": "Если есть дети, укажите возраст каждого. (например, 4, 9)",
            "guest_name": "Пожалуйста, укажите имя и фамилию для бронирования.",
            "phone": "Пожалуйста, укажите ваш номер телефона для связи.",
            "email": "Пожалуйста, укажите ваш e-mail. (необязательно)",
            "cancel_policy_type": "Какой вариант отмены предпочитаете: невозвратный или бесплатная отмена?",
            "room_distribution": "Как разделим размещение по комнатам? (например, 3+3 или 4+2)",
            "route": "Пожалуйста, укажите маршрут трансфера. (откуда -> куда)",
            "date": "Какая дата бронирования?",
            "time": "Пожалуйста, укажите время.",
            "party_size": "На сколько гостей оформить бронь?",
            "notes": "Есть ли особые пожелания?",
        },
    }
    language_code = language if language in prompts else "tr"
    prompt = prompts[language_code].get(key)
    if prompt:
        return prompt
    if language_code == "en":
        return f"Please share this detail so I can continue: {required_question}"
    if language_code == "ru":
        return f"Пожалуйста, уточните эту информацию, чтобы я продолжил(а): {required_question}"
    return f"Devam edebilmem için şu bilgiyi paylaşır mısınız: {required_question}"


def _enforce_single_step_collection(response: LLMResponse) -> None:
    """Force reservation verification to collect one field at a time."""
    state = str(response.internal_json.state or "").upper()
    if state != "NEEDS_VERIFICATION":
        return

    intent = str(response.internal_json.intent or "").lower().strip()
    if not any(intent.startswith(prefix) for prefix in ("stay_", "restaurant_", "transfer_")):
        return

    required = [
        str(item).strip()
        for item in response.internal_json.required_questions
        if isinstance(item, str) and str(item).strip()
    ]
    if not required:
        return

    first_required = required[0]
    response.internal_json.required_questions = [first_required]
    if len(required) > 1 or not str(response.user_message or "").strip():
        language = str(response.internal_json.language or "tr").lower()
        response.user_message = _single_field_prompt(language, first_required)


def _to_int(value: Any, default: int = 0) -> int:
    """Convert arbitrary values into int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_cancel_policy(value: Any) -> str:
    """Normalize cancellation policy to FREE_CANCEL or NON_REFUNDABLE."""
    normalized = _canonical_text(str(value or ""))
    if normalized in {"nonrefundable", "iptaledilemez", "iadeyapilmaz"}:
        return "NON_REFUNDABLE"
    if normalized in {"freecancel", "ucretsiziptal"}:
        return "FREE_CANCEL"
    return "FREE_CANCEL"


def _should_auto_submit_stay_hold(internal_json: InternalJSON) -> bool:
    """Return True when parsed response indicates stay hold must be submitted now."""
    if str(internal_json.intent or "").lower() != "stay_booking_create":
        return False

    state = str(internal_json.state or "").upper()
    if state not in {"READY_FOR_TOOL", "NEEDS_CONFIRMATION", "PENDING_APPROVAL"}:
        return False

    parsed_tool_calls = ResponseParser.extract_tool_calls(internal_json)
    tool_names = {
        str(item.get("name") or "").strip()
        for item in parsed_tool_calls
        if isinstance(item, dict)
    }
    if state in {"READY_FOR_TOOL", "PENDING_APPROVAL"} and (
        "stay_create_hold" in tool_names or "approval_request" in tool_names
    ):
        return True

    next_step = _canonical_text(str(internal_json.next_step or ""))
    if not next_step:
        return state == "READY_FOR_TOOL"
    if "createstayhold" in next_step and ("approval" in next_step or "onay" in next_step):
        return True
    if next_step in {"adminapprovalwait", "awaitadminapproval"}:
        return True
    if "adminapproval" in next_step or "adminonay" in next_step:
        return True
    return state == "READY_FOR_TOOL"


def _resolve_requested_room_type_id(entities: dict[str, Any], profile: Any | None) -> int:
    """Resolve requested room type id to PMS room_type_id when possible."""
    room_id = _to_int(entities.get("room_type_id"), 0)
    if room_id > 0 and profile is not None:
        for room in getattr(profile, "room_types", []):
            profile_room_id = _to_int(getattr(room, "id", 0), 0)
            pms_room_id = _to_int(getattr(room, "pms_room_type_id", 0), 0)
            if room_id == pms_room_id and pms_room_id > 0:
                return pms_room_id
            if room_id == profile_room_id and pms_room_id > 0:
                return pms_room_id
    if room_id > 0:
        return room_id

    requested_name = _canonical_text(str(entities.get("room_type") or entities.get("room_name") or ""))
    if not requested_name or profile is None:
        return 0

    for room in getattr(profile, "room_types", []):
        localized_name = getattr(room, "name", None)
        candidates = (
            _canonical_text(str(getattr(localized_name, "tr", ""))),
            _canonical_text(str(getattr(localized_name, "en", ""))),
        )
        if requested_name not in candidates:
            continue
        return _to_int(getattr(room, "pms_room_type_id", 0), 0)
    return 0


def _select_offer_for_stay_hold(
    offers: list[dict[str, Any]],
    requested_room_type_id: int,
    cancel_policy_type: str,
    profile: Any | None,
) -> dict[str, Any] | None:
    """Pick the best matching quote offer for hold creation."""
    if not offers:
        return None

    def _matches(offer: dict[str, Any], *, check_room: bool, check_policy: bool) -> bool:
        if (
            check_room
            and requested_room_type_id > 0
            and _to_int(offer.get("room_type_id"), 0) != requested_room_type_id
        ):
            return False
        if check_policy:
            resolved = _resolve_quote_policy_key(offer, profile)
            if resolved and resolved != cancel_policy_type:
                return False
        return True

    candidate_sets = (
        [offer for offer in offers if _matches(offer, check_room=True, check_policy=True)],
        [offer for offer in offers if _matches(offer, check_room=True, check_policy=False)],
        [offer for offer in offers if _matches(offer, check_room=False, check_policy=True)],
        list(offers),
    )
    for candidates in candidate_sets:
        if not candidates:
            continue
        return min(
            candidates,
            key=lambda offer: (
                _decimal_from_value(offer.get("discounted_price", offer.get("price", 0))),
                _to_int(offer.get("room_type_id"), 0),
            ),
        )
    return None


def _build_stay_draft_from_offer(
    entities: dict[str, Any],
    offer: dict[str, Any],
    cancel_policy_type: str,
) -> dict[str, Any] | None:
    """Build stay_create_hold draft payload from entities and selected quote offer."""
    checkin_date = str(entities.get("checkin_date") or "").strip()
    checkout_date = str(entities.get("checkout_date") or "").strip()
    guest_name = str(entities.get("guest_name") or "").strip()
    phone = str(entities.get("phone") or "").strip()
    adults = _to_int(entities.get("adults"), 0)
    room_type_id = _to_int(offer.get("room_type_id"), 0)
    board_type_id = _to_int(offer.get("board_type_id", entities.get("board_type_id", 0)), 0)
    rate_type_id = _to_int(offer.get("rate_type_id"), 0)
    rate_code_id = _to_int(offer.get("rate_code_id"), 0)
    if (
        not checkin_date
        or not checkout_date
        or not guest_name
        or not phone
        or adults <= 0
        or room_type_id <= 0
        or board_type_id <= 0
        or rate_type_id <= 0
        or rate_code_id <= 0
    ):
        return None

    total_price = _decimal_from_value(offer.get("discounted_price", offer.get("price", 0)))
    if total_price <= 0:
        total_price = _decimal_from_value(offer.get("price", 0))
    if total_price <= 0:
        return None

    chd_ages: list[int] = []
    raw_chd_ages = entities.get("chd_ages")
    if isinstance(raw_chd_ages, list):
        for age in raw_chd_ages:
            normalized_age = _to_int(age, -1)
            if normalized_age >= 0:
                chd_ages.append(normalized_age)

    draft: dict[str, Any] = {
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "room_type_id": room_type_id,
        "board_type_id": board_type_id,
        "rate_type_id": rate_type_id,
        "rate_code_id": rate_code_id,
        "price_agency_id": offer.get("price_agency_id"),
        "currency_display": str(offer.get("currency_code") or entities.get("currency") or "EUR").upper(),
        "total_price_eur": float(total_price),
        "adults": adults,
        "chd_ages": chd_ages,
        "guest_name": guest_name,
        "phone": phone,
        "email": entities.get("email"),
        "nationality": str(entities.get("nationality") or "TR").upper(),
        "cancel_policy_type": cancel_policy_type,
        "notes": entities.get("notes"),
    }
    return draft


async def _auto_submit_stay_hold(
    conversation: Conversation,
    entities: dict[str, Any],
    language: str,
    dispatcher: Any,
) -> list[dict[str, Any]]:
    """Fallback: create stay hold deterministically when LLM skips tool calls."""
    profile = get_profile(conversation.hotel_id)
    requested_room_type_id = _resolve_requested_room_type_id(entities, profile)
    if requested_room_type_id <= 0:
        return []

    checkin_date = str(entities.get("checkin_date") or "").strip()
    checkout_date = str(entities.get("checkout_date") or "").strip()
    adults = _to_int(entities.get("adults"), 0)
    if not checkin_date or not checkout_date or adults <= 0:
        return []

    cancel_policy_type = _normalize_cancel_policy(entities.get("cancel_policy_type"))
    quote_language = str(entities.get("language") or language or "tr").upper()
    if quote_language not in {"TR", "EN"}:
        quote_language = "TR"

    quote_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults": adults,
        "chd_count": _to_int(entities.get("chd_count"), 0),
        "chd_ages": entities.get("chd_ages") if isinstance(entities.get("chd_ages"), list) else [],
        "currency": str(entities.get("currency") or "EUR").upper(),
        "language": quote_language,
        "nationality": str(entities.get("nationality") or "TR").upper(),
        "cancel_policy_type": cancel_policy_type,
    }
    quote_result = await dispatcher.dispatch("booking_quote", **quote_args)
    if not isinstance(quote_result, dict) or quote_result.get("error"):
        logger.warning("stay_hold_auto_submit_quote_failed")
        return []

    offers = quote_result.get("offers")
    if not isinstance(offers, list):
        return []
    parsed_offers = [offer for offer in offers if isinstance(offer, dict)]
    selected_offer = _select_offer_for_stay_hold(
        parsed_offers,
        requested_room_type_id=requested_room_type_id,
        cancel_policy_type=cancel_policy_type,
        profile=profile,
    )
    if selected_offer is None:
        return []

    draft = _build_stay_draft_from_offer(entities, selected_offer, cancel_policy_type)
    if draft is None:
        return []

    hold_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "draft": draft,
    }
    if conversation.id is not None:
        hold_args["conversation_id"] = str(conversation.id)

    hold_result = await dispatcher.dispatch("stay_create_hold", **hold_args)
    if not isinstance(hold_result, dict) or hold_result.get("error"):
        logger.warning("stay_hold_auto_submit_create_failed")
        return []

    fallback_calls: list[dict[str, Any]] = [
        {"name": "booking_quote", "arguments": quote_args, "result": quote_result},
        {"name": "stay_create_hold", "arguments": hold_args, "result": hold_result},
    ]
    approval_request_id = str(hold_result.get("approval_request_id") or "").strip()
    if approval_request_id:
        fallback_calls.append(
            {
                "name": "approval_request",
                "arguments": {
                    "hotel_id": conversation.hotel_id,
                    "approval_type": "STAY",
                    "reference_id": str(hold_result.get("stay_hold_id") or ""),
                    "required_roles": ["ADMIN"],
                },
                "result": {
                    "approval_request_id": approval_request_id,
                    "status": hold_result.get("approval_status", "REQUESTED"),
                },
            }
        )

    logger.info(
        "stay_hold_auto_submitted",
        hold_id=hold_result.get("stay_hold_id"),
        approval_request_id=approval_request_id or None,
    )
    return fallback_calls


async def _run_message_pipeline(
    conversation: Conversation,
    normalized_text: str,
    dispatcher: Any | None = None,
    expected_language: str | None = None,
) -> LLMResponse:
    """Run message pipeline and return structured LLM response."""
    target_language = (
        expected_language
        if expected_language in SUPPORTED_LANGUAGE_CODES
        else conversation.language if conversation.language in SUPPORTED_LANGUAGE_CODES else "tr"
    )
    if PAYMENT_DATA_PATTERN.search(normalized_text):
        return LLMResponse(
            user_message=_payment_warning_message(target_language),
            internal_json=InternalJSON(
                language=target_language,
                intent="payment_inquiry",
                state="HANDOFF",
                risk_flags=["PAYMENT_CONFUSION"],
                next_step="handoff_to_sales",
            ),
        )

    payment_intake_response = _build_payment_intake_response(
        conversation=conversation,
        normalized_text=normalized_text,
        target_language=target_language,
    )
    if payment_intake_response is not None:
        return payment_intake_response

    try:
        prompt_builder = get_prompt_builder()
        llm_client = get_llm_client()
        messages = prompt_builder.build_messages(conversation, normalized_text)
        tools = get_tool_definitions()
        if dispatcher is not None:
            tool_executor = _build_dispatcher_executor(dispatcher, conversation)
        else:
            async def _unavailable_executor(tool_name: str, _tool_args: str | dict[str, Any]) -> str:
                logger.warning("tool_dispatcher_unavailable", tool_name=tool_name)
                return orjson.dumps({"error": "TOOL_DISPATCHER_UNAVAILABLE", "tool": tool_name}).decode()

            tool_executor = _unavailable_executor

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
            return _build_child_quote_handoff_response(conversation.hotel_id, executed_calls)

        parsed = ResponseParser.parse(content)
        intent = str(parsed.internal_json.intent or "").lower()
        language = (
            target_language
            if target_language in SUPPORTED_LANGUAGE_CODES
            else str(parsed.internal_json.language or "tr").lower()
        )
        parsed.internal_json.language = language
        _suppress_default_year_question(parsed, normalized_text)
        entities = parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else {}
        if _is_elevator_question(normalized_text):
            parsed.user_message = _build_elevator_reply(conversation.hotel_id, language)
            return parsed
        if language == "tr" and _is_payment_method_question(normalized_text):
            parsed.user_message = _build_turkish_payment_methods_reply(conversation.hotel_id)
            return parsed
        if language == "tr" and _is_parking_question(normalized_text):
            parsed.user_message = _build_turkish_parking_reply(conversation.hotel_id)
            return parsed
        if language == "tr" and _is_child_bedding_question(normalized_text, entities):
            parsed.user_message = _build_turkish_child_bedding_reply(conversation.hotel_id, entities)
            return parsed
        if (
            dispatcher is not None
            and not _executed_stay_hold_submission(executed_calls)
            and _should_auto_submit_stay_hold(parsed.internal_json)
        ):
            fallback_calls = await _auto_submit_stay_hold(
                conversation=conversation,
                entities=entities,
                language=language,
                dispatcher=dispatcher,
            )
            if fallback_calls:
                executed_calls.extend(fallback_calls)
            else:
                logger.warning(
                    "stay_hold_submission_missing_after_pending_approval",
                    conversation_id=str(conversation.id) if conversation.id is not None else None,
                    state=str(parsed.internal_json.state or ""),
                    next_step=str(parsed.internal_json.next_step or ""),
                )
                return LLMResponse(
                    user_message=(
                        "Talebinizi aldik ancak rezervasyon kaydini teknik olarak tamamlayamadik. "
                        "Ekibimiz sizi manuel olarak en kisa surede bilgilendirecektir."
                    ),
                    internal_json=InternalJSON(
                        language=language,
                        intent="stay_booking_create",
                        state="HANDOFF",
                        entities=entities,
                        required_questions=[],
                        handoff={"needed": True, "reason": "stay_hold_submission_failed"},
                        risk_flags=["TOOL_ERROR_REPEAT"],
                        next_step="manual_review_required",
                    ),
                )
        if intent == "stay_quote" and _booking_quote_failed_or_empty(executed_calls):
            risk_flags = list(parsed.internal_json.risk_flags or [])
            if "TOOL_UNAVAILABLE" not in risk_flags:
                risk_flags.append("TOOL_UNAVAILABLE")
            parsed.user_message = _price_unavailable_message(language)
            parsed.internal_json.state = "HANDOFF"
            parsed.internal_json.required_questions = []
            parsed.internal_json.handoff = {"needed": True, "reason": "live_price_unavailable"}
            parsed.internal_json.risk_flags = risk_flags
            parsed.internal_json.next_step = "handoff_to_live_price_team"
            return parsed
        if intent == "stay_quote" and language == "tr" and _executed_booking_quote(executed_calls):
            deterministic_messages = _build_deterministic_turkish_stay_quote_messages(
                conversation.hotel_id,
                executed_calls,
            )
            if deterministic_messages:
                normalized_messages = [
                    _normalize_turkish_stay_quote_reply(message, normalized_text)
                    for message in deterministic_messages
                ]
                parsed.user_message = normalized_messages[0]
                if len(normalized_messages) > 1:
                    entities = parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else {}
                    entities["user_message_parts"] = normalized_messages
                    parsed.internal_json.entities = entities
            else:
                parsed.user_message = _normalize_turkish_stay_quote_reply(parsed.user_message, normalized_text)
        if _executed_stay_hold_submission(executed_calls):
            parsed.user_message = _stay_pending_approval_message(language)
            parsed.internal_json.state = "PENDING_APPROVAL"
            parsed.internal_json.next_step = "await_admin_approval"
        _enforce_single_step_collection(parsed)
        return parsed
    except LLMUnavailableError:
        logger.warning("llm_unavailable_fallback")
        return LLMResponse(
            user_message=_default_reply_message(target_language),
            internal_json=InternalJSON(
                language=target_language,
                intent="other",
                state="INTENT_DETECTED",
                risk_flags=[],
                next_step="await_user_input",
            ),
        )


def _build_dispatcher_executor(dispatcher: Any, conversation: Conversation | None = None) -> Any:
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

        if conversation is not None:
            parsed_args = dict(parsed_args)
            if conversation.hotel_id and not parsed_args.get("hotel_id"):
                parsed_args["hotel_id"] = conversation.hotel_id
            if (
                tool_name in {
                    "stay_create_hold",
                    "restaurant_create_hold",
                    "transfer_create_hold",
                    "handoff_create_ticket",
                    "crm_log",
                }
                and conversation.id is not None
                and not parsed_args.get("conversation_id")
            ):
                parsed_args["conversation_id"] = str(conversation.id)

        result = await dispatcher.dispatch(tool_name, **parsed_args)
        return orjson.dumps(result).decode()

    return _execute


class _HandoffToolAdapter:
    """Adapter exposing create_ticket method for escalation engine."""

    def __init__(self, dispatcher: Any) -> None:
        self._dispatcher = dispatcher

    async def create_ticket(self, **kwargs: Any) -> dict[str, Any]:
        """Dispatch handoff ticket tool call."""
        result = await self._dispatcher.dispatch("handoff_create_ticket", **kwargs)
        if isinstance(result, dict):
            return cast(dict[str, Any], result)
        return {"status": "FAILED", "error_type": "INVALID_TOOL_RESULT"}


class _NotifyToolAdapter:
    """Adapter exposing send method for escalation engine."""

    def __init__(self, dispatcher: Any) -> None:
        self._dispatcher = dispatcher

    async def send(self, **kwargs: Any) -> dict[str, Any]:
        """Dispatch notification tool call."""
        result = await self._dispatcher.dispatch("notify_send", **kwargs)
        if isinstance(result, dict):
            return cast(dict[str, Any], result)
        return {"status": "FAILED", "error_type": "INVALID_TOOL_RESULT"}


async def _create_or_get_conversation(
    repository: ConversationRepository,
    incoming: IncomingMessage,
    hotel_id: int,
) -> Conversation:
    """Get active conversation by phone hash or create one."""
    phone_hash = _hash_phone(incoming.phone)
    conversation = await repository.get_active_by_phone(hotel_id, phone_hash)
    if conversation is not None:
        return conversation

    initial_language = _detect_message_language(incoming.text, "tr")
    new_conversation = Conversation(
        hotel_id=hotel_id,
        phone_hash=phone_hash,
        phone_display=_mask_phone(incoming.phone),
        language=initial_language,
    )
    return await repository.create(new_conversation)


async def _process_incoming_message(
    incoming: IncomingMessage,
    hotel_id: int,
    audit_context: dict[str, Any],
    dispatcher: Any,
    escalation_engine: Any,
    tools: dict[str, Any],
    db_pool: Any,
) -> None:
    """Background pipeline: log message, generate response, and send via WhatsApp."""
    conversation_repository = ConversationRepository()
    whatsapp_client = get_whatsapp_client()

    try:
        conversation = await _create_or_get_conversation(conversation_repository, incoming, hotel_id)
        if conversation.id is None:
            raise RuntimeError("Conversation id is missing.")

        normalized_text = _normalize_text(incoming.text)
        detected_language = _detect_message_language(normalized_text, conversation.language)
        if conversation.language != detected_language:
            conversation.language = detected_language
            await conversation_repository.update_language(conversation.id, detected_language)

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=normalized_text,
            internal_json=audit_context,
        )
        await conversation_repository.add_message(user_msg)
        conversation.messages = await conversation_repository.get_recent_messages(
            conversation.id,
            count=CONTEXT_WINDOW_MAX_MESSAGES,
        )

        await whatsapp_client.mark_as_read(incoming.message_id)

        llm_response = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=normalized_text,
            dispatcher=dispatcher,
            expected_language=detected_language,
        )
        current_state_value = (
            str(conversation.current_state.value)
            if hasattr(conversation.current_state, "value")
            else str(conversation.current_state or "GREETING")
        )
        next_state = str(llm_response.internal_json.state or current_state_value)
        next_intent = str(llm_response.internal_json.intent or "").strip() or None
        next_entities = llm_response.internal_json.entities or None
        next_risk_flags = llm_response.internal_json.risk_flags or None
        await conversation_repository.update_state(
            conversation_id=conversation.id,
            state=next_state,
            intent=next_intent,
            entities=next_entities,
            risk_flags=next_risk_flags,
        )

        message_parts = _extract_user_message_parts(llm_response)
        if not message_parts:
            message_parts = [llm_response.user_message]

        for index, raw_message in enumerate(message_parts, start=1):
            reply_text = formatter.truncate(raw_message)
            await whatsapp_client.send_text_message(to=incoming.phone, body=reply_text)

            assistant_internal_json = llm_response.internal_json.model_dump(mode="json")
            assistant_internal_json["message_part_index"] = index
            assistant_internal_json["message_part_total"] = len(message_parts)

            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=reply_text,
                internal_json=assistant_internal_json,
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
    hotel_id: int,
    audit_context: dict[str, Any],
    dispatcher: Any,
    escalation_engine: Any,
    tools: dict[str, Any],
    db_pool: Any,
) -> None:
    """Add incoming message task to FastAPI background worker."""
    background_tasks.add_task(
        _process_incoming_message,
        incoming,
        hotel_id,
        audit_context,
        dispatcher,
        escalation_engine,
        tools,
        db_pool,
    )


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

    now_ts = int(time.time())
    if incoming.timestamp <= 0 or abs(now_ts - incoming.timestamp) > WEBHOOK_MAX_AGE_SECONDS:
        logger.warning("whatsapp_webhook_stale_or_invalid_timestamp", message_id=incoming.message_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    phone_hash = _hash_phone(incoming.phone)
    webhook_ip = request.client.host if request.client is not None else "unknown"
    redis_client = getattr(request.app.state, "redis", None)

    if redis_client is not None:
        if await _redis_is_duplicate_message(redis_client, incoming.message_id):
            logger.info("whatsapp_webhook_duplicate", message_id=incoming.message_id)
            return {"status": "ok"}
        ip_allowed = await _redis_allow_rate_limit(
            redis_client,
            f"rl:webhook:{webhook_ip}:min",
            settings.rate_limit_webhook_per_minute,
            60,
        )
        if not ip_allowed:
            logger.warning("whatsapp_webhook_ip_limited", ip=webhook_ip)
            return {"status": "ok"}
        per_minute_allowed = await _redis_allow_rate_limit(
            redis_client,
            f"rl:phone:{phone_hash}:min",
            settings.rate_limit_per_phone_per_minute,
            60,
        )
        per_hour_allowed = await _redis_allow_rate_limit(
            redis_client,
            f"rl:phone:{phone_hash}:hour",
            settings.rate_limit_per_phone_per_hour,
            3600,
        )
        if not per_minute_allowed or not per_hour_allowed:
            logger.warning("whatsapp_phone_rate_limited", phone=_mask_phone(incoming.phone))
            return {"status": "ok"}
    else:
        logger.warning("whatsapp_webhook_redis_unavailable_fallback_to_local_limits")
        if deduplicator.is_duplicate(incoming.message_id):
            logger.info("whatsapp_webhook_duplicate", message_id=incoming.message_id)
            return {"status": "ok"}

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
    resolved_hotel_id = await _resolve_hotel_id_for_incoming(incoming, db_pool)
    if resolved_hotel_id is None:
        return {"status": "ok"}

    tools = {
        "handoff": _HandoffToolAdapter(dispatcher) if dispatcher is not None else None,
        "notify": _NotifyToolAdapter(dispatcher) if dispatcher is not None else None,
    }
    if tools["handoff"] is None or tools["notify"] is None:
        tools = {}

    route_audit = {
        "route": "/api/v1/webhook/whatsapp",
        "webhook_ip": webhook_ip,
        "signature_valid": True,
        "received_at": datetime.now(UTC).isoformat(),
        "resolved_hotel_id": resolved_hotel_id,
        "phone_number_id": incoming.phone_number_id,
        "display_phone_number": incoming.display_phone_number,
    }
    audit_context = {
        "source_type": "live_whatsapp",
        "hotel_id": resolved_hotel_id,
        "sender_profile_name": incoming.display_name or None,
        "wa_id_masked": _mask_phone(incoming.phone),
        "wa_id_hash": phone_hash,
        "message_id": incoming.message_id,
        "message_type": incoming.message_type,
        "route_audit": route_audit,
    }

    _schedule_background_task(
        background_tasks,
        incoming,
        resolved_hotel_id,
        audit_context,
        dispatcher,
        escalation_engine,
        tools,
        db_pool,
    )
    logger.info(
        "whatsapp_webhook_message_accepted",
        phone=_mask_phone(incoming.phone),
        message_type=incoming.message_type,
        wa_message_id=incoming.message_id,
        sender_profile_name=incoming.display_name or "",
        hotel_id=resolved_hotel_id,
        route=route_audit["route"],
    )
    return {"status": "accepted"}
