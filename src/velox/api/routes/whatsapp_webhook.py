"""WhatsApp webhook routes for verification and incoming messages."""

import hashlib
import re
import time
import unicodedata
from collections import defaultdict, deque
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

import orjson
import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from velox.adapters.elektraweb.endpoints import CHILD_OCCUPANCY_UNVERIFIED
from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.adapters.whatsapp.webhook import IncomingMessage, WhatsAppWebhook
from velox.config.constants import SUPPORTED_LANGUAGES
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
    return hashlib.sha256(phone.encode()).hexdigest()


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

    best_language = max(scores, key=scores.get)
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


def _build_deterministic_turkish_stay_quote_reply(
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
) -> str | None:
    """Format Turkish quote replies directly from booking_quote tool output."""
    offers = _extract_quote_offers(executed_calls)
    if not offers:
        return None

    profile = get_profile(hotel_id)
    room_order: dict[int, int] = {}
    if profile is not None:
        room_order = {
            int(getattr(room, "pms_room_type_id", 0) or 0): index
            for index, room in enumerate(getattr(profile, "room_types", []))
        }

    grouped_offers: dict[Any, dict[str, Any]] = {}
    for offer in offers:
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
        language = (
            target_language
            if target_language in SUPPORTED_LANGUAGE_CODES
            else str(parsed.internal_json.language or "tr").lower()
        )
        parsed.internal_json.language = language
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
        if intent == "stay_quote" and language == "tr" and _executed_booking_quote(executed_calls):
            deterministic_reply = _build_deterministic_turkish_stay_quote_reply(
                conversation.hotel_id,
                executed_calls,
            )
            if deterministic_reply:
                parsed.user_message = deterministic_reply
            parsed.user_message = _normalize_turkish_stay_quote_reply(parsed.user_message, normalized_text)
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

    initial_language = _detect_message_language(incoming.text, "tr")
    new_conversation = Conversation(
        hotel_id=settings.elektra_hotel_id,
        phone_hash=phone_hash,
        phone_display=_mask_phone(incoming.phone),
        language=initial_language,
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
        detected_language = _detect_message_language(normalized_text, conversation.language)
        if conversation.language != detected_language:
            conversation.language = detected_language
            await conversation_repository.update_language(conversation.id, detected_language)

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
            expected_language=detected_language,
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
