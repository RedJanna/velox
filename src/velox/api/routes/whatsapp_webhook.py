"""WhatsApp webhook routes for verification and incoming messages."""

import hashlib
import re
import time
import unicodedata
from collections import defaultdict, deque
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, cast

import orjson
import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from velox.adapters.elektraweb.endpoints import CHILD_OCCUPANCY_UNVERIFIED
from velox.adapters.whatsapp.client import WhatsAppSendBlockedError, get_whatsapp_client
from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.adapters.whatsapp.webhook import IncomingMessage, MessageStatusEvent, WhatsAppWebhook
from velox.config.constants import (
    CONTEXT_WINDOW_MAX_MESSAGES,
    SUPPORTED_LANGUAGES,
    ConversationState,
    Intent,
    RestaurantReservationMode,
)
from velox.config.settings import settings
from velox.core.burst_buffer import AggregatedMessage, BufferedMessage, enqueue_or_fallback
from velox.core.conversation_idle_policy import get_idle_close_threshold_seconds, get_idle_reset_config
from velox.core.fallback_response_library import out_of_scope_refusal, response_validation_fallback
from velox.core.hotel_profile_loader import get_profile
from velox.core.media_pipeline import MediaPipelineService
from velox.core.media_response_policy import build_media_policy_response
from velox.core.pipeline import post_process_escalation
from velox.core.response_validator import validate_guest_response
from velox.core.scope_classifier import ScopeDecision, classify_reception_scope
from velox.core.voice_pipeline import VoicePipelineService
from velox.core.voice_response_policy import build_voice_policy_response
from velox.db.repositories.conversation import ConversationRepository
from velox.db.repositories.restaurant_floor_plan import RestaurantSettingsRepository
from velox.db.repositories.whatsapp_number import WhatsAppNumberRepository
from velox.escalation.engine import EscalationEngine
from velox.llm.client import LLMUnavailableError, get_llm_client
from velox.llm.function_registry import get_tool_definitions
from velox.llm.prompt_builder import get_prompt_builder
from velox.llm.response_parser import ResponseParser
from velox.models.conversation import Conversation, InternalJSON, LLMResponse, Message
from velox.models.escalation import EscalationResult
from velox.models.media import InboundMediaItem
from velox.tools.notification import NotifySendTool, send_admin_whatsapp_alerts
from velox.utils.metrics import (
    record_intent_domain_guard,
    record_structured_output_fallback,
    record_structured_output_repair_outcome,
)
from velox.utils.operation_mode import sync_operation_mode_from_redis
from velox.utils.privacy import hash_phone

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

DEDUPE_TTL_SECONDS = 3600
MAX_TEXT_LENGTH = 4096
WEBHOOK_MAX_AGE_SECONDS = 300
TICKET_DEDUPE_KEY_MAX_LENGTH = 200
RESTAURANT_MANUAL_MODE_KEYWORDS = (
    "restoran",
    "restaurant",
    "masa",
    "table",
    "rezervasyon",
    "reservation",
    "menu",
    "menü",
    "kahvalti",
    "kahvaltı",
    "breakfast",
    "ogle",
    "ögle",
    "öğle",
    "lunch",
    "aksam",
    "akşam",
    "dinner",
    "yemek",
    "meal",
    "servis",
    "service",
)

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
RESERVATION_INTENT_PREFIXES = ("stay_", "restaurant_", "transfer_")
RESERVATION_DATE_FIELD_KEYS = {"checkin_date", "checkout_date", "date"}
PHONE_CHOICE_USE_CURRENT_VALUES = {
    "1",
    "bir",
    "one",
    "option1",
    "secenek1",
    "seçenek1",
    "mevcut",
    "current",
}
PHONE_CHOICE_DIFFERENT_VALUES = {
    "2",
    "iki",
    "two",
    "option2",
    "secenek2",
    "seçenek2",
    "farkli",
    "farklı",
    "different",
}
PHONE_PLACEHOLDER_VALUES = {"whatsappnumberconfirmed", "whatsappnumber"}
RESTAURANT_AREA_PROMPT_PATTERN = re.compile(
    r"(iç\s*mekan|ic\s*mekan|dış\s*mekan|dis\s*mekan|indoor|outdoor|alan tercihi|hangi alan|iç mi dış mı|ic mi dis mi)",
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
# ── Language hint dictionaries (expanded) ─────────────────────────
# Each tuple contains common greetings, polite words, travel/hotel
# vocabulary AND short everyday words so even a single-word message
# like "hello" or "привет" triggers the correct language.

TURKISH_LANGUAGE_HINTS = (
    # greetings & polite
    "merhaba", "selam", "hosgeldiniz", "hos geldiniz", "gunaydin",
    "iyi gunler", "iyi aksamlar", "tesekkurler", "tesekkur",
    "lutfen", "sagol", "sagolun", "evet", "hayir", "tamam",
    # travel & hotel
    "rezervasyon", "otel", "fiyat", "oda", "kahvalti", "havaalani",
    "transfer", "gece", "gecelik", "konaklama", "giris", "cikis",
    "tarih", "kisi", "kişi", "yetiskin", "cocuk", "iptal",
    # connectors & common
    "ve", "icin", "bir", "bu", "ne", "nasil", "var", "yok",
    "istiyorum", "bilgi", "musait", "bos",
)
ENGLISH_LANGUAGE_HINTS = (
    # greetings & polite
    "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
    "good night", "thanks", "thank you", "please", "yes", "no", "ok", "okay",
    "sorry", "excuse me", "welcome", "bye", "goodbye",
    # travel & hotel
    "hotel", "room", "booking", "reservation", "price", "rate", "night",
    "checkin", "check-in", "checkout", "check-out", "airport", "transfer",
    "breakfast", "pool", "spa", "beach", "available", "availability",
    "cancel", "cancellation", "guest", "adult", "child", "children",
    # common verbs & words
    "i", "you", "we", "need", "want", "would", "like", "can", "could",
    "have", "do", "is", "are", "the", "for", "how", "much", "when",
    "what", "where", "my", "your",
)
GERMAN_LANGUAGE_HINTS = (
    # greetings & polite
    "hallo", "guten morgen", "guten tag", "guten abend", "gute nacht",
    "danke", "bitte", "ja", "nein", "entschuldigung", "tschuss",
    "willkommen", "auf wiedersehen",
    # travel & hotel
    "zimmer", "preis", "buchung", "reservierung", "ubernachtung",
    "flughafen", "transfer", "fruhstuck", "strand", "schwimmbad",
    "verfugbar", "stornierung", "stornieren", "anreise", "abreise",
    "erwachsene", "kinder", "nacht",
    # common
    "ich", "wir", "sie", "mochte", "haben", "ist", "ein", "eine",
    "fur", "wie", "viel", "wann", "wo", "das", "der", "die",
)
ARABIC_LANGUAGE_HINTS = (
    # greetings & polite
    "مرحبا", "اهلا", "سلام", "صباح الخير", "مساء الخير",
    "شكرا", "من فضلك", "نعم", "لا", "مع السلامة",
    # travel & hotel
    "حجز", "غرفة", "فندق", "سعر", "ليلة", "مطار", "نقل",
    "فطور", "شاطئ", "مسبح", "متاح", "الغاء", "وصول", "مغادرة",
    "بالغ", "طفل", "اطفال",
    # common
    "انا", "نحن", "اريد", "كم", "متى", "اين", "هل", "كيف",
)
RUSSIAN_LANGUAGE_HINTS = (
    # greetings & polite
    "привет", "здравствуйте", "доброе утро", "добрый день",
    "добрый вечер", "спасибо", "пожалуйста", "да", "нет",
    "извините", "до свидания",
    # travel & hotel
    "отель", "гостиница", "номер", "бронирование", "бронь",
    "цена", "стоимость", "ночь", "аэропорт", "трансфер",
    "завтрак", "бассейн", "пляж", "свободно", "отмена",
    "заезд", "выезд", "взрослый", "ребенок", "дети",
    # common
    "я", "мы", "вы", "хочу", "нужно", "можно", "есть",
    "сколько", "когда", "где", "как", "мне", "нам",
)
SPANISH_LANGUAGE_HINTS = (
    # greetings & polite
    "hola", "buenos dias", "buenas tardes", "buenas noches",
    "gracias", "por favor", "si", "no", "perdon", "disculpe",
    "bienvenido", "adios", "hasta luego",
    # travel & hotel
    "habitacion", "hotel", "precio", "reserva", "reservacion",
    "noche", "aeropuerto", "traslado", "transfer", "desayuno",
    "piscina", "playa", "disponible", "cancelacion", "cancelar",
    "llegada", "salida", "adulto", "nino", "ninos",
    # common
    "yo", "nosotros", "quiero", "necesito", "puedo", "tiene",
    "cuanto", "cuando", "donde", "como", "el", "la", "un", "una",
    "para", "con",
)
FRENCH_LANGUAGE_HINTS = (
    # greetings & polite
    "bonjour", "bonsoir", "bonne nuit", "salut", "merci",
    "s'il vous plait", "sil vous plait", "oui", "non",
    "excusez-moi", "bienvenue", "au revoir",
    # travel & hotel
    "chambre", "hotel", "prix", "reservation", "nuit", "nuitee",
    "aeroport", "transfert", "petit dejeuner", "piscine", "plage",
    "disponible", "annulation", "annuler", "arrivee", "depart",
    "adulte", "enfant", "enfants",
    # common
    "je", "nous", "vous", "voudrais", "besoin", "pouvez",
    "combien", "quand", "ou", "comment", "le", "la", "un", "une",
    "pour", "avec",
)
CHINESE_LANGUAGE_HINTS = (
    # greetings & polite
    "你好", "您好", "早上好", "晚上好", "谢谢", "请", "是", "不",
    "对不起", "再见",
    # travel & hotel
    "酒店", "宾馆", "房间", "预订", "价格", "费用", "晚",
    "机场", "接送", "早餐", "游泳池", "海滩", "可以", "取消",
    "入住", "退房", "成人", "儿童", "孩子",
    # common
    "我", "我们", "你", "要", "需要", "多少", "什么时候",
    "哪里", "怎么", "有", "没有",
)
HINDI_LANGUAGE_HINTS = (
    # greetings & polite
    "नमस्ते", "नमस्कार", "सुप्रभात", "शुभ संध्या",
    "धन्यवाद", "शुक्रिया", "कृपया", "हां", "नहीं",
    "माफ कीजिए", "अलविदा",
    # travel & hotel
    "होटल", "कमरा", "बुकिंग", "रिज़र्वेशन", "कीमत", "दाम",
    "रात", "एयरपोर्ट", "हवाई अड्डा", "ट्रांसफर", "नाश्ता",
    "स्विमिंग पूल", "बीच", "उपलब्ध", "रद्द", "चेक इन",
    "चेक आउट", "वयस्क", "बच्चा", "बच्चे",
    # common
    "मैं", "हम", "आप", "चाहिए", "कितना", "कब", "कहां",
    "कैसे", "है", "हैं", "मुझे", "हमें",
)
PORTUGUESE_LANGUAGE_HINTS = (
    # greetings & polite
    "ola", "bom dia", "boa tarde", "boa noite", "obrigado",
    "obrigada", "por favor", "sim", "nao", "desculpe",
    "bem-vindo", "adeus", "ate logo",
    # travel & hotel
    "quarto", "hotel", "preco", "reserva", "noite",
    "aeroporto", "transfer", "translado", "cafe da manha",
    "piscina", "praia", "disponivel", "cancelamento", "cancelar",
    "chegada", "saida", "adulto", "crianca", "criancas",
    # common
    "eu", "nos", "voce", "quero", "preciso", "posso", "tem",
    "quanto", "quando", "onde", "como", "o", "a", "um", "uma",
    "para", "com",
)
LANGUAGE_HINTS = {
    "tr": TURKISH_LANGUAGE_HINTS,
    "en": ENGLISH_LANGUAGE_HINTS,
    "de": GERMAN_LANGUAGE_HINTS,
    "ar": ARABIC_LANGUAGE_HINTS,
    "ru": RUSSIAN_LANGUAGE_HINTS,
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
URL_PATTERN = re.compile(r"(https?://\S+|www\.\S+)", flags=re.IGNORECASE)
URL_LIKE_TOKEN_PATTERN = re.compile(
    r"^(?:[a-z0-9-]+\.)+[a-z]{2,}(?:[/:?#].*)?$",
    flags=re.IGNORECASE,
)
TECHNICAL_LINK_TOKENS = {
    "checkin",
    "checkout",
    "adult",
    "adults",
    "child",
    "children",
    "childages",
    "language",
    "currency",
    "promo",
    "promocode",
    "utm_source",
    "utm_medium",
    "utm_campaign",
}
LANGUAGE_SWITCH_MIN_SCORE = 2
LANGUAGE_SWITCH_MIN_MARGIN = 2


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


def _extract_media_items_from_incoming(incoming: IncomingMessage) -> list[InboundMediaItem]:
    """Extract media payload details from one incoming message."""
    if not incoming.media_id:
        return []
    return [
        InboundMediaItem(
            media_id=incoming.media_id,
            media_type=str(incoming.message_type or ""),
            mime_type=str(incoming.media_mime_type or ""),
            sha256=str(incoming.media_sha256 or ""),
            caption=str(incoming.media_caption or ""),
            whatsapp_message_id=str(incoming.message_id or ""),
        )
    ]


def _extract_media_items_from_audits(audit_contexts: list[dict[str, Any]]) -> list[InboundMediaItem]:
    """Extract media payload details from burst audit contexts."""
    items: list[InboundMediaItem] = []
    for audit in audit_contexts:
        media = audit.get("media")
        if not isinstance(media, dict):
            continue
        media_id = str(media.get("id") or "").strip()
        if not media_id:
            continue
        items.append(
            InboundMediaItem(
                media_id=media_id,
                media_type=str(media.get("type") or "image"),
                mime_type=str(media.get("mime_type") or ""),
                sha256=str(media.get("sha256") or ""),
                caption=str(media.get("caption") or ""),
                whatsapp_message_id=str(audit.get("message_id") or ""),
            )
        )
    return items


def _extract_media_items_from_aggregated(aggregated: AggregatedMessage) -> list[InboundMediaItem]:
    """Extract media payload details from aggregated burst object."""
    items: list[InboundMediaItem] = []
    for media in aggregated.media_items:
        if not isinstance(media, dict):
            continue
        media_id = str(media.get("media_id") or "").strip()
        if not media_id:
            continue
        items.append(
            InboundMediaItem(
                media_id=media_id,
                media_type=str(media.get("media_type") or "image"),
                mime_type=str(media.get("mime_type") or ""),
                sha256=str(media.get("sha256") or ""),
                caption=str(media.get("caption") or ""),
                whatsapp_message_id=str(media.get("message_id") or ""),
            )
        )
    if items:
        return items
    return _extract_media_items_from_audits(aggregated.audit_contexts)


async def _analyze_media_policy_response(
    *,
    hotel_id: int,
    conversation_id: Any,
    language: str,
    media_items: list[InboundMediaItem],
    user_text: str = "",
) -> LLMResponse | None:
    """Run media analysis pipeline and return deterministic response when applicable."""
    if not settings.media_analysis_enabled:
        return None
    if not media_items:
        return None
    if not any(item.media_type == "image" for item in media_items):
        return None
    whatsapp_client = get_whatsapp_client()
    pipeline = MediaPipelineService(whatsapp_client)
    try:
        result = await pipeline.process_first_image(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            language=language,
            media_items=media_items,
        )
    except Exception as error:
        logger.warning(
            "media_policy_pipeline_failed",
            hotel_id=hotel_id,
            conversation_id=str(conversation_id),
            error_type=type(error).__name__,
        )
        return build_media_policy_response(
            language=language,
            analysis=None,
            failure_reason="ANALYSIS_ERROR",
            user_text=user_text,
        )
    if result.analyzed and result.analysis is not None:
        return build_media_policy_response(
            language=language,
            analysis=result.analysis,
            user_text=user_text,
        )
    return build_media_policy_response(
        language=language,
        analysis=None,
        failure_reason=result.failure_reason,
        user_text=user_text,
    )


async def _process_voice_message(
    *,
    hotel_id: int,
    conversation_id: Any,
    media_items: list[InboundMediaItem],
    preferred_language: str | None = None,
) -> tuple[str | None, str | None, LLMResponse | None]:
    """Transcribe audio and return transcript text, language override, and fallback response."""
    fallback_language = preferred_language or settings.audio_transcription_fallback_language
    if not settings.audio_transcription_enabled:
        return None, None, None
    if not media_items:
        return None, None, None
    if not any(item.media_type == "audio" for item in media_items):
        return None, None, None

    whatsapp_client = get_whatsapp_client()
    pipeline = VoicePipelineService(whatsapp_client)
    try:
        result = await pipeline.process_first_audio(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            media_items=media_items,
        )
    except Exception as error:
        logger.warning(
            "voice_policy_pipeline_failed",
            hotel_id=hotel_id,
            conversation_id=str(conversation_id),
            error_type=type(error).__name__,
        )
        fallback = build_voice_policy_response(
            language=fallback_language,
            transcription=None,
            failure_reason="TRANSCRIPTION_ERROR",
        )
        return None, None, fallback

    if not result.analyzed or result.transcription is None:
        fallback = build_voice_policy_response(
            language=fallback_language,
            transcription=None,
            failure_reason=result.failure_reason,
        )
        return None, None, fallback

    fallback = build_voice_policy_response(
        language=result.transcription.language or fallback_language,
        transcription=result.transcription,
    )
    if fallback is not None:
        return None, result.transcription.language or None, fallback

    transcript_text = result.transcription.text.strip()
    if not transcript_text:
        fallback = build_voice_policy_response(
            language=result.transcription.language or fallback_language,
            transcription=result.transcription,
            failure_reason="EMPTY_TRANSCRIPT",
        )
        return None, result.transcription.language or None, fallback

    return transcript_text, result.transcription.language or None, None


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


def _restaurant_pending_approval_message(language: str = "tr") -> str:
    """Guest-facing acknowledgement for restaurant approval flow."""
    if language == "en":
        return (
            "Your restaurant reservation request has been received.\n\n"
            "We have forwarded it for approval and will inform you as soon as it is confirmed."
        )
    if language == "ru":
        return (
            "Мы получили ваш запрос на бронирование ресторана.\n\n"
            "Мы передали его на подтверждение и сообщим вам сразу после одобрения."
        )
    return (
        "Restoran rezervasyon talebinizi aldik.\n\n"
        "Talebinizi onay icin ilgili birimimize ilettik. Onay geldiginde size hemen bilgi verecegiz."
    )


def _transfer_pending_approval_message(language: str = "tr") -> str:
    """Guest-facing acknowledgement for transfer approval flow."""
    if language == "en":
        return (
            "Your transfer reservation request has been received.\n\n"
            "We have forwarded it for approval and will inform you as soon as it is confirmed."
        )
    if language == "ru":
        return (
            "Мы получили ваш запрос на трансфер.\n\n"
            "Мы передали его на подтверждение и сообщим вам сразу после одобрения."
        )
    return (
        "Transfer rezervasyon talebinizi aldik.\n\n"
        "Talebinizi onay icin ilgili birimimize ilettik. Onay geldiginde size hemen bilgi verecegiz."
    )


def _restaurant_confirmed_message(language: str = "tr") -> str:
    """Guest-facing confirmation after restaurant hold is finalized."""
    if language == "en":
        return "Your restaurant reservation has been confirmed and finalized."
    if language == "ru":
        return "Ваше бронирование ресторана подтверждено и окончательно оформлено."
    return "Restoran rezervasyonunuz onaylandi ve kesinlestirildi."


def _restaurant_unavailable_message(language: str = "tr") -> str:
    """Guest-facing prompt when requested restaurant slot is not available."""
    if language == "en":
        return (
            "I could not find availability for that exact time. "
            "If you want, I can check an alternative time for you."
        )
    if language == "ru":
        return (
            "На это точное время свободного места не найдено. "
            "Если хотите, я могу проверить для вас другое время."
        )
    return (
        "Istediginiz saat icin uygun masa bulamadim. "
        "Dilerseniz alternatif bir saat kontrol edebilirim."
    )


def _format_month_day_label(value: str, language: str) -> str:
    """Convert MM-DD season values into a readable month-day label."""
    try:
        month, day = (int(part) for part in str(value or "").split("-", maxsplit=1))
        date_value = date(2000, month, day)
    except (TypeError, ValueError):
        return str(value or "")

    if language == "en":
        return date_value.strftime("%B %d")

    tr_months = {
        1: "Ocak",
        2: "Subat",
        3: "Mart",
        4: "Nisan",
        5: "Mayis",
        6: "Haziran",
        7: "Temmuz",
        8: "Agustos",
        9: "Eylul",
        10: "Ekim",
        11: "Kasim",
        12: "Aralik",
    }
    if language == "ru":
        ru_months = {
            1: "января",
            2: "февраля",
            3: "марта",
            4: "апреля",
            5: "мая",
            6: "июня",
            7: "июля",
            8: "августа",
            9: "сентября",
            10: "октября",
            11: "ноября",
            12: "декабря",
        }
        return f"{day} {ru_months.get(month, str(month))}"
    return f"{day} {tr_months.get(month, str(month))}"


def _restaurant_season_unavailable_message(language: str, season: dict[str, Any] | None = None) -> str:
    """Guest-facing message for out-of-season restaurant requests."""
    season_info = season or {}
    open_label = _format_month_day_label(str(season_info.get("open") or ""), language)
    close_label = _format_month_day_label(str(season_info.get("close") or ""), language)
    if language == "en":
        window = f"{open_label} - {close_label}" if open_label and close_label else "the active season"
        return (
            f"Our restaurant serves guests during {window}. "
            "This requested date is outside that period. If you want, please share another date within the season."
        )
    if language == "ru":
        window = f"{open_label} - {close_label}" if open_label and close_label else "активный сезон"
        return (
            f"Наш ресторан работает в период {window}. "
            "Запрошенная дата находится вне сезона. При желании укажите другую дату в пределах сезона."
        )
    window = f"{open_label} - {close_label}" if open_label and close_label else "sezon donemimiz"
    return (
        f"Restoranimiz {window} tarihleri arasinda hizmet vermektedir. "
        "Sectiginiz tarih sezon disinda kaliyor. Dilerseniz sezon icinde baska bir tarih paylasabilirsiniz."
    )


def _reservation_season_unavailable_message(
    language: str,
    season: dict[str, Any] | None,
    reservation_type: str,
) -> str:
    """Guest-facing out-of-season message for stay/transfer reservation flows."""
    season_info = season or {}
    open_label = _format_month_day_label(str(season_info.get("open") or ""), language)
    close_label = _format_month_day_label(str(season_info.get("close") or ""), language)
    if language == "en":
        window = f"{open_label} - {close_label}" if open_label and close_label else "the active season"
        if reservation_type == "transfer":
            return (
                f"We accept transfer reservations during {window}. "
                "This requested date is outside that period. If you want, please share another date within the season."
            )
        return (
            f"We accept stay reservations during {window}. "
            "This requested date is outside that period. If you want, please share another date within the season."
        )
    if language == "ru":
        window = f"{open_label} - {close_label}" if open_label and close_label else "активный сезон"
        if reservation_type == "transfer":
            return (
                f"Мы принимаем трансферные бронирования в период {window}. "
                "Запрошенная дата находится вне сезона. При желании укажите другую дату в пределах сезона."
            )
        return (
            f"Мы принимаем бронирование проживания в период {window}. "
            "Запрошенная дата находится вне сезона. При желании укажите другую дату в пределах сезона."
        )
    window = f"{open_label} - {close_label}" if open_label and close_label else "sezon donemimiz"
    if reservation_type == "transfer":
        return (
            f"Transfer rezervasyonlarimizi {window} tarihleri arasinda aliyoruz. "
            "Sectiginiz tarih sezon disinda kaliyor. Dilerseniz sezon icinde baska bir tarih paylasabilirsiniz."
        )
    return (
        f"Konaklama rezervasyonlarimizi {window} tarihleri arasinda aliyoruz. "
        "Sectiginiz tarih sezon disinda kaliyor. Dilerseniz sezon icinde baska bir tarih paylasabilirsiniz."
    )


def _restaurant_hours_unavailable_message(language: str, profile: Any | None) -> str:
    """Guest-facing message for requests outside restaurant operating hours."""
    hours = getattr(getattr(profile, "restaurant", None), "hours", {}) if profile is not None else {}
    dinner_hours = str(hours.get("dinner") or "").strip()
    if language == "en":
        if dinner_hours:
            return f"Our dinner service hours are {dinner_hours}. Please share a time within that range."
        return "The requested time is outside our restaurant operating hours. Please share another time."
    if language == "ru":
        if dinner_hours:
            return f"Часы ужина: {dinner_hours}. Пожалуйста, укажите время в этом диапазоне."
        return "Запрошенное время находится вне часов работы ресторана. Пожалуйста, укажите другое время."
    if dinner_hours:
        return f"Aksam servisi saatlerimiz {dinner_hours}. Bu aralikta bir saat paylasir misiniz?"
    return "Sectiginiz saat restoran hizmet saatlerimizin disinda kaliyor. Baska bir saat paylasir misiniz?"


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


def _collapse_repeated_letters(value: str) -> str:
    """Reduce repeated letters so minor typos like 'haaziran' still match month aliases."""
    return re.sub(r"(.)\1+", r"\1", str(value or ""))


def _normalize_month_token(value: str) -> str:
    """Map free-form month tokens onto a stable canonical month key."""
    collapsed = _collapse_repeated_letters(value.casefold())
    canonical = _canonical_text(collapsed)
    if canonical in _STAY_MONTH_LABELS:
        return canonical
    if canonical in _STAY_MONTH_ALIASES:
        return _STAY_MONTH_ALIASES[canonical]
    for alias, month_key in _STAY_MONTH_ALIASES.items():
        if canonical.startswith(alias) or alias.startswith(canonical):
            return month_key
    return ""


def _extract_stay_date_mentions(user_text: str) -> list[str]:
    """Extract coarse day-month mentions to stabilize stay follow-up turns."""
    mentions: list[str] = []

    for match in _DAY_MONTH_PATTERN.finditer(user_text):
        day = int(match.group(1))
        if not 1 <= day <= 31:
            continue
        month_key = _normalize_month_token(match.group(2))
        if not month_key:
            continue
        label = f"{day} {_STAY_MONTH_LABELS.get(month_key, month_key.title())}"
        if label not in mentions:
            mentions.append(label)

    for match in _NUMERIC_DATE_PATTERN.finditer(user_text):
        day = int(match.group(1))
        month = int(match.group(2))
        if not (1 <= day <= 31 and 1 <= month <= 12):
            continue
        label = f"{day:02d}.{month:02d}"
        if label not in mentions:
            mentions.append(label)

    return mentions[:2]


def _extract_adult_count_hint(user_text: str) -> int:
    """Extract an explicit adult count when the guest states it directly."""
    match = _ADULT_COUNT_PATTERN.search(user_text)
    if not match:
        return 0
    return _to_int(match.group(1), 0)


def _intent_domain(intent: str) -> str:
    """Collapse detailed intents onto coarse product domains."""
    normalized = str(intent or "").strip().lower()
    if normalized.startswith("stay_"):
        return "stay"
    if normalized.startswith("restaurant_"):
        return "restaurant"
    if normalized.startswith("transfer_"):
        return "transfer"
    if normalized.startswith("room_service_"):
        return "room_service"
    return "other"


def _build_stay_followup_override_message(
    language: str,
    *,
    date_mentions: list[str],
    adult_count: int,
) -> tuple[str, list[str], str]:
    """Build a deterministic stay follow-up prompt when the model drifts into restaurant intent."""
    if language == "en":
        if len(date_mentions) >= 2 and adult_count > 0:
            return (
                f"I noted your stay request as {date_mentions[0]} - {date_mentions[1]} for {adult_count} adult(s).\n\n"
                "If there will be children, please share their ages. If not, you can reply 'no children'.",
                ["chd_ages"],
                "collect_stay_children_or_confirm_none",
            )
        if len(date_mentions) >= 2:
            return (
                f"I noted your requested dates as {date_mentions[0]} - {date_mentions[1]}.\n\n"
                "How many adults will stay?",
                ["adults"],
                "collect_stay_adults",
            )
        if len(date_mentions) == 1:
            return (
                f"I noted {date_mentions[0]} for your stay request.\n\n"
                "Please also share your check-out date.",
                ["checkout_date"],
                "collect_stay_checkout_date",
            )
        return (
            "For a stay request, please share your check-in date, check-out date, and number of adults.",
            ["checkin_date"],
            "collect_stay_checkin_date",
        )

    if language == "ru":
        if len(date_mentions) >= 2 and adult_count > 0:
            return (
                f"Я зафиксировал(а) ваш запрос на проживание: "
                f"{date_mentions[0]} - {date_mentions[1]}, {adult_count} взрослый(ых).\n\n"
                "Если будут дети, укажите их возраст. Если детей нет, можно ответить 'без детей'.",
                ["chd_ages"],
                "collect_stay_children_or_confirm_none",
            )
        if len(date_mentions) >= 2:
            return (
                f"Я зафиксировал(а) ваши даты: {date_mentions[0]} - {date_mentions[1]}.\n\n"
                "Сколько взрослых будет проживать?",
                ["adults"],
                "collect_stay_adults",
            )
        if len(date_mentions) == 1:
            return (
                f"Я зафиксировал(а) дату {date_mentions[0]}.\n\n"
                "Пожалуйста, укажите также дату выезда.",
                ["checkout_date"],
                "collect_stay_checkout_date",
            )
        return (
            "Для запроса на проживание укажите дату заезда, дату выезда и количество взрослых.",
            ["checkin_date"],
            "collect_stay_checkin_date",
        )

    if len(date_mentions) >= 2 and adult_count > 0:
        return (
            f"Konaklama talebinizi not aldım: {date_mentions[0]} - {date_mentions[1]}, {adult_count} yetişkin.\n\n"
            "Çocuk olacaksa yaşlarını paylaşır mısınız? Çocuk yoksa 'çocuk yok' yazabilirsiniz.",
            ["chd_ages"],
            "collect_stay_children_or_confirm_none",
        )
    if len(date_mentions) >= 2:
        return (
            f"Konaklama tarihinizi {date_mentions[0]} - {date_mentions[1]} olarak not aldım.\n\n"
            "Kaç yetişkin konaklayacaksınız?",
            ["adults"],
            "collect_stay_adults",
        )
    if len(date_mentions) == 1:
        return (
            f"Konaklama için {date_mentions[0]} tarihini not aldım.\n\n"
            "Çıkış tarihinizi de paylaşır mısınız?",
            ["checkout_date"],
            "collect_stay_checkout_date",
        )
    return (
        "Konaklama talebiniz için giriş tarihi, çıkış tarihi ve yetişkin sayısını paylaşır mısınız?",
        ["checkin_date"],
        "collect_stay_checkin_date",
    )


def _restaurant_manual_mode_message(language: str) -> str:
    """Return guest-facing handoff message when restaurant manual mode is enabled."""
    if language == "en":
        return (
            "Restaurant requests are handled in Manual Mode right now. "
            "I am connecting you to a live customer representative."
        )
    if language == "ru":
        return (
            "Запросы по ресторану сейчас обрабатываются в ручном режиме. "
            "Подключаю вас к живому представителю."
        )
    return (
        "Restoran talepleri su anda Manuel Modda yonetiliyor. "
        "Sizi canli musteri temsilcisine bagliyorum."
    )


def _is_restaurant_manual_mode_candidate(conversation: Conversation, normalized_text: str) -> bool:
    """Return True when the turn is clearly related to restaurant flow."""
    current_intent = str(conversation.current_intent or "").strip().lower()
    if _intent_domain(current_intent) == "restaurant":
        return True

    canonical_text = _canonical_text(normalized_text)
    if any(keyword in canonical_text for keyword in RESTAURANT_MANUAL_MODE_KEYWORDS):
        return True

    entities = conversation.entities_json if isinstance(conversation.entities_json, dict) else {}
    last_intent = str(entities.get("last_intent") or "").strip().lower()
    return _intent_domain(last_intent) == "restaurant"


async def _should_force_restaurant_manual_handoff(conversation: Conversation, normalized_text: str) -> bool:
    """Return True when restaurant manual mode requires immediate human handoff."""
    if not _is_restaurant_manual_mode_candidate(conversation, normalized_text):
        return False

    try:
        settings_repo = RestaurantSettingsRepository()
        restaurant_settings = await settings_repo.get(conversation.hotel_id)
    except Exception:
        logger.warning(
            "restaurant_settings_lookup_failed",
            hotel_id=conversation.hotel_id,
        )
        return False
    return restaurant_settings.reservation_mode == RestaurantReservationMode.MANUEL


def _apply_turn_intent_domain_guard(
    response: LLMResponse,
    *,
    normalized_text: str,
    tool_names_presented: list[str],
) -> dict[str, Any] | None:
    """Clamp obvious cross-domain drift when the parsed intent contradicts the turn's tool surface."""
    parsed_intent = str(response.internal_json.intent or "").strip().lower()
    if _intent_domain(parsed_intent) != "restaurant":
        return None

    presented_names = {str(name or "").strip() for name in tool_names_presented if str(name or "").strip()}
    restaurant_domain_tools = _RESTAURANT_TOOL_SHORTLIST - _GENERAL_TOOL_SHORTLIST - {"approval_request"}
    stay_domain_tools = _STAY_TOOL_SHORTLIST - _GENERAL_TOOL_SHORTLIST - {"approval_request"}
    has_restaurant_tools = bool(presented_names & restaurant_domain_tools)
    has_stay_tools = bool(presented_names & stay_domain_tools)
    if has_restaurant_tools or not has_stay_tools:
        return None

    canonical_text = _canonical_text(normalized_text)
    date_mentions = _extract_stay_date_mentions(normalized_text)
    adult_count = _extract_adult_count_hint(normalized_text)
    has_restaurant_words = any(
        token in canonical_text
        for token in ("restoran", "restaurant", "masa", "table", "aksamyemegi", "dinner", "lunch", "menu")
    )
    has_time_of_day = _TIME_OF_DAY_PATTERN.search(normalized_text) is not None
    looks_like_stay_followup = bool(date_mentions) and not has_restaurant_words and not has_time_of_day
    if not looks_like_stay_followup:
        return None

    language = str(response.internal_json.language or "tr").lower()
    message, required_questions, next_step = _build_stay_followup_override_message(
        language,
        date_mentions=date_mentions,
        adult_count=adult_count,
    )
    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    override_meta = {
        "applied": True,
        "from_intent": parsed_intent,
        "to_intent": Intent.STAY_AVAILABILITY.value,
        "reason": "stay_followup_without_restaurant_tools",
    }
    entities["intent_domain_guard"] = override_meta
    stay_hints = (
        dict(entities.get("stay_followup_hints") or {})
        if isinstance(entities.get("stay_followup_hints"), dict)
        else {}
    )
    if date_mentions:
        stay_hints["date_mentions"] = date_mentions
    if adult_count > 0:
        stay_hints["adults"] = adult_count
    if stay_hints:
        entities["stay_followup_hints"] = stay_hints

    response.user_message = message
    response.internal_json.intent = Intent.STAY_AVAILABILITY.value
    response.internal_json.state = ConversationState.NEEDS_VERIFICATION.value
    response.internal_json.entities = entities
    response.internal_json.required_questions = required_questions
    response.internal_json.next_step = next_step
    response.internal_json.handoff = {"needed": False}
    return override_meta


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


def _canonicalize_tool_calls(
    raw_tool_calls: list[dict[str, Any]] | None,
    *,
    default_status: str,
) -> list[dict[str, Any]]:
    """Normalize tool call payloads for INTERNAL_JSON and message persistence."""
    normalized: list[dict[str, Any]] = []
    for item in raw_tool_calls or []:
        if not isinstance(item, dict):
            continue
        tool_name = str(item.get("name") or item.get("tool") or "").strip()
        if not tool_name:
            continue

        arguments = item.get("arguments")
        if not isinstance(arguments, dict):
            arguments = item.get("args")
        if not isinstance(arguments, dict):
            arguments = _loads_tool_payload(arguments)
        if not isinstance(arguments, dict):
            arguments = {}

        normalized_item: dict[str, Any] = {
            "name": tool_name,
            "status": str(item.get("status") or default_status).strip() or default_status,
            "arguments": arguments,
        }

        if "result" in item:
            parsed_result = _loads_tool_payload(item.get("result"))
            normalized_item["result"] = parsed_result if parsed_result else item.get("result")

        normalized.append(normalized_item)
    return normalized


def _extract_tool_definition_names(tools: list[dict[str, Any]] | None) -> list[str]:
    """Return normalized tool names from OpenAI tool definition payloads."""
    names: list[str] = []
    for tool in tools or []:
        tool_name = ""
        if isinstance(tool, dict):
            function_block = tool.get("function")
            if isinstance(function_block, dict):
                tool_name = str(function_block.get("name") or "").strip()
            elif isinstance(tool.get("name"), str):
                tool_name = str(tool.get("name") or "").strip()
        if tool_name and tool_name not in names:
            names.append(tool_name)
    return names


_GENERAL_TOOL_SHORTLIST = {"faq_lookup", "hotel_info_lookup", "handoff_create_ticket"}
_STAY_TOOL_SHORTLIST = {
    "booking_availability",
    "booking_quote",
    "stay_create_hold",
    "booking_get_reservation",
    "booking_modify",
    "booking_cancel",
    "approval_request",
    "payment_request_prepayment",
}
_RESTAURANT_TOOL_SHORTLIST = {
    "restaurant_availability",
    "restaurant_create_hold",
    "restaurant_confirm",
    "restaurant_modify",
    "restaurant_cancel",
    "approval_request",
}
_TRANSFER_TOOL_SHORTLIST = {
    "transfer_get_info",
    "transfer_create_hold",
    "transfer_confirm",
    "transfer_modify",
    "transfer_cancel",
    "approval_request",
}
_ROOM_SERVICE_TOOL_SHORTLIST = {
    "room_service_create_order",
    "notify_send",
}

_STAY_TOOL_HINTS = (
    "rezervasyon",
    "reservation",
    "booking",
    "oda",
    "room",
    "checkin",
    "check-in",
    "checkout",
    "check-out",
    "fiyat",
    "price",
    "iptal",
    "cancel",
)
_RESTAURANT_TOOL_HINTS = (
    "restaurant",
    "restoran",
    "masa",
    "table",
    "kahvalt",
    "aksam yemegi",
    "akşam yemeği",
    "dinner",
    "lunch",
    "menu",
    "menü",
    "vegan",
)
_TRANSFER_TOOL_HINTS = ("transfer", "havaalani", "havaalanı", "airport", "flight", "ucus", "uçuş")
_ROOM_SERVICE_TOOL_HINTS = ("room service", "oda servisi", "siparis", "sipariş")
_DAY_MONTH_PATTERN = re.compile(r"\b(\d{1,2})\s*([a-zA-ZçğıöşüÇĞİÖŞÜ]{3,})\b", flags=re.IGNORECASE)
_NUMERIC_DATE_PATTERN = re.compile(r"\b(\d{1,2})[./-](\d{1,2})(?:[./-](?:\d{2,4}))?\b")
_ADULT_COUNT_PATTERN = re.compile(
    r"\b(\d{1,2})\s*(?:yetiskin|yetişkin|adult|adults)\b",
    flags=re.IGNORECASE,
)
_TIME_OF_DAY_PATTERN = re.compile(r"\b(?:saat\s*)?(?:[01]?\d|2[0-3])[:.]([0-5]\d)\b", flags=re.IGNORECASE)
_STAY_MONTH_LABELS = {
    "ocak": "Ocak",
    "subat": "Subat",
    "mart": "Mart",
    "nisan": "Nisan",
    "mayis": "Mayis",
    "haziran": "Haziran",
    "temmuz": "Temmuz",
    "agustos": "Agustos",
    "eylul": "Eylul",
    "ekim": "Ekim",
    "kasim": "Kasim",
    "aralik": "Aralik",
    "january": "January",
    "february": "February",
    "march": "March",
    "april": "April",
    "may": "May",
    "june": "June",
    "july": "July",
    "august": "August",
    "september": "September",
    "october": "October",
    "november": "November",
    "december": "December",
}
_STAY_MONTH_ALIASES = {
    "oca": "ocak",
    "ocak": "ocak",
    "sub": "subat",
    "suba": "subat",
    "subat": "subat",
    "mart": "mart",
    "nis": "nisan",
    "nisa": "nisan",
    "nisan": "nisan",
    "may": "mayis",
    "mayi": "mayis",
    "mayis": "mayis",
    "haz": "haziran",
    "hazi": "haziran",
    "hazir": "haziran",
    "haziran": "haziran",
    "tem": "temmuz",
    "temm": "temmuz",
    "temmuz": "temmuz",
    "agu": "agustos",
    "agus": "agustos",
    "agusto": "agustos",
    "agustos": "agustos",
    "eyl": "eylul",
    "eylu": "eylul",
    "eylul": "eylul",
    "eki": "ekim",
    "ekim": "ekim",
    "kas": "kasim",
    "kasi": "kasim",
    "kasim": "kasim",
    "ara": "aralik",
    "aral": "aralik",
    "aralik": "aralik",
    "jan": "january",
    "janu": "january",
    "january": "january",
    "feb": "february",
    "febr": "february",
    "february": "february",
    "mar": "march",
    "march": "march",
    "apr": "april",
    "apri": "april",
    "april": "april",
    "jun": "june",
    "june": "june",
    "jul": "july",
    "july": "july",
    "aug": "august",
    "augu": "august",
    "august": "august",
    "sep": "september",
    "sept": "september",
    "september": "september",
    "oct": "october",
    "octo": "october",
    "october": "october",
    "nov": "november",
    "nove": "november",
    "november": "november",
    "dec": "december",
    "dece": "december",
    "december": "december",
}


def _resolve_tool_shortlist_names(conversation: Conversation, normalized_text: str) -> set[str]:
    """Select the smallest relevant tool subset for the current turn."""
    text = str(normalized_text or "").casefold()
    current_intent = str(conversation.current_intent.value if conversation.current_intent else "").casefold()

    shortlist = set(_GENERAL_TOOL_SHORTLIST)
    if any(token in current_intent for token in ("restaurant", "menu")) or any(
        token in text for token in _RESTAURANT_TOOL_HINTS
    ):
        shortlist.update(_RESTAURANT_TOOL_SHORTLIST)
    elif "transfer" in current_intent or any(token in text for token in _TRANSFER_TOOL_HINTS):
        shortlist.update(_TRANSFER_TOOL_SHORTLIST)
    elif "room_service" in current_intent or any(token in text for token in _ROOM_SERVICE_TOOL_HINTS):
        shortlist.update(_ROOM_SERVICE_TOOL_SHORTLIST)
    else:
        shortlist.update(_STAY_TOOL_SHORTLIST)
    return shortlist


def _select_tool_definitions_for_turn(
    conversation: Conversation,
    normalized_text: str,
    tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Filter the global tool list down to the relevant subset for this turn."""
    shortlist = _resolve_tool_shortlist_names(conversation, normalized_text)
    selected: list[dict[str, Any]] = []
    for tool in tools:
        function_block = tool.get("function") if isinstance(tool, dict) else None
        tool_name = str(function_block.get("name") or "").strip() if isinstance(function_block, dict) else ""
        if tool_name and tool_name in shortlist:
            selected.append(tool)
    return selected


def _sync_response_tool_calls(
    response: LLMResponse,
    executed_calls: list[dict[str, Any]] | None,
) -> None:
    """Prefer real executed tool calls; otherwise normalize parsed tool intents."""
    canonical_executed = _canonicalize_tool_calls(executed_calls, default_status="executed")
    if canonical_executed:
        response.internal_json.tool_calls = canonical_executed
        return
    response.internal_json.tool_calls = _canonicalize_tool_calls(
        response.internal_json.tool_calls,
        default_status="planned",
    )


def _merge_entities_with_context(
    previous_entities: dict[str, Any] | None,
    current_entities: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge current entities into previous context without erasing verified booking context."""
    merged: dict[str, Any] = dict(previous_entities or {})
    preserve_positive_int_keys = {
        "room_type_id",
        "board_type_id",
        "rate_type_id",
        "rate_code_id",
        "price_agency_id",
        "adults",
        "chd_count",
        "children",
    }
    preserve_non_empty_list_keys = {"chd_ages", "child_ages"}

    for key, value in (current_entities or {}).items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue

        previous_value = merged.get(key)
        if key in preserve_non_empty_list_keys:
            if isinstance(value, list) and not value and isinstance(previous_value, list) and previous_value:
                continue
        elif key in preserve_positive_int_keys:
            current_int = _to_int(value, 0)
            previous_int = _to_int(previous_value, 0)
            if current_int <= 0 and previous_int > 0:
                continue

        merged[key] = value

    normalized_child_ages = merged.get("chd_ages")
    if not isinstance(normalized_child_ages, list):
        normalized_child_ages = merged.get("child_ages")
    if isinstance(normalized_child_ages, list) and normalized_child_ages:
        age_count = sum(1 for age in normalized_child_ages if _to_int(age, -1) >= 0)
        if age_count > 0:
            if _to_int(merged.get("chd_count"), 0) <= 0:
                merged["chd_count"] = age_count
            if _to_int(merged.get("children"), 0) <= 0:
                merged["children"] = age_count

    return merged


def _sanitize_entities_for_intent(intent: str | None, entities: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only intent-safe entity fields to avoid cross-flow contamination."""
    source = dict(entities or {})
    normalized_intent = str(intent or '').strip().lower()
    if normalized_intent == 'restaurant_booking_create':
        allowed = {
            'hotel_id', 'date', 'time', 'party_size', 'guest_name', 'phone', 'notes', 'area',
            'restaurant_hold_id', 'slot_id', 'language', 'confirmation', 'source'
        }
        return {key: value for key, value in source.items() if key in allowed}
    if normalized_intent.startswith('restaurant_'):
        allowed = {
            'hotel_id', 'date', 'time', 'party_size', 'guest_name', 'phone', 'notes', 'area',
            'restaurant_hold_id', 'slot_id', 'language', 'confirmation', 'source'
        }
        return {key: value for key, value in source.items() if key in allowed}
    return source


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
        args = _loads_tool_payload(call.get("arguments"))
        checkin_raw = str(args.get("checkin_date") or "").strip()
        checkout_raw = str(args.get("checkout_date") or "").strip()
        required_dates: set[str] = set()
        try:
            checkin_date = date.fromisoformat(checkin_raw)
            checkout_date = date.fromisoformat(checkout_raw)
            cursor = checkin_date
            while cursor < checkout_date:
                required_dates.add(cursor.isoformat())
                cursor += timedelta(days=1)
        except ValueError:
            required_dates = set()

        rows = result.get("rows")
        if not isinstance(rows, list):
            rows = []

        room_date_coverage: dict[int, set[str]] = {}
        positive_rooms: set[int] = set()
        has_row_dates = False
        for row in rows:
            if not isinstance(row, dict):
                continue
            room_type_id = int(row.get("room_type_id", 0) or 0)
            if room_type_id <= 0:
                continue
            if bool(row.get("stop_sell")):
                continue
            if int(row.get("room_to_sell", 0) or 0) <= 0:
                continue
            positive_rooms.add(room_type_id)
            row_date = str(row.get("date") or "").strip()
            if row_date:
                has_row_dates = True
                room_date_coverage.setdefault(room_type_id, set()).add(row_date)

        eligible_from_rows: set[int] = set()
        if required_dates and has_row_dates:
            for room_type_id, covered_dates in room_date_coverage.items():
                if required_dates.issubset(covered_dates):
                    eligible_from_rows.add(room_type_id)
        else:
            eligible_from_rows = set(positive_rooms)

        for room_type_id in sorted(eligible_from_rows):
            if room_type_id in seen:
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


def _has_booking_availability_call(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when booking_availability already ran in this turn."""
    return any(str(call.get("name") or "") == "booking_availability" for call in executed_calls)


def _has_nonempty_availability_inventory(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when availability call returned any row/derived inventory signal."""
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_availability":
            continue
        result = _loads_tool_payload(call.get("result"))
        rows = result.get("rows")
        if isinstance(rows, list) and rows:
            return True
        derived = result.get("derived")
        if isinstance(derived, dict):
            eligible_ids = derived.get("eligible_room_type_ids")
            if isinstance(eligible_ids, list) and eligible_ids:
                return True
    return False


def _latest_booking_quote_args(executed_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return latest booking_quote arguments as dict."""
    for call in reversed(executed_calls):
        if str(call.get("name") or "") != "booking_quote":
            continue
        args = _loads_tool_payload(call.get("arguments"))
        if args:
            return args
    return {}


async def _backfill_availability_for_quote(
    *,
    conversation: Conversation,
    dispatcher: Any | None,
    executed_calls: list[dict[str, Any]],
) -> None:
    """Ensure quote responses have availability data for room filtering."""
    if dispatcher is None:
        return
    if _has_booking_availability_call(executed_calls):
        return
    quote_args = _latest_booking_quote_args(executed_calls)
    if not quote_args:
        return

    checkin_date = str(quote_args.get("checkin_date") or "").strip()
    checkout_date = str(quote_args.get("checkout_date") or "").strip()
    adults = _to_int(quote_args.get("adults"), 0)
    if not checkin_date or not checkout_date or adults <= 0:
        return

    availability_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults": adults,
        "chd_count": _to_int(quote_args.get("chd_count"), 0),
        "chd_ages": quote_args.get("chd_ages") if isinstance(quote_args.get("chd_ages"), list) else [],
        "currency": str(quote_args.get("currency") or "EUR").upper(),
    }
    result = await dispatcher.dispatch("booking_availability", **availability_args)
    if not isinstance(result, dict):
        return
    executed_calls.append(
        {
            "name": "booking_availability",
            "arguments": availability_args,
            "result": result,
        }
    )


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


def _extract_quote_fallback_room_type_ids(payloads: list[dict[str, Any]]) -> list[int]:
    """Derive room type ids from quote offers when availability rows are empty."""
    explicit_sellable_ids: list[int] = []
    implicit_offer_ids: list[int] = []
    seen_explicit: set[int] = set()
    seen_implicit: set[int] = set()

    for payload in payloads:
        offers = payload.get("offers")
        if not isinstance(offers, list):
            continue
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            room_type_id = int(offer.get("room_type_id", 0) or 0)
            if room_type_id <= 0:
                continue

            stop_sell_raw = offer.get("stop_sell")
            room_to_sell_raw = offer.get("room_to_sell")
            has_stop_sell = stop_sell_raw is not None
            has_room_to_sell = room_to_sell_raw is not None

            if has_stop_sell and bool(stop_sell_raw):
                continue
            if has_room_to_sell and int(room_to_sell_raw or 0) <= 0:
                continue

            if has_stop_sell or has_room_to_sell:
                if room_type_id in seen_explicit:
                    continue
                seen_explicit.add(room_type_id)
                explicit_sellable_ids.append(room_type_id)
                continue

            if room_type_id in seen_implicit:
                continue
            seen_implicit.add(room_type_id)
            implicit_offer_ids.append(room_type_id)

    if explicit_sellable_ids:
        return explicit_sellable_ids
    return implicit_offer_ids


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


def _extract_restaurant_capacity_handoff_context(executed_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return collected restaurant reservation context when restaurant flow requires handoff."""
    create_handoff_reasons = {"DAILY_CAPACITY_FULL", "NO_CAPACITY", "SLOT_NOT_AVAILABLE"}
    availability_handoff_reasons = {"NO_CAPACITY", "SLOT_NOT_AVAILABLE", "DAILY_CAPACITY_FULL"}
    availability_snapshot: dict[str, Any] = {}

    for call in reversed(executed_calls):
        tool_name = str(call.get("name") or "")
        result = _loads_tool_payload(call.get("result"))

        if tool_name == "restaurant_create_hold":
            if str(result.get("reason") or "") not in create_handoff_reasons:
                continue
            if not bool(result.get("handoff_required")):
                continue
            context = result.get("collected_reservation_context")
            if isinstance(context, dict):
                context_copy = dict(context)
                if result.get("guest_message"):
                    context_copy["guest_message"] = str(result.get("guest_message"))
                handoff_reason = str(result.get("reason") or "").strip()
                if handoff_reason:
                    context_copy["handoff_reason"] = handoff_reason
                return context_copy

        if tool_name == "restaurant_availability":
            if bool(result.get("available")):
                continue
            reason = str(result.get("reason") or "")
            if reason not in availability_handoff_reasons and reason:
                continue
            snapshot = result.get("collected_reservation_context")
            if isinstance(snapshot, dict):
                availability_snapshot = dict(snapshot)
            else:
                args = _loads_tool_payload(call.get("arguments") or call.get("args"))
                if not isinstance(args, dict):
                    args = {}
                availability_snapshot = {
                    "date": args.get("date"),
                    "time": args.get("time"),
                    "party_size": args.get("party_size"),
                    "area": args.get("area"),
                    "notes": args.get("notes"),
                }
            availability_snapshot["guest_message"] = "Sizleri canlı müşteri temsilcisine bağlıyorum."

    return availability_snapshot


def _build_restaurant_capacity_handoff_response(
    conversation: Conversation,
    executed_calls: list[dict[str, Any]],
    language: str,
) -> LLMResponse | None:
    """Create deterministic handoff when restaurant create flow cannot complete automatically."""
    context = _extract_restaurant_capacity_handoff_context(executed_calls)
    if not context:
        return None

    entities = _merge_entities_with_context(conversation.entities_json, context)
    raw_reason = str(context.get("handoff_reason") or "").strip().upper()
    handoff_reason = (
        "restaurant_daily_capacity_full"
        if raw_reason == "DAILY_CAPACITY_FULL"
        else "restaurant_capacity_or_slot_unavailable"
    )

    if language == "en":
        default_message = (
            "Our daily restaurant reservation quota is currently full. "
            "I am connecting you to a live customer representative now."
            if handoff_reason == "restaurant_daily_capacity_full"
            else "I am connecting you to a live customer representative now."
        )
    else:
        default_message = (
            "Gunluk restoran rezervasyon kotamiz su anda dolu. Sizleri canli musteri temsilcisine bagliyorum."
            if handoff_reason == "restaurant_daily_capacity_full"
            else "Sizleri canli musteri temsilcisine bagliyorum."
        )
    user_message = str(context.get("guest_message") or default_message)

    return LLMResponse(
        user_message=user_message,
        internal_json=InternalJSON(
            language=language,
            intent="restaurant_booking_create",
            state="HANDOFF",
            entities=entities,
            required_questions=[],
            handoff={"needed": True, "reason": handoff_reason},
            risk_flags=["RESTAURANT_CAPACITY_HANDOFF"],
            escalation={"level": "L2", "route_to_role": "ADMIN", "sla_hint": "high"},
            next_step="handoff_to_restaurant_team",
        ),
    )


def _is_out_of_season_tool_result(result: dict[str, Any]) -> bool:
    """Return True when tool payload indicates season rejection."""
    return str(result.get("reason") or "").strip().upper() == "OUT_OF_SEASON"


def _extract_stay_or_transfer_out_of_season_context(executed_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return context for deterministic stay/transfer season-rejection responses."""
    tool_intent_map = {
        "booking_availability": "stay_availability",
        "booking_quote": "stay_quote",
        "stay_create_hold": "stay_booking_create",
        "transfer_create_hold": "transfer_booking_create",
    }
    for call in reversed(executed_calls):
        tool_name = str(call.get("name") or "")
        intent = tool_intent_map.get(tool_name)
        if not intent:
            continue

        result = _loads_tool_payload(call.get("result"))
        if not _is_out_of_season_tool_result(result):
            continue

        args = _loads_tool_payload(call.get("arguments") or call.get("args"))
        if not isinstance(args, dict):
            args = {}

        reservation_type = "transfer" if tool_name == "transfer_create_hold" else "stay"
        context: dict[str, Any] = {
            "intent": intent,
            "reservation_type": reservation_type,
        }
        if reservation_type == "stay":
            checkin_date = args.get("checkin_date")
            checkout_date = args.get("checkout_date")
            if tool_name == "stay_create_hold":
                draft = args.get("draft")
                if isinstance(draft, dict):
                    checkin_date = draft.get("checkin_date", checkin_date)
                    checkout_date = draft.get("checkout_date", checkout_date)
            context["checkin_date"] = checkin_date
            context["checkout_date"] = checkout_date
            context["required_questions"] = ["checkin_date"]
            context["next_step"] = "collect_in_season_stay_date"
        else:
            context["date"] = args.get("date")
            context["required_questions"] = ["date"]
            context["next_step"] = "collect_in_season_transfer_date"

        season = result.get("season")
        if isinstance(season, dict):
            context["season"] = {
                "open": str(season.get("open") or ""),
                "close": str(season.get("close") or ""),
            }
        return context
    return {}


def _build_stay_or_transfer_out_of_season_response(
    conversation: Conversation,
    executed_calls: list[dict[str, Any]],
    language: str,
) -> LLMResponse | None:
    """Create deterministic guest response for stay/transfer out-of-season requests."""
    context = _extract_stay_or_transfer_out_of_season_context(executed_calls)
    if not context:
        return None

    entities = _merge_entities_with_context(conversation.entities_json, context)
    reservation_type = str(context.get("reservation_type") or "stay")
    profile = get_profile(conversation.hotel_id)
    season = context.get("season") if isinstance(context.get("season"), dict) else getattr(profile, "season", {})
    return LLMResponse(
        user_message=_reservation_season_unavailable_message(
            language,
            season if isinstance(season, dict) else {},
            reservation_type=reservation_type,
        ),
        internal_json=InternalJSON(
            language=language,
            intent=str(context.get("intent") or "stay_availability"),
            state="NEEDS_VERIFICATION",
            entities=entities,
            required_questions=list(context.get("required_questions") or []),
            handoff={"needed": False, "reason": None},
            risk_flags=["DATE_INVALID"],
            next_step=str(context.get("next_step") or "collect_in_season_date"),
        ),
    )


def _extract_restaurant_unavailable_context(executed_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return context for deterministic restaurant unavailability responses."""
    supported_reasons = {"OUT_OF_SEASON", "OUTSIDE_RESTAURANT_HOURS"}
    for call in reversed(executed_calls):
        tool_name = str(call.get("name") or "")
        if tool_name not in {"restaurant_availability", "restaurant_create_hold"}:
            continue

        result = _loads_tool_payload(call.get("result"))
        reason = str(result.get("reason") or "").strip().upper()
        options = result.get("options")
        available = bool(result.get("available"))

        if reason not in supported_reasons and (available or not isinstance(options, list) or options):
            continue

        args = _loads_tool_payload(call.get("arguments") or call.get("args"))
        context: dict[str, Any] = {
            "reason": reason or "NO_AVAILABILITY_MATCH",
            "date": args.get("date"),
            "time": args.get("time"),
            "party_size": args.get("party_size"),
            "guest_name": args.get("guest_name"),
            "phone": args.get("phone"),
            "area": args.get("area"),
            "notes": args.get("notes"),
        }
        season = result.get("season")
        if isinstance(season, dict):
            context["season"] = {
                "open": str(season.get("open") or ""),
                "close": str(season.get("close") or ""),
            }
        return context
    return {}


def _build_restaurant_unavailable_response(
    conversation: Conversation,
    executed_calls: list[dict[str, Any]],
    language: str,
) -> LLMResponse | None:
    """Create deterministic guest response for restaurant season/hours/unavailable cases."""
    context = _extract_restaurant_unavailable_context(executed_calls)
    if not context:
        return None

    entities = _merge_entities_with_context(conversation.entities_json, context)
    reason = str(context.get("reason") or "").upper()
    profile = get_profile(conversation.hotel_id)
    if reason == "OUT_OF_SEASON":
        season = context.get("season") if isinstance(context.get("season"), dict) else getattr(profile, "season", {})
        return LLMResponse(
            user_message=_restaurant_season_unavailable_message(language, season if isinstance(season, dict) else {}),
            internal_json=InternalJSON(
                language=language,
                intent="restaurant_booking_create",
                state="NEEDS_VERIFICATION",
                entities=entities,
                required_questions=["date"],
                handoff={"needed": False, "reason": None},
                risk_flags=["DATE_INVALID"],
                next_step="collect_in_season_restaurant_date",
            ),
        )
    if reason == "OUTSIDE_RESTAURANT_HOURS":
        return LLMResponse(
            user_message=_restaurant_hours_unavailable_message(language, profile),
            internal_json=InternalJSON(
                language=language,
                intent="restaurant_booking_create",
                state="NEEDS_VERIFICATION",
                entities=entities,
                required_questions=["time"],
                handoff={"needed": False, "reason": None},
                risk_flags=[],
                next_step="collect_restaurant_time_within_hours",
            ),
        )
    return LLMResponse(
        user_message=_restaurant_unavailable_message(language),
        internal_json=InternalJSON(
            language=language,
            intent="restaurant_booking_create",
            state="NEEDS_VERIFICATION",
            entities=entities,
            required_questions=["time"],
            handoff={"needed": False, "reason": None},
            risk_flags=[],
            next_step="collect_alternative_restaurant_time",
        ),
    )


def _build_structured_output_error_response(
    language: str,
    reason: str,
    conversation: Conversation | None = None,
) -> LLMResponse:
    """Return a safe retry prompt when the model fails to emit valid INTERNAL_JSON."""
    normalized_reason = str(reason or "").strip() or "unknown"
    record_structured_output_fallback(normalized_reason)
    preserved_entities = (
        dict(conversation.entities_json)
        if conversation is not None and isinstance(conversation.entities_json, dict)
        else {}
    )
    preserved_entities = _merge_entities_with_context(
        preserved_entities,
        {
            "response_parser": {
                "applied": True,
                "reason": normalized_reason,
            }
        },
    )
    preserved_state = (
        str(conversation.current_state or "NEEDS_VERIFICATION")
        if conversation is not None
        else "NEEDS_VERIFICATION"
    )
    if preserved_state in {"", "GREETING", "HANDOFF", "CLOSED"}:
        preserved_state = "NEEDS_VERIFICATION"
    preserved_intent = (
        str(conversation.current_intent.value if conversation.current_intent else "other")
        if conversation is not None
        else "other"
    )
    risk_flags = list(conversation.risk_flags) if conversation is not None else []
    if "STRUCTURED_OUTPUT_ERROR" not in risk_flags:
        risk_flags.append("STRUCTURED_OUTPUT_ERROR")
    return LLMResponse(
        user_message=response_validation_fallback(language),
        internal_json=InternalJSON(
            language=language,
            intent=preserved_intent,
            state=preserved_state,
            entities=preserved_entities,
            required_questions=[],
            handoff={"needed": False, "reason": None},
            risk_flags=risk_flags,
            next_step="restate_guest_request",
        ),
    )


async def _attempt_structured_output_repair(
    *,
    llm_client: Any,
    raw_content: str,
    language: str,
    parser_error_reason: str,
    conversation: Conversation,
    executed_calls: list[dict[str, Any]],
) -> LLMResponse | None:
    """Try a strict-schema repair pass before falling back to a generic retry prompt."""
    repair_fn = getattr(llm_client, "repair_structured_output", None)
    if not callable(repair_fn):
        return None

    repaired_payload = await repair_fn(
        raw_content=raw_content,
        language=language,
        parser_error_reason=parser_error_reason,
        current_intent=conversation.current_intent.value if conversation.current_intent else "other",
        current_state=str(conversation.current_state or "NEEDS_VERIFICATION"),
        current_entities=conversation.entities_json,
        executed_calls=executed_calls,
    )
    if not isinstance(repaired_payload, dict):
        return None

    user_message = str(repaired_payload.get("user_message") or "").strip()
    internal_payload = repaired_payload.get("internal_json")
    if not user_message or not isinstance(internal_payload, dict):
        record_structured_output_repair_outcome("missing_fields")
        logger.warning(
            "llm_structured_output_repair_missing_fields",
            has_user_message=bool(user_message),
            has_internal_json=isinstance(internal_payload, dict),
        )
        return None

    try:
        repaired_internal = ResponseParser.validate_internal_json(internal_payload)
    except Exception:
        record_structured_output_repair_outcome("validation_failed")
        logger.warning("llm_structured_output_repair_validation_failed")
        return None

    record_structured_output_repair_outcome("applied")
    logger.info(
        "llm_structured_output_repair_applied",
        conversation_id=str(conversation.id) if conversation.id is not None else None,
        parser_error_reason=parser_error_reason,
        executed_call_count=len(executed_calls),
    )
    return LLMResponse(user_message=user_message, internal_json=repaired_internal)


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


def _is_room_type_identification_question(user_text: str) -> bool:
    """Detect image follow-up questions that ask to identify a room type."""
    normalized = _normalize_language_text(user_text)
    keywords = (
        "oda tipi",
        "oda turu",
        "hangi oda tipi",
        "hangi oda",
        "room type",
        "which room type",
        "what room type",
        "какой тип номера",
        "тип номера",
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


def _strip_language_detection_noise(text: str) -> str:
    """Strip URL-heavy and technical noise before language hint scoring."""
    without_urls = URL_PATTERN.sub(" ", text)
    if not without_urls.strip():
        return ""
    cleaned_tokens: list[str] = []
    for raw_token in without_urls.split():
        token = raw_token.strip(".,;:!?()[]{}<>\"'")
        if not token:
            continue
        lowered = token.casefold()
        if lowered in TECHNICAL_LINK_TOKENS:
            continue
        if URL_LIKE_TOKEN_PATTERN.match(lowered):
            continue
        if any(character in token for character in ("/", "=", "&", "?", "%", "#")):
            continue
        cleaned_tokens.append(token)
    return " ".join(cleaned_tokens)


def _detect_message_language(text: str, fallback: str = "tr", *, sticky_mode: bool = False) -> str:
    """Detect guest message language with lightweight heuristics."""
    safe_fallback = fallback if fallback in SUPPORTED_LANGUAGE_CODES else "tr"
    cleaned_text = _strip_language_detection_noise(text)
    normalized = _normalize_language_text(cleaned_text)
    if not normalized:
        return safe_fallback

    for pattern, language_code in SCRIPT_LANGUAGE_PATTERNS:
        if pattern.search(cleaned_text):
            return language_code

    scores = {
        language_code: sum(1 for keyword in keywords if _contains_keyword(normalized, keyword))
        for language_code, keywords in LANGUAGE_HINTS.items()
    }
    if re.search(r"[çğış]", cleaned_text.casefold()):
        scores["tr"] += 2

    best_language = max(scores, key=lambda language_code: scores[language_code])
    best_score = scores[best_language]
    if best_score > 0:
        top_languages = [language_code for language_code, score in scores.items() if score == best_score]
        if len(top_languages) == 1:
            if not sticky_mode or best_language == safe_fallback:
                return best_language
            sorted_scores = sorted(scores.values(), reverse=True)
            second_best = sorted_scores[1] if len(sorted_scores) > 1 else 0
            if (
                best_score >= LANGUAGE_SWITCH_MIN_SCORE
                and (best_score - second_best) >= LANGUAGE_SWITCH_MIN_MARGIN
            ):
                return best_language
            return safe_fallback
    if safe_fallback in SUPPORTED_LANGUAGE_CODES:
        return safe_fallback
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
    _ = entities
    profile = get_profile(hotel_id)
    default_note = (
        "2 çocuklu konaklamalarda oda tipine ve uygunluğa göre 2 ek yatak veya "
        "1 ek yatak + 1 sofa hazırlanabilir."
    )
    bedding_note = default_note
    if profile is not None:
        children_policy = profile.facility_policies.get("children", {})
        configured_note = children_policy.get("bedding_note_tr")
        if isinstance(configured_note, str) and configured_note.strip():
            bedding_note = configured_note.strip()

    return f"{bedding_note}\n\nHangisini tercih edersiniz?"


def _has_recent_media_analysis_context(conversation: Conversation) -> bool:
    """Return True when recent conversation context includes media analysis output."""
    recent_messages = conversation.messages[-6:] if conversation.messages else []
    for message in reversed(recent_messages):
        internal = message.internal_json if isinstance(message.internal_json, dict) else {}
        entities = internal.get("entities")
        if isinstance(entities, dict) and isinstance(entities.get("media_analysis"), dict):
            return True

    entities_json = conversation.entities_json if isinstance(conversation.entities_json, dict) else {}
    return isinstance(entities_json.get("media_analysis"), dict)


def _list_profile_room_type_names(hotel_id: int, language: str) -> list[str]:
    """Return configured room type names from HOTEL_PROFILE in a stable order."""
    profile = get_profile(hotel_id)
    if profile is None:
        return []

    preferred_language = "tr" if language == "tr" else "en"
    names: list[str] = []
    for room_type in getattr(profile, "room_types", []):
        localized = getattr(room_type, "name", None)
        selected = str(getattr(localized, preferred_language, "") or "").strip()
        fallback = str(getattr(localized, "tr", "") or getattr(localized, "en", "") or "").strip()
        name = selected or fallback
        if name:
            names.append(name)
    return list(dict.fromkeys(names))


def _build_media_room_type_grounded_response(hotel_id: int, language: str) -> LLMResponse:
    """Build deterministic room-type response grounded only in HOTEL_PROFILE data."""
    room_names = _list_profile_room_type_names(hotel_id, language)
    room_names_text = ", ".join(room_names) if room_names else "-"

    if language == "en":
        user_message = (
            "I cannot confirm the exact room type only from this image.\n\n"
            f"Room types configured in our system: {room_names_text}.\n\n"
            "If you share check-in/check-out dates and number of guests, "
            "I can verify live availability and rates for these room types."
        )
    elif language == "ru":
        user_message = (
            "По одному фото я не могу точно подтвердить тип номера.\n\n"
            f"Типы номеров в нашей системе: {room_names_text}.\n\n"
            "Если укажете даты заезда/выезда и количество гостей, "
            "я проверю актуальную доступность и цены по этим типам."
        )
    else:
        user_message = (
            "Bu görselden oda tipini tek başına kesin doğrulayamıyorum.\n\n"
            f"Sistemimizde tanımlı oda tipleri: {room_names_text}.\n\n"
            "Giriş-çıkış tarihi ve kişi sayısını paylaşırsanız, "
            "bu oda tipleri için canlı müsaitlik ve fiyatı hemen kontrol edebilirim."
        )

    return LLMResponse(
        user_message=user_message,
        internal_json=InternalJSON(
            language=language,
            intent="stay_quote",
            state="NEEDS_VERIFICATION",
            entities={},
            required_questions=["checkin_date", "checkout_date", "adults"],
            tool_calls=[],
            notifications=[],
            handoff={"needed": False},
            risk_flags=[],
            escalation={"level": "L0", "route_to_role": "NONE"},
            next_step="ask_clarifying_question",
        ),
    )


def _profile_room_aliases_canonical(hotel_id: int) -> set[str]:
    """Return canonical room aliases defined in HOTEL_PROFILE."""
    profile = get_profile(hotel_id)
    if profile is None:
        return set()

    aliases: set[str] = set()
    for room_type in getattr(profile, "room_types", []):
        localized = getattr(room_type, "name", None)
        for candidate in (
            str(getattr(localized, "tr", "") or "").strip(),
            str(getattr(localized, "en", "") or "").strip(),
        ):
            canonical = _canonical_text(candidate)
            if canonical:
                aliases.add(canonical)
    return aliases


def _contains_profile_unsupported_room_taxonomy(text: str, hotel_id: int) -> bool:
    """Detect room class terms that are not present in HOTEL_PROFILE room names."""
    canonical_text = _canonical_text(text)
    if not canonical_text:
        return False

    profile_aliases = _profile_room_aliases_canonical(hotel_id)
    unsupported_terms = (
        "standard",
        "standart",
        "suite",
        "suit",
        "suitoda",
        "suitroom",
    )
    for term in unsupported_terms:
        if term in canonical_text and all(term not in alias for alias in profile_aliases):
            return True
    return False


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
    if "kontrat" in normalized_rate or "contract" in normalized_rate:
        return "CONTRACT"
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
    requested_room_type_id: int = 0,
) -> str | None:
    """Build deterministic room blocks from merged quote offers."""
    grouped_offers: dict[Any, dict[str, Any]] = {}
    for offer in offers_for_call:
        if requested_room_type_id > 0 and _to_int(offer.get("room_type_id"), 0) != requested_room_type_id:
            continue
        policy_key = _resolve_quote_policy_key(offer, profile)
        if policy_key not in {"FREE_CANCEL", "NON_REFUNDABLE"}:
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
    requested_room_type_id: int = 0,
) -> str | None:
    """Build one Turkish customer-facing quote message for one room occupancy."""
    arguments_raw = payload.get("arguments")
    arguments: dict[str, Any] = cast(dict[str, Any], arguments_raw) if isinstance(arguments_raw, dict) else {}
    offers = payload.get("offers")
    if not isinstance(offers, list):
        return None
    offer_blocks = _build_offer_blocks_for_payload(
        offers,
        profile=profile,
        room_order=room_order,
        requested_room_type_id=requested_room_type_id,
    )
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
    *,
    user_text: str = "",
    entities: dict[str, Any] | None = None,
) -> list[str]:
    """Format Turkish quote replies as one or multiple customer messages."""
    payloads = _extract_quote_call_payloads(executed_calls)
    if not payloads:
        offers = _extract_quote_offers(executed_calls)
        if not offers:
            return []
        payloads = [{"arguments": {}, "offers": offers}]
    has_availability_call = _has_booking_availability_call(executed_calls)
    available_room_type_ids = _extract_available_room_type_ids(executed_calls)
    if has_availability_call and not available_room_type_ids:
        if _has_nonempty_availability_inventory(executed_calls):
            return [TR_NO_AVAILABLE_ROOM_FOR_QUOTE]
        quote_fallback_room_type_ids = _extract_quote_fallback_room_type_ids(payloads)
        if not quote_fallback_room_type_ids:
            return [TR_NO_AVAILABLE_ROOM_FOR_QUOTE]
        available_room_type_ids = quote_fallback_room_type_ids
    payloads = _filter_quote_payloads_by_available_room_types(payloads, available_room_type_ids)
    if not payloads and has_availability_call:
        return [TR_NO_AVAILABLE_ROOM_FOR_QUOTE]
    grouped_payloads = _group_quote_payloads(payloads)

    profile = get_profile(hotel_id)
    explicit_room_request = False
    requested_room_type_id = 0
    if isinstance(entities, dict):
        explicit_room_request, requested_room_type_id = _guest_explicitly_requested_room_type(
            user_text,
            entities,
            profile,
        )
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
            requested_room_type_id=requested_room_type_id if explicit_room_request else 0,
        )
        return [single_message] if single_message else []

    messages: list[str] = []
    for index, payload in enumerate(grouped_payloads, start=1):
        message = _build_stay_quote_message_for_payload(
            payload,
            profile=profile,
            room_order=room_order,
            room_header=f"{index}. Oda",
            requested_room_type_id=requested_room_type_id if explicit_room_request else 0,
        )
        if message:
            messages.append(message)
    return messages


def _build_deterministic_turkish_stay_quote_reply(
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
    *,
    user_text: str = "",
    entities: dict[str, Any] | None = None,
) -> str | None:
    """Return the first deterministic Turkish quote message for compatibility."""
    messages = _build_deterministic_turkish_stay_quote_messages(
        hotel_id,
        executed_calls,
        user_text=user_text,
        entities=entities,
    )
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


def _current_reservation_year() -> int:
    """Return runtime current year used for reservation date defaults."""
    return datetime.now(UTC).year


def _extract_explicit_year_values(user_text: str) -> list[int]:
    """Extract explicit 4-digit year mentions from user text."""
    years: list[int] = []
    for match in EXPLICIT_YEAR_PATTERN.finditer(user_text):
        try:
            year = int(match.group(0))
        except ValueError:
            continue
        if year not in years:
            years.append(year)
    return years


def _extract_non_current_year(user_text: str, *, current_year: int | None = None) -> int | None:
    """Return the first explicit year that differs from the runtime current year."""
    active_year = current_year if current_year is not None else _current_reservation_year()
    for year in _extract_explicit_year_values(user_text):
        if year != active_year:
            return year
    return None


def _is_reservation_intent(intent: str) -> bool:
    """Return True when intent belongs to stay/restaurant/transfer reservation flows."""
    return str(intent or "").strip().lower().startswith(RESERVATION_INTENT_PREFIXES)


def _reservation_year_handoff_message(language: str, requested_year: int, current_year: int) -> str:
    """Return guest-facing handoff message for non-current-year reservation requests."""
    if language == "en":
        return (
            f"Our automatic flow uses {current_year} by default. "
            f"To handle reservation requests for {requested_year} correctly, "
            "I am connecting you to our live team now."
        )
    if language == "ru":
        return (
            f"По умолчанию автоматический поток работает с {current_year} годом. "
            f"Чтобы корректно оформить запрос на бронирование на {requested_year} год, "
            "я сейчас подключаю вас к нашей живой команде."
        )
    return (
        f"Otomatik akışta varsayılan yıl {current_year}. "
        f"{requested_year} yılı için rezervasyon talebinizi doğru şekilde ilerletebilmek adına "
        "sizi canlı ekibimize yönlendiriyorum."
    )


def _reservation_no_year_followup_message(language: str) -> str:
    """Return a year-free fallback prompt when only year clarification was removed."""
    if language == "en":
        return "If you share your date range and guest count, I can continue right away."
    if language == "ru":
        return "Если укажете диапазон дат и количество гостей, я сразу продолжу."
    return "Tarih aralığı ve kişi sayısını netleştirirseniz hemen devam edebilirim."


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
    _user_text: str,
) -> None:
    """Remove year-only clarification prompts from reservation verification flows."""
    intent = str(response.internal_json.intent or "").lower()
    if not _is_reservation_intent(intent):
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
        language = str(response.internal_json.language or "tr").lower()
        response.user_message = _reservation_no_year_followup_message(language)


def _apply_non_current_year_reservation_handoff(
    response: LLMResponse,
    *,
    requested_year: int,
    current_year: int,
) -> None:
    """Force human handoff when guest explicitly requests a non-current reservation year."""
    language = str(response.internal_json.language or "tr").lower()
    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    entities["requested_year"] = requested_year
    entities["current_year"] = current_year
    response.internal_json.entities = entities

    risk_flags = list(response.internal_json.risk_flags or [])
    if "NON_CURRENT_YEAR_REQUEST" not in risk_flags:
        risk_flags.append("NON_CURRENT_YEAR_REQUEST")

    response.user_message = _reservation_year_handoff_message(
        language,
        requested_year=requested_year,
        current_year=current_year,
    )
    response.internal_json.state = "HANDOFF"
    response.internal_json.required_questions = []
    response.internal_json.handoff = {"needed": True, "reason": "reservation_non_current_year"}
    response.internal_json.risk_flags = risk_flags
    response.internal_json.escalation = {"level": "L1", "route_to_role": "ADMIN", "sla_hint": "medium"}
    response.internal_json.next_step = "handoff_to_reservations_team"


def _normalize_restaurant_area_value(value: Any) -> str:
    """Normalize restaurant area labels into canonical indoor/outdoor buckets."""
    normalized = _canonical_text(str(value or ""))
    if normalized in {"outdoor", "outdoorarea", "dismekan", "acikalan", "acik"}:
        return "outdoor"
    if normalized in {"indoor", "indoorarea", "icmekan", "kapalialan", "kapali"}:
        return "indoor"
    return normalized


def _single_restaurant_area_type(hotel_id: int) -> str:
    """Return canonical area type only when hotel profile exposes exactly one restaurant area."""
    profile = get_profile(hotel_id)
    restaurant = getattr(profile, "restaurant", None)
    raw_area_types = getattr(restaurant, "area_types", []) if restaurant is not None else []
    normalized_area_types: list[str] = []
    for item in raw_area_types or []:
        normalized = _normalize_restaurant_area_value(item)
        if normalized and normalized not in normalized_area_types:
            normalized_area_types.append(normalized)
    if len(normalized_area_types) == 1:
        return normalized_area_types[0]
    return ""


def _contains_restaurant_area_prompt(text: str) -> bool:
    """Detect follow-up prompts that ask the guest to choose indoor/outdoor seating."""
    if not text:
        return False
    if RESTAURANT_AREA_PROMPT_PATTERN.search(text):
        return True
    normalized = _normalize_language_text(text)
    return any(
        _contains_keyword(normalized, keyword)
        for keyword in ("alan tercihi", "hangi alan", "teras", "bahce", "garden", "patio")
    )


def _restaurant_missing_required_fields(entities: dict[str, Any]) -> list[str]:
    """Return missing restaurant reservation fields in collection order."""
    missing: list[str] = []
    if not bool(str(entities.get("date") or "").strip()):
        missing.append("date")
    if not bool(str(entities.get("time") or "").strip()):
        missing.append("time")
    if _to_int(entities.get("party_size"), 0) <= 0:
        missing.append("party_size")
    if not bool(str(entities.get("guest_name") or "").strip()):
        missing.append("guest_name")
    if not bool(str(entities.get("phone") or "").strip()):
        missing.append("phone")
    return missing


def _restaurant_tool_progress_message(language: str) -> str:
    """Guest-facing progress message once restaurant slot checking can begin."""
    if language == "en":
        return "I have the necessary details. I am checking restaurant availability now."
    if language == "ru":
        return "У меня есть вся необходимая информация. Сейчас проверяю наличие мест в ресторане."
    return "Gerekli bilgileri aldim. Restoran uygunlugunu simdi kontrol ediyorum."


def _suppress_restaurant_area_question(response: LLMResponse, hotel_id: int) -> None:
    """Do not ask indoor/outdoor when the hotel profile exposes only one restaurant area type."""
    if str(response.internal_json.intent or "").lower() != "restaurant_booking_create":
        return

    single_area_type = _single_restaurant_area_type(hotel_id)
    if not single_area_type:
        return

    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    if not str(entities.get("area") or "").strip():
        entities["area"] = single_area_type
        response.internal_json.entities = entities

    original_required = [
        str(item).strip()
        for item in response.internal_json.required_questions
        if isinstance(item, str) and str(item).strip()
    ]
    filtered_required = [
        question
        for question in original_required
        if _canonical_required_question_key(question) != "area"
    ]
    removed_area_requirement = len(filtered_required) != len(original_required)
    response.internal_json.required_questions = filtered_required

    current_message = str(response.user_message or "").strip()
    if not removed_area_requirement and not _contains_restaurant_area_prompt(current_message):
        return

    language = str(response.internal_json.language or "tr").lower()
    if filtered_required:
        response.user_message = _single_field_prompt(language, filtered_required[0])
        return

    missing_required = _restaurant_missing_required_fields(entities)
    if missing_required:
        response.internal_json.required_questions = [missing_required[0]]
        response.user_message = _single_field_prompt(language, missing_required[0])
        return

    response.internal_json.required_questions = []
    response.internal_json.state = "READY_FOR_TOOL"
    response.internal_json.next_step = "run_restaurant_availability"
    response.user_message = _restaurant_tool_progress_message(language)


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
    if any(token in normalized for token in ("area", "alan", "indoor", "outdoor", "icmekan", "dismekan")):
        return "area"
    if "date" in normalized or "tarih" in normalized:
        return "date"
    if "time" in normalized or "saat" in normalized:
        return "time"
    if any(token in normalized for token in ("party", "paxcount", "kisisayisi")):
        return "party_size"
    if any(token in normalized for token in ("notes", "not", "specialrequest", "ozelistek")):
        return "notes"
    return question.strip()


def _phone_collection_prompt(language: str) -> str:
    """Return single-message phone collection flow with current-number shortcut options."""
    if language == "en":
        return (
            "To make it easier for us to send your reservation confirmation and contact you during the next steps:\n\n"
            "Would you like us to save your current WhatsApp number in our system?\n"
            "If you prefer to use a different number, you may share it with us.\n\n"
            "Please indicate your choice by typing the number: 1 or 2.\n"
            "1) Save my current WhatsApp number\n"
            "2) I will share a different number"
        )
    if language == "ru":
        return (
            "Чтобы нам было удобнее отправить подтверждение бронирования и связаться с вами на следующих шагах:\n\n"
            "Сохранить ваш текущий номер WhatsApp в системе?\n"
            "Если хотите использовать другой номер, можете отправить его нам.\n\n"
            "Пожалуйста, укажите выбор цифрой: 1 или 2.\n"
            "1) Сохранить текущий номер WhatsApp\n"
            "2) Укажу другой номер"
        )
    return (
        "Rezervasyon onayını gönderebilmemiz ve sonraki adımlarda size ulaşabilmemiz için:\n\n"
        "Mevcut WhatsApp numaranızı sistemimize kaydedelim mi?\n"
        "Farklı bir numara kullanmak isterseniz bizimle paylaşabilirsiniz.\n\n"
        "Lütfen seçiminizi numara yazarak belirtin: 1 veya 2.\n"
        "1) Mevcut WhatsApp numaramı kaydet\n"
        "2) Farklı bir numara paylaşacağım"
    )


def _different_phone_followup_message(language: str) -> str:
    """Return follow-up prompt when guest selects sharing a different phone number."""
    if language == "en":
        return "Please share the different phone number you would like us to save. (+country code)"
    if language == "ru":
        return "Пожалуйста, укажите другой номер телефона, который хотите сохранить. (+код страны)"
    return "Kaydetmemizi istediğiniz farklı telefon numarasını paylaşır mısınız? (+ülke kodu ile)"


def _phone_saved_message(language: str) -> str:
    """Return acknowledgement after current WhatsApp number is accepted for contact."""
    if language == "en":
        return "Great, I have saved your current WhatsApp number for contact."
    if language == "ru":
        return "Отлично, я сохранил(а) ваш текущий номер WhatsApp для связи."
    return "Harika, mevcut WhatsApp numaranızı iletişim için kaydettim."


def _normalize_phone_for_collection(phone: str) -> str:
    """Normalize phone into E.164-like format for reservation entities."""
    cleaned = "".join(char for char in str(phone or "").strip() if char.isdigit() or char == "+")
    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"
    if cleaned and not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"
    digit_count = len(cleaned.replace("+", ""))
    if digit_count < 10 or digit_count > 15:
        return ""
    return cleaned


def _parse_phone_collection_choice(user_text: str) -> str:
    """Return parsed phone-choice action from guest reply."""
    canonical = _canonical_text(user_text)
    if canonical in PHONE_CHOICE_DIFFERENT_VALUES:
        return "share_different"
    if canonical in PHONE_CHOICE_USE_CURRENT_VALUES:
        return "use_current"
    if any(token in canonical for token in ("farkli", "farklı", "different")):
        return "share_different"
    if any(token in canonical for token in ("mevcut", "current", "whatsapp")):
        return "use_current"
    return ""


def _response_requests_phone(response: LLMResponse) -> bool:
    """Return True when parsed response expects phone collection from guest."""
    required_questions = [
        str(item).strip()
        for item in response.internal_json.required_questions
        if isinstance(item, str) and str(item).strip()
    ]
    if any(_canonical_required_question_key(item) == "phone" for item in required_questions):
        return True

    next_step = _canonical_text(str(response.internal_json.next_step or ""))
    return "phone" in next_step or "telefon" in next_step


def _contains_phone_prompt_indicator(text: str) -> bool:
    """Return True when text likely asks the guest for a phone number."""
    if not text:
        return False
    lowered = text.casefold()
    return "telefon" in lowered or "phone" in lowered or "whatsapp" in lowered


def _sanitize_phone_entity(
    entities: dict[str, Any],
    *,
    current_whatsapp_phone: str | None,
) -> dict[str, Any]:
    """Normalize phone entity and replace placeholders with current WhatsApp number."""
    raw_phone = str(entities.get("phone") or "").strip()
    if not raw_phone:
        return entities

    canonical = _canonical_text(raw_phone)
    if canonical in PHONE_PLACEHOLDER_VALUES:
        normalized = _normalize_phone_for_collection(current_whatsapp_phone or "")
        if normalized:
            entities["phone"] = normalized
            entities["phone_source"] = "whatsapp_current_number"
        else:
            entities.pop("phone", None)
        return entities

    normalized = _normalize_phone_for_collection(raw_phone)
    if normalized:
        entities["phone"] = normalized
        return entities

    entities.pop("phone", None)
    return entities


def _force_stay_intent_when_hold_ready(
    response: LLMResponse,
    *,
    conversation: Conversation,
    entities: dict[str, Any],
) -> None:
    """Clamp stay intent/state when hold creation is clearly next."""
    current_intent = str(response.internal_json.intent or "").lower().strip()
    if current_intent == "stay_booking_create":
        return

    next_step = _canonical_text(str(response.internal_json.next_step or ""))
    if "staycreatehold" not in next_step:
        return

    has_dates = bool(str(entities.get("checkin_date") or "").strip()) and bool(
        str(entities.get("checkout_date") or "").strip()
    )
    has_adults = _to_int(entities.get("adults"), 0) > 0
    has_guest = bool(str(entities.get("guest_name") or "").strip())
    has_phone = bool(str(entities.get("phone") or "").strip())
    has_context_intent = str(conversation.current_intent or "").lower().startswith("stay_")

    if not (has_context_intent or (has_dates and has_adults and has_guest and has_phone)):
        return

    response.internal_json.intent = "stay_booking_create"
    if str(response.internal_json.state or "").upper() == "NEEDS_VERIFICATION":
        required = [
            str(item).strip()
            for item in response.internal_json.required_questions
            if isinstance(item, str) and str(item).strip()
        ]
        if not required:
            response.internal_json.state = "READY_FOR_TOOL"


def _enforce_phone_collection_prompt(response: LLMResponse) -> None:
    """Ensure phone collection uses the WhatsApp-number choice template."""
    if str(response.internal_json.state or "").upper() == "HANDOFF":
        return
    if not _response_requests_phone(response):
        return

    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    if str(entities.get("phone") or "").strip():
        return

    language = str(response.internal_json.language or "tr").lower()
    current_message = str(response.user_message or "").strip()
    if current_message == _different_phone_followup_message(language):
        return
    if current_message == _phone_saved_message(language):
        return

    required = [
        str(item).strip()
        for item in response.internal_json.required_questions
        if isinstance(item, str) and str(item).strip()
    ]
    has_phone_required = any(_canonical_required_question_key(item) == "phone" for item in required)
    next_step = _canonical_text(str(response.internal_json.next_step or ""))
    next_step_mentions_phone = "phone" in next_step or "telefon" in next_step

    if has_phone_required:
        if len(required) > 1 and not _contains_phone_prompt_indicator(current_message):
            return
    else:
        if not (next_step_mentions_phone and _contains_phone_prompt_indicator(current_message)):
            return

    response.user_message = _phone_collection_prompt(language)
    if not has_phone_required:
        response.internal_json.required_questions = ["phone", *required]


def _inject_phone_choice_signal(
    *,
    conversation: Conversation,
    user_text: str,
    current_whatsapp_phone: str | None,
) -> str:
    """Rewrite bare 1/2 replies into explicit phone intents so the LLM can resolve them deterministically."""
    if not current_whatsapp_phone:
        return user_text
    if not _is_reservation_intent(str(conversation.current_intent or "")):
        return user_text

    entities = conversation.entities_json if isinstance(conversation.entities_json, dict) else {}
    if bool(str(entities.get("phone") or "").strip()):
        return user_text

    choice = _parse_phone_collection_choice(user_text)
    if not choice:
        return user_text

    if choice == "share_different":
        return "I want to use a different phone number for reservation contact."

    normalized_phone = _normalize_phone_for_collection(current_whatsapp_phone)
    if not normalized_phone:
        return user_text
    return f"Use this WhatsApp number for reservation contact: {normalized_phone}"


def _apply_phone_collection_choice_override(
    response: LLMResponse,
    *,
    user_text: str,
    current_whatsapp_phone: str | None,
) -> None:
    """Apply deterministic phone-option handling when guest replies with choice 1/2."""
    if not _response_requests_phone(response):
        return

    choice = _parse_phone_collection_choice(user_text)
    if not choice:
        return

    language = str(response.internal_json.language or "tr").lower()
    if choice == "share_different":
        response.internal_json.required_questions = ["phone"]
        response.user_message = _different_phone_followup_message(language)
        return

    normalized_phone = _normalize_phone_for_collection(current_whatsapp_phone or "")
    if not normalized_phone:
        return

    entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
    entities["phone"] = normalized_phone
    entities["phone_source"] = "whatsapp_current_number"
    response.internal_json.entities = entities

    original_required = [
        str(item).strip()
        for item in response.internal_json.required_questions
        if isinstance(item, str) and str(item).strip()
    ]
    filtered_required = [
        question for question in original_required if _canonical_required_question_key(question) != "phone"
    ]
    response.internal_json.required_questions = filtered_required

    if filtered_required:
        response.user_message = _single_field_prompt(language, filtered_required[0])
        return

    if str(response.internal_json.intent or "").lower() == "restaurant_booking_create":
        missing_required = _restaurant_missing_required_fields(entities)
        if missing_required:
            response.internal_json.required_questions = [missing_required[0]]
            response.user_message = _single_field_prompt(language, missing_required[0])
            return
        response.internal_json.required_questions = []
        response.internal_json.state = "READY_FOR_TOOL"
        response.internal_json.next_step = "run_restaurant_availability"
        response.user_message = _restaurant_tool_progress_message(language)
        return

    response.user_message = _phone_saved_message(language)


def _single_field_prompt(language: str, required_question: str) -> str:
    """Build one-step follow-up prompt for a single missing reservation field."""
    key = _canonical_required_question_key(required_question)
    prompts = {
        "tr": {
            "checkin_date": "Rezervasyon için önce giriş tarihinizi paylaşır mısınız? (GG.AA)",
            "checkout_date": "Çıkış tarihinizi paylaşır mısınız? (GG.AA)",
            "adults": "Kaç yetişkin konaklayacaksınız?",
            "chd_ages": "Çocuk varsa yaşlarını tek tek paylaşır mısınız? (ör. 4, 9)",
            "guest_name": "Rezervasyon için ad soyad bilginizi paylaşır mısınız?",
            "phone": _phone_collection_prompt("tr"),
            "email": "E-posta adresinizi paylaşır mısınız? (opsiyonel)",
            "cancel_policy_type": "Hangi iptal politikasıyla devam edelim: İptal edilemez mi, Ücretsiz İptal mi?",
            "room_distribution": "Oda dağılımını nasıl planlayalım? (ör. 3+3 veya 4+2)",
            "route": "Transfer için güzergâhı paylaşır mısınız? (nereden -> nereye)",
            "area": "Acik alan mi kapali alan mi tercih edersiniz?",
            "date": "Rezervasyon tarihi nedir? (GG.AA)",
            "time": "Saat bilgisini paylaşır mısınız?",
            "party_size": "Kaç kişi için rezervasyon yapalım?",
            "notes": "Eklemek istediğiniz özel bir not var mı?",
        },
        "en": {
            "checkin_date": "Please share your check-in date first. (DD.MM)",
            "checkout_date": "Please share your check-out date. (DD.MM)",
            "adults": "How many adults will stay?",
            "chd_ages": "If there are children, please share each age. (e.g. 4, 9)",
            "guest_name": "Please share the full name for the reservation.",
            "phone": _phone_collection_prompt("en"),
            "email": "Please share your email address. (optional)",
            "cancel_policy_type": "Which cancellation policy do you prefer: Non-refundable or Free Cancellation?",
            "room_distribution": "How would you like to split the rooms? (e.g. 3+3 or 4+2)",
            "route": "Please share the transfer route. (from -> to)",
            "area": "Do you prefer indoor or outdoor seating?",
            "date": "What is the reservation date? (DD.MM)",
            "time": "Please share the preferred time.",
            "party_size": "How many guests should I reserve for?",
            "notes": "Any special note you would like to add?",
        },
        "ru": {
            "checkin_date": "Пожалуйста, сначала укажите дату заезда. (ДД.ММ)",
            "checkout_date": "Пожалуйста, укажите дату выезда. (ДД.ММ)",
            "adults": "Сколько взрослых будет проживать?",
            "chd_ages": "Если есть дети, укажите возраст каждого. (например, 4, 9)",
            "guest_name": "Пожалуйста, укажите имя и фамилию для бронирования.",
            "phone": _phone_collection_prompt("ru"),
            "email": "Пожалуйста, укажите ваш e-mail. (необязательно)",
            "cancel_policy_type": "Какой вариант отмены предпочитаете: невозвратный или бесплатная отмена?",
            "room_distribution": "Как разделим размещение по комнатам? (например, 3+3 или 4+2)",
            "route": "Пожалуйста, укажите маршрут трансфера. (откуда -> куда)",
            "area": "Вы предпочитаете место в помещении или на открытом воздухе?",
            "date": "Какая дата бронирования? (ДД.ММ)",
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
    first_required_key = _canonical_required_question_key(first_required)
    if (
        first_required_key == "phone"
        or len(required) > 1
        or not str(response.user_message or "").strip()
    ):
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
    if state not in {"READY_FOR_TOOL", "NEEDS_CONFIRMATION", "PENDING_APPROVAL", "NEEDS_VERIFICATION"}:
        return False

    parsed_tool_calls = ResponseParser.extract_tool_calls(internal_json)
    tool_names = {
        str(item.get("name") or "").strip()
        for item in parsed_tool_calls
        if isinstance(item, dict)
    }
    if state == "NEEDS_VERIFICATION" and "stay_create_hold" in tool_names:
        required = [
            str(item).strip()
            for item in internal_json.required_questions
            if isinstance(item, str) and str(item).strip()
        ]
        return len(required) == 0
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


def _stay_hold_fields_present(entities: dict[str, Any]) -> bool:
    """Return True when minimum fields exist to build stay hold draft via quote fallback."""
    return (
        bool(str(entities.get("checkin_date") or "").strip())
        and bool(str(entities.get("checkout_date") or "").strip())
        and _to_int(entities.get("adults"), 0) > 0
        and bool(str(entities.get("guest_name") or "").strip())
        and bool(str(entities.get("phone") or "").strip())
    )


def _stay_room_hint_present(entities: dict[str, Any]) -> bool:
    """Return True when stay entities already contain a room preference hint."""
    return bool(
        str(entities.get("room_type") or entities.get("room_name") or entities.get("room_type_name") or "").strip()
    ) or _to_int(entities.get("room_type_id"), 0) > 0


def _message_supplies_stay_guest_details(user_text: str) -> bool:
    """Detect contact-detail style replies that usually complete a stay draft."""
    normalized = _canonical_text(user_text)
    if not normalized:
        return False
    detail_tokens = (
        "adsoyad",
        "advesoyad",
        "guestname",
        "telno",
        "telefon",
        "phone",
        "uyruk",
        "nationality",
        "email",
        "eposta",
        "fiyattipi",
    )
    hits = sum(1 for token in detail_tokens if token in normalized)
    return hits >= 2 or "@" in user_text


def _assistant_claims_stay_created(user_message: str) -> bool:
    """Detect guest-facing stay success claims that require a real hold underneath."""
    normalized = _canonical_text(user_message)
    if not normalized:
        return False
    creation_tokens = (
        "rezervasyonunuzolusturuldu",
        "rezervasyonunolusturuldu",
        "rezervasyonunuzonaylandi",
        "reservationcreated",
        "reservationconfirmed",
    )
    return any(token in normalized for token in creation_tokens)


def _should_auto_submit_stay_hold_from_context(
    internal_json: InternalJSON,
    entities: dict[str, Any],
    *,
    user_text: str,
    user_message: str,
) -> bool:
    """Recover a skipped stay hold when the guest already supplied complete booking details."""
    state = str(internal_json.state or "").upper()
    if state not in {"READY_FOR_TOOL", "NEEDS_CONFIRMATION", "PENDING_APPROVAL", "NEEDS_VERIFICATION"}:
        return False
    if not _stay_hold_fields_present(entities) or not _stay_room_hint_present(entities):
        return False
    if _assistant_claims_stay_created(user_message):
        return True
    return _message_supplies_stay_guest_details(user_text)


def _should_auto_submit_stay_hold_from_handoff(
    internal_json: InternalJSON,
    entities: dict[str, Any],
) -> bool:
    """Return True for recoverable stay handoff cases caused by missing live rate identifiers."""
    if str(internal_json.state or "").upper() != "HANDOFF":
        return False
    if not _stay_hold_fields_present(entities):
        return False

    handoff = internal_json.handoff if isinstance(internal_json.handoff, dict) else {}
    reason_text = _canonical_text(
        f"{handoff.get('reason') or ''} {internal_json.next_step or ''} {internal_json.intent or ''}"
    )
    if "livepriceunavailable" in reason_text or "stayholdsubmissionfailed" in reason_text:
        return False

    has_rate_identifier_signal = any(
        token in reason_text
        for token in (
            "rateidentifier",
            "ratetypeid",
            "ratecodeid",
            "priceagencyid",
        )
    )
    has_stay_hold_signal = "staycreatehold" in reason_text or "pmsgrounding" in reason_text
    has_room_type_mapping_signal = (
        "roomtypes" in reason_text
        and "sistemid" in reason_text
        and "otomatikhold" in reason_text
        and ("olusturulamiyor" in reason_text or "oluşturulamıyor" in reason_text)
    )
    has_room_type_hint = bool(
        _canonical_text(
            str(entities.get("room_type") or entities.get("room_name") or entities.get("room_type_name") or "")
        )
    )

    # Some model outputs set handoff.needed=false while still emitting a recoverable mapping reason.
    if has_room_type_mapping_signal and has_room_type_hint:
        return True
    return has_rate_identifier_signal and has_stay_hold_signal


def _restaurant_required_fields_present(entities: dict[str, Any]) -> bool:
    """Return True when enough restaurant fields exist to call availability/create tools."""
    return (
        bool(str(entities.get("date") or "").strip())
        and bool(str(entities.get("time") or "").strip())
        and _to_int(entities.get("party_size"), 0) > 0
        and bool(str(entities.get("guest_name") or "").strip())
        and bool(str(entities.get("phone") or "").strip())
    )


def _is_affirmative_confirmation(text: str) -> bool:
    """Return True when the guest explicitly confirms proceeding."""
    normalized = _normalize_language_text(text)
    keywords = (
        "evet",
        "tamam",
        "olur",
        "uygun",
        "dogru",
        "onayliyorum",
        "yes",
        "ok",
        "okay",
        "confirm",
        "approved",
        "da",
        "podtverzhdayu",
    )
    return any(_contains_keyword(normalized, keyword) for keyword in keywords)


def _should_auto_submit_restaurant_hold(
    internal_json: InternalJSON,
    entities: dict[str, Any],
    normalized_text: str,
) -> bool:
    """Return True when parsed response indicates restaurant hold must be submitted now."""
    if str(internal_json.intent or "").lower() != "restaurant_booking_create":
        return False
    if not _restaurant_required_fields_present(entities):
        return False

    state = str(internal_json.state or "").upper()
    if state not in {"READY_FOR_TOOL", "TOOL_RUNNING", "NEEDS_CONFIRMATION", "PENDING_APPROVAL", "NEEDS_VERIFICATION"}:
        return False
    if state == "NEEDS_CONFIRMATION" and not _is_affirmative_confirmation(normalized_text):
        return False

    parsed_tool_calls = ResponseParser.extract_tool_calls(internal_json)
    tool_names = {
        str(item.get("name") or "").strip()
        for item in parsed_tool_calls
        if isinstance(item, dict)
    }
    if state == "NEEDS_VERIFICATION" and "restaurant_create_hold" in tool_names:
        required = [
            str(item).strip()
            for item in internal_json.required_questions
            if isinstance(item, str) and str(item).strip()
        ]
        return len(required) == 0
    if {"restaurant_availability", "restaurant_create_hold"} & tool_names:
        return True

    next_step = _canonical_text(str(internal_json.next_step or ""))
    if not next_step:
        return state in {"READY_FOR_TOOL", "TOOL_RUNNING", "PENDING_APPROVAL"}
    if "restaurantcreatehold" in next_step:
        return True
    if next_step == "awaittoolresult":
        return True
    if "approval" in next_step or "onay" in next_step:
        return True
    return state in {"READY_FOR_TOOL", "TOOL_RUNNING", "PENDING_APPROVAL"}


def _executed_restaurant_hold_submission(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when a restaurant hold was successfully created."""
    for call in executed_calls:
        if str(call.get("name") or "") != "restaurant_create_hold":
            continue
        result = _loads_tool_payload(call.get("result"))
        if str(result.get("restaurant_hold_id") or "").strip():
            return True
    return False


def _transfer_required_fields_present(entities: dict[str, Any]) -> bool:
    """Return True when enough transfer fields exist to call transfer_create_hold."""
    return (
        bool(str(entities.get("route") or "").strip())
        and bool(str(entities.get("date") or "").strip())
        and bool(str(entities.get("time") or "").strip())
        and _to_int(entities.get("pax_count"), 0) > 0
        and bool(str(entities.get("guest_name") or "").strip())
        and bool(str(entities.get("phone") or "").strip())
    )


def _should_auto_submit_transfer_hold(
    internal_json: InternalJSON,
    entities: dict[str, Any],
    normalized_text: str,
) -> bool:
    """Return True when parsed response indicates transfer hold must be submitted now."""
    if str(internal_json.intent or "").lower() != "transfer_booking_create":
        return False
    if not _transfer_required_fields_present(entities):
        return False

    state = str(internal_json.state or "").upper()
    if state not in {"READY_FOR_TOOL", "TOOL_RUNNING", "NEEDS_CONFIRMATION", "PENDING_APPROVAL", "NEEDS_VERIFICATION"}:
        return False
    if state == "NEEDS_CONFIRMATION" and not _is_affirmative_confirmation(normalized_text):
        return False

    parsed_tool_calls = ResponseParser.extract_tool_calls(internal_json)
    tool_names = {
        str(item.get("name") or "").strip()
        for item in parsed_tool_calls
        if isinstance(item, dict)
    }
    if "transfer_create_hold" in tool_names:
        if state == "NEEDS_VERIFICATION":
            required = [
                str(item).strip()
                for item in internal_json.required_questions
                if isinstance(item, str) and str(item).strip()
            ]
            return len(required) == 0
        return True

    next_step = _canonical_text(str(internal_json.next_step or ""))
    if not next_step:
        return state in {"READY_FOR_TOOL", "TOOL_RUNNING", "PENDING_APPROVAL"}
    if "transfercreatehold" in next_step:
        return True
    if next_step == "awaittoolresult":
        return True
    if "approval" in next_step or "onay" in next_step:
        return True
    return state in {"READY_FOR_TOOL", "TOOL_RUNNING", "PENDING_APPROVAL"}


def _executed_transfer_hold_submission(executed_calls: list[dict[str, Any]]) -> bool:
    """Return True when a transfer hold was successfully created."""
    for call in executed_calls:
        if str(call.get("name") or "") != "transfer_create_hold":
            continue
        result = _loads_tool_payload(call.get("result"))
        if str(result.get("transfer_hold_id") or "").strip():
            return True
    return False


async def _auto_submit_transfer_hold(
    conversation: Conversation,
    entities: dict[str, Any],
    dispatcher: Any,
) -> list[dict[str, Any]]:
    """Fallback: create transfer hold deterministically when LLM skips tool calls."""
    route = str(entities.get("route") or "").strip()
    date_value = str(entities.get("date") or "").strip()
    time_value = str(entities.get("time") or "").strip()
    pax_count = _to_int(entities.get("pax_count"), 0)
    guest_name = str(entities.get("guest_name") or "").strip()
    phone = str(entities.get("phone") or "").strip()
    if not route or not date_value or not time_value or pax_count <= 0 or not guest_name or not phone:
        return []

    hold_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "route": route,
        "date": date_value,
        "time": time_value,
        "pax_count": pax_count,
        "guest_name": guest_name,
        "phone": phone,
    }
    if str(entities.get("flight_no") or "").strip():
        hold_args["flight_no"] = str(entities.get("flight_no") or "").strip()
    if "baby_seat" in entities:
        hold_args["baby_seat"] = bool(entities.get("baby_seat"))
    if "notes" in entities:
        hold_args["notes"] = str(entities.get("notes") or "")
    if conversation.id is not None:
        hold_args["conversation_id"] = str(conversation.id)

    hold_result = await dispatcher.dispatch("transfer_create_hold", **hold_args)
    if not isinstance(hold_result, dict) or hold_result.get("error"):
        logger.warning("transfer_hold_auto_submit_create_failed")
        return []

    fallback_calls: list[dict[str, Any]] = [
        {"name": "transfer_create_hold", "arguments": hold_args, "result": hold_result}
    ]
    approval_request_id = str(hold_result.get("approval_request_id") or "").strip()
    if approval_request_id:
        fallback_calls.append(
            {
                "name": "approval_request",
                "arguments": {
                    "hotel_id": conversation.hotel_id,
                    "approval_type": "TRANSFER",
                    "reference_id": str(hold_result.get("transfer_hold_id") or ""),
                    "required_roles": ["ADMIN"],
                },
                "result": {
                    "approval_request_id": approval_request_id,
                    "status": hold_result.get("approval_status", "REQUESTED"),
                },
            }
        )

    logger.info(
        "transfer_hold_auto_submitted",
        hold_id=hold_result.get("transfer_hold_id"),
        approval_request_id=approval_request_id or None,
    )
    return fallback_calls


def _select_restaurant_slot_id(entities: dict[str, Any], availability_result: dict[str, Any]) -> str:
    """Pick a slot id from availability result, preferring any pre-selected slot."""
    raw_options = availability_result.get("options")
    if not isinstance(raw_options, list):
        return ""

    preferred_slot_id = str(entities.get("slot_id") or "").strip()
    normalized_options = [item for item in raw_options if isinstance(item, dict)]
    if preferred_slot_id:
        for item in normalized_options:
            option_id = str(item.get("slot_id") or "").strip()
            if option_id == preferred_slot_id:
                return option_id

    for item in normalized_options:
        option_id = str(item.get("slot_id") or "").strip()
        if option_id:
            return option_id
    return ""


async def _auto_submit_restaurant_hold(
    conversation: Conversation,
    entities: dict[str, Any],
    dispatcher: Any,
) -> list[dict[str, Any]]:
    """Fallback: create restaurant hold deterministically when LLM skips tool calls."""
    date_value = str(entities.get("date") or "").strip()
    time_value = str(entities.get("time") or "").strip()
    party_size = _to_int(entities.get("party_size"), 0)
    guest_name = str(entities.get("guest_name") or "").strip()
    phone = str(entities.get("phone") or "").strip()
    if not date_value or not time_value or party_size <= 0 or not guest_name or not phone:
        return []

    availability_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "date": date_value,
        "time": time_value,
        "party_size": party_size,
    }
    if str(entities.get("area") or "").strip():
        availability_args["area"] = str(entities.get("area") or "").strip()
    if str(entities.get("notes") or "").strip():
        availability_args["notes"] = str(entities.get("notes") or "").strip()

    availability_result = await dispatcher.dispatch("restaurant_availability", **availability_args)
    if not isinstance(availability_result, dict) or availability_result.get("error"):
        logger.warning("restaurant_hold_auto_submit_availability_failed")
        return []

    fallback_calls: list[dict[str, Any]] = [
        {"name": "restaurant_availability", "arguments": availability_args, "result": availability_result},
    ]
    if not bool(availability_result.get("available")):
        return fallback_calls

    selected_slot_id = _select_restaurant_slot_id(entities, availability_result)
    if not selected_slot_id:
        logger.warning("restaurant_hold_auto_submit_slot_missing")
        return fallback_calls

    hold_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "slot_id": selected_slot_id,
        "guest_name": guest_name,
        "phone": phone,
        "party_size": party_size,
    }
    if str(entities.get("area") or "").strip():
        hold_args["area"] = str(entities.get("area") or "").strip()
    if "notes" in entities:
        hold_args["notes"] = str(entities.get("notes") or "")
    if conversation.id is not None:
        hold_args["conversation_id"] = str(conversation.id)

    hold_result = await dispatcher.dispatch("restaurant_create_hold", **hold_args)
    if not isinstance(hold_result, dict) or hold_result.get("error"):
        logger.warning("restaurant_hold_auto_submit_create_failed")
        return []

    fallback_calls.append({"name": "restaurant_create_hold", "arguments": hold_args, "result": hold_result})
    approval_request_id = str(hold_result.get("approval_request_id") or "").strip()
    if approval_request_id:
        fallback_calls.append(
            {
                "name": "approval_request",
                "arguments": {
                    "hotel_id": conversation.hotel_id,
                    "approval_type": "RESTAURANT",
                    "reference_id": str(hold_result.get("restaurant_hold_id") or ""),
                    "required_roles": ["ADMIN", "CHEF"],
                    "any_of": True,
                },
                "result": {
                    "approval_request_id": approval_request_id,
                    "status": "REQUESTED",
                },
            }
        )

    logger.info(
        "restaurant_hold_auto_submitted",
        hold_id=hold_result.get("restaurant_hold_id"),
        approval_request_id=approval_request_id or None,
    )
    return fallback_calls


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

    requested_name = _canonical_text(
        str(entities.get("room_type") or entities.get("room_name") or entities.get("room_type_name") or "")
    )
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


def _resolve_requested_room_type_label(
    entities: dict[str, Any],
    profile: Any | None,
    requested_room_type_id: int,
    language: str,
) -> str:
    """Resolve a human-readable room label for the requested stay room."""
    if requested_room_type_id > 0 and profile is not None:
        for room in getattr(profile, "room_types", []):
            profile_room_id = _to_int(getattr(room, "id", 0), 0)
            pms_room_id = _to_int(getattr(room, "pms_room_type_id", 0), 0)
            if requested_room_type_id not in {profile_room_id, pms_room_id}:
                continue
            localized_name = getattr(room, "name", None)
            if str(language or "tr").lower() == "en":
                label = str(getattr(localized_name, "en", "") or getattr(localized_name, "tr", "") or "").strip()
            else:
                label = str(getattr(localized_name, "tr", "") or getattr(localized_name, "en", "") or "").strip()
            if label:
                return label
    return str(entities.get("room_type") or entities.get("room_name") or entities.get("room_type_name") or "").strip()


def _guest_explicitly_requested_room_type(
    user_text: str,
    entities: dict[str, Any],
    profile: Any | None,
) -> tuple[bool, int]:
    """Return whether the current guest message explicitly names one room type."""
    requested_room_type_id = _resolve_requested_room_type_id(entities, profile)
    if requested_room_type_id <= 0:
        return False, 0

    normalized_user_text = _canonical_text(user_text)
    if not normalized_user_text:
        return False, 0

    candidate_names: set[str] = set()
    for field_name in ("room_type", "room_name", "room_type_name"):
        candidate = _canonical_text(str(entities.get(field_name) or ""))
        if candidate:
            candidate_names.add(candidate)

    if profile is not None:
        for room in getattr(profile, "room_types", []):
            profile_room_id = _to_int(getattr(room, "id", 0), 0)
            pms_room_id = _to_int(getattr(room, "pms_room_type_id", 0), 0)
            if requested_room_type_id not in {profile_room_id, pms_room_id}:
                continue
            localized_name = getattr(room, "name", None)
            for raw_name in (
                getattr(localized_name, "tr", ""),
                getattr(localized_name, "en", ""),
            ):
                candidate = _canonical_text(str(raw_name or ""))
                if candidate:
                    candidate_names.add(candidate)

    for candidate_name in candidate_names:
        if candidate_name and candidate_name in normalized_user_text:
            return True, requested_room_type_id
    return False, requested_room_type_id


def _policy_label(cancel_policy_type: str, language: str) -> str:
    """Format cancellation policy label for guest-facing fallback text."""
    normalized = _normalize_cancel_policy(cancel_policy_type)
    if str(language or "tr").lower() == "en":
        return "free cancellation" if normalized == "FREE_CANCEL" else "non-refundable"
    return "ucretsiz iptal" if normalized == "FREE_CANCEL" else "iptal edilemez"


def _available_offer_room_type_ids(
    offers: list[dict[str, Any]],
    *,
    cancel_policy_type: str,
    profile: Any | None,
) -> list[int]:
    """Collect unique room type ids from live quote offers, keeping policy filtering when possible."""
    if not offers:
        return []
    ids: list[int] = []
    seen: set[int] = set()
    preferred_policy_ids: list[int] = []
    preferred_seen: set[int] = set()
    normalized_policy = _normalize_cancel_policy(cancel_policy_type)
    for offer in offers:
        room_type_id = _to_int(offer.get("room_type_id"), 0)
        if room_type_id <= 0:
            continue
        if room_type_id not in seen:
            seen.add(room_type_id)
            ids.append(room_type_id)
        if normalized_policy and _resolve_quote_policy_key(offer, profile) == normalized_policy and room_type_id not in preferred_seen:
            preferred_seen.add(room_type_id)
            preferred_policy_ids.append(room_type_id)
    return preferred_policy_ids or ids


def _build_requested_room_offer_missing_response(
    *,
    conversation: Conversation,
    entities: dict[str, Any],
    language: str,
    requested_room_type_id: int,
    offers: list[dict[str, Any]],
    cancel_policy_type: str,
    profile: Any | None,
) -> LLMResponse:
    """Build a deterministic reply when the requested room/policy combination is not offerable."""
    requested_label = _resolve_requested_room_type_label(entities, profile, requested_room_type_id, language)
    matching_room_exists = any(
        _to_int(offer.get("room_type_id"), 0) == requested_room_type_id for offer in offers
    ) if requested_room_type_id > 0 else False
    available_names = _format_available_room_names(
        conversation.hotel_id,
        _available_offer_room_type_ids(
            offers,
            cancel_policy_type=cancel_policy_type,
            profile=profile,
        ),
    )
    normalized_language = str(language or "tr").lower()
    policy_text = _policy_label(cancel_policy_type, normalized_language)
    if normalized_language == "en":
        if matching_room_exists and requested_label:
            lead = f"I could not find a {policy_text} offer for {requested_label} on those dates."
            required_questions = ["cancel_policy_type"]
            next_step = "collect_cancel_policy_preference"
        else:
            room_label = requested_label or "the requested room"
            lead = f"I could not find a live offer for {room_label} on those dates."
            required_questions = ["room_type"]
            next_step = "collect_room_type_preference"
        if available_names:
            follow_up = "Currently offerable room types: " + ", ".join(available_names) + "."
            closing = "Please tell me which one you want to continue with."
        else:
            follow_up = "I could not find an offerable alternative room type right now."
            closing = "Our sales team will review this manually."
        user_message = f"{lead}\n\n{follow_up}\n{closing}"
    else:
        if matching_room_exists and requested_label:
            lead = f"{requested_label} icin bu tarihlerde {policy_text} teklif bulamadim."
            required_questions = ["cancel_policy_type"]
            next_step = "collect_cancel_policy_preference"
        else:
            room_label = requested_label or "istediginiz oda tipi"
            lead = f"{room_label} icin bu tarihlerde canli teklif bulamadim."
            required_questions = ["room_type"]
            next_step = "collect_room_type_preference"
        if available_names:
            follow_up = "Su anda tekliflenebilen oda tipleri: " + ", ".join(available_names) + "."
            closing = "Lutfen hangisiyle devam etmek istediginizi yazin."
        else:
            follow_up = "Su anda tekliflenebilen alternatif oda tipi goremedim."
            closing = "Satis ekibimiz talebinizi manuel olarak inceleyecek."
        user_message = f"{lead}\n\n{follow_up}\n{closing}"
    return LLMResponse(
        user_message=user_message,
        internal_json=InternalJSON(
            language=normalized_language,
            intent="stay_booking_create",
            state="HANDOFF" if not available_names else "NEEDS_VERIFICATION",
            entities=entities,
            required_questions=[] if not available_names else required_questions,
            handoff={"needed": not bool(available_names), "reason": "requested_room_offer_unavailable"},
            risk_flags=["TOOL_ERROR_REPEAT"] if not available_names else [],
            next_step="manual_review_required" if not available_names else next_step,
        ),
    )


def _select_offer_for_stay_hold(
    offers: list[dict[str, Any]],
    requested_room_type_id: int,
    cancel_policy_type: str,
    profile: Any | None,
) -> dict[str, Any] | None:
    """Pick the best matching quote offer for hold creation without changing the requested room."""
    if not offers:
        return None
    non_contract_offers = [
        offer
        for offer in offers
        if _resolve_quote_policy_key(offer, profile) != "CONTRACT"
    ]
    if non_contract_offers:
        offers = non_contract_offers

    def _matches(offer: dict[str, Any], *, check_room: bool, check_policy: bool) -> bool:
        if (
            check_room
            and requested_room_type_id > 0
            and _to_int(offer.get("room_type_id"), 0) != requested_room_type_id
        ):
            return False
        if check_policy:
            resolved = _resolve_quote_policy_key(offer, profile)
            if resolved != cancel_policy_type:
                return False
        return True

    if requested_room_type_id > 0:
        candidate_sets: tuple[list[dict[str, Any]], ...]
        if cancel_policy_type:
            candidate_sets = (
                [offer for offer in offers if _matches(offer, check_room=True, check_policy=True)],
            )
        else:
            candidate_sets = (
                [offer for offer in offers if _matches(offer, check_room=True, check_policy=False)],
            )
    elif cancel_policy_type:
        candidate_sets = (
            [offer for offer in offers if _matches(offer, check_room=False, check_policy=True)],
        )
    else:
        candidate_sets = (list(offers),)

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
    price_agency_id = _to_int(offer.get("price_agency_id"), 0)
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
        or price_agency_id <= 0
    ):
        return None

    total_price = _decimal_from_value(offer.get("discounted_price", offer.get("price", 0)))
    if total_price <= 0:
        total_price = _decimal_from_value(offer.get("price", 0))
    if total_price <= 0:
        return None

    chd_ages: list[int] = []
    raw_chd_ages = entities.get("chd_ages")
    if not isinstance(raw_chd_ages, list):
        raw_chd_ages = entities.get("child_ages")
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
        "price_agency_id": price_agency_id,
        "currency_display": str(offer.get("currency_code") or entities.get("currency") or "EUR").upper(),
        "total_price_eur": float(total_price),
        "adults": adults,
        "chd_ages": chd_ages,
        "guest_name": guest_name,
        "phone": phone,
        "email": entities.get("email"),
        "nationality": str(entities.get("nationality") or "TR").upper(),
        "cancel_policy_type": cancel_policy_type,
        "notes": str(entities.get("notes") or ""),
    }
    return draft


async def _auto_submit_stay_hold(
    conversation: Conversation,
    entities: dict[str, Any],
    language: str,
    dispatcher: Any,
) -> tuple[list[dict[str, Any]], LLMResponse | None]:
    """Fallback: create stay hold deterministically when LLM skips tool calls."""
    profile = get_profile(conversation.hotel_id)
    room_hint_present = _stay_room_hint_present(entities)
    requested_room_type_id = _resolve_requested_room_type_id(entities, profile)

    checkin_date = str(entities.get("checkin_date") or "").strip()
    checkout_date = str(entities.get("checkout_date") or "").strip()
    adults = _to_int(entities.get("adults"), 0)
    if not checkin_date or not checkout_date or adults <= 0:
        return [], None

    cancel_policy_type = _normalize_cancel_policy(entities.get("cancel_policy_type"))
    quote_language = str(entities.get("language") or language or "tr").upper()
    if quote_language not in {"TR", "EN"}:
        quote_language = "TR"

    raw_quote_chd_ages = entities.get("chd_ages")
    if not isinstance(raw_quote_chd_ages, list):
        raw_quote_chd_ages = entities.get("child_ages")
    quote_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults": adults,
        "chd_count": _to_int(entities.get("chd_count"), _to_int(entities.get("children"), 0)),
        "chd_ages": raw_quote_chd_ages if isinstance(raw_quote_chd_ages, list) else [],
        "currency": str(entities.get("currency") or "EUR").upper(),
        "language": quote_language,
        "nationality": str(entities.get("nationality") or "TR").upper(),
        "cancel_policy_type": cancel_policy_type,
    }
    quote_result = await dispatcher.dispatch("booking_quote", **quote_args)
    if not isinstance(quote_result, dict):
        logger.warning("stay_hold_auto_submit_quote_failed")
        return [], None
    fallback_calls: list[dict[str, Any]] = [
        {"name": "booking_quote", "arguments": quote_args, "result": quote_result},
    ]
    if _is_out_of_season_tool_result(quote_result):
        return fallback_calls, None
    if quote_result.get("error"):
        logger.warning("stay_hold_auto_submit_quote_failed")
        return [], None

    offers = quote_result.get("offers")
    if not isinstance(offers, list):
        return [], None
    parsed_offers = [offer for offer in offers if isinstance(offer, dict)]
    if not room_hint_present or requested_room_type_id <= 0:
        return fallback_calls, _build_requested_room_offer_missing_response(
            conversation=conversation,
            entities=entities,
            language=language,
            requested_room_type_id=requested_room_type_id,
            offers=parsed_offers,
            cancel_policy_type=cancel_policy_type,
            profile=profile,
        )
    selected_offer = _select_offer_for_stay_hold(
        parsed_offers,
        requested_room_type_id=requested_room_type_id,
        cancel_policy_type=cancel_policy_type,
        profile=profile,
    )
    if selected_offer is None:
        return fallback_calls, _build_requested_room_offer_missing_response(
            conversation=conversation,
            entities=entities,
            language=language,
            requested_room_type_id=requested_room_type_id,
            offers=parsed_offers,
            cancel_policy_type=cancel_policy_type,
            profile=profile,
        )

    draft = _build_stay_draft_from_offer(entities, selected_offer, cancel_policy_type)
    if draft is None:
        return [], None

    hold_args: dict[str, Any] = {
        "hotel_id": conversation.hotel_id,
        "draft": draft,
    }
    if conversation.id is not None:
        hold_args["conversation_id"] = str(conversation.id)

    hold_result = await dispatcher.dispatch("stay_create_hold", **hold_args)
    if not isinstance(hold_result, dict) or hold_result.get("error"):
        logger.warning("stay_hold_auto_submit_create_failed")
        return [], None

    fallback_calls.append({"name": "stay_create_hold", "arguments": hold_args, "result": hold_result})
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
    return fallback_calls, None


async def _run_message_pipeline(
    conversation: Conversation,
    normalized_text: str,
    dispatcher: Any | None = None,
    expected_language: str | None = None,
    burst_metadata: dict[str, Any] | None = None,
    reply_context: dict[str, Any] | None = None,
    current_whatsapp_phone: str | None = None,
) -> LLMResponse:
    """Run message pipeline and return structured LLM response."""
    original_user_text = normalized_text
    normalized_text = _inject_phone_choice_signal(
        conversation=conversation,
        user_text=normalized_text,
        current_whatsapp_phone=current_whatsapp_phone,
    )
    target_language = (
        expected_language
        if expected_language in SUPPORTED_LANGUAGE_CODES
        else conversation.language if conversation.language in SUPPORTED_LANGUAGE_CODES else "tr"
    )

    def _finalize_response(
        candidate: LLMResponse,
        *,
        scope_decision: ScopeDecision | None = None,
        language_override: str | None = None,
        executed_calls: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        _sync_response_tool_calls(candidate, executed_calls)
        return validate_guest_response(
            candidate,
            default_language=language_override or target_language,
            scope_decision=scope_decision,
        )

    if PAYMENT_DATA_PATTERN.search(normalized_text):
        return _finalize_response(
            LLMResponse(
                user_message=_payment_warning_message(target_language),
                internal_json=InternalJSON(
                    language=target_language,
                    intent="payment_inquiry",
                    state="HANDOFF",
                    risk_flags=["PAYMENT_CONFUSION"],
                    next_step="handoff_to_sales",
                ),
            )
        )

    payment_intake_response = _build_payment_intake_response(
        conversation=conversation,
        normalized_text=normalized_text,
        target_language=target_language,
    )
    if payment_intake_response is not None:
        return _finalize_response(payment_intake_response)

    if _has_recent_media_analysis_context(conversation) and _is_room_type_identification_question(normalized_text):
        return _finalize_response(_build_media_room_type_grounded_response(conversation.hotel_id, target_language))

    scope_result = classify_reception_scope(normalized_text)
    if scope_result.decision == ScopeDecision.OUT_OF_SCOPE and not _has_payment_intake_state(conversation):
        return _finalize_response(
            LLMResponse(
                user_message=out_of_scope_refusal(target_language),
                internal_json=InternalJSON(
                    language=target_language,
                    intent="other",
                    state="INTENT_DETECTED",
                    entities={
                        "scope_classifier": {
                            "decision": scope_result.decision.value,
                            "reason": scope_result.reason,
                            "confidence": round(scope_result.confidence, 3),
                        }
                    },
                    required_questions=[],
                    handoff={"needed": False},
                    risk_flags=[],
                    next_step="await_hotel_related_request",
                ),
            ),
            scope_decision=scope_result.decision,
        )

    if await _should_force_restaurant_manual_handoff(conversation, normalized_text):
        existing_entities = conversation.entities_json if isinstance(conversation.entities_json, dict) else {}
        return _finalize_response(
            LLMResponse(
                user_message=_restaurant_manual_mode_message(target_language),
                internal_json=InternalJSON(
                    language=target_language,
                    intent="restaurant_booking_create",
                    state="HANDOFF",
                    entities=dict(existing_entities),
                    required_questions=[],
                    handoff={"needed": True, "reason": "restaurant_manual_mode"},
                    risk_flags=[],
                    next_step="handoff_to_restaurant_team",
                ),
            ),
            scope_decision=scope_result.decision,
        )

    try:
        prompt_builder = get_prompt_builder()
        llm_client = get_llm_client()
        messages = prompt_builder.build_messages(
            conversation,
            normalized_text,
            detected_language=target_language,
            burst_metadata=burst_metadata,
            reply_context=reply_context,
        )
        tools = _select_tool_definitions_for_turn(
            conversation,
            normalized_text,
            get_tool_definitions(),
        )
        tool_names_presented = _extract_tool_definition_names(tools)
        if dispatcher is not None:
            tool_executor = _build_dispatcher_executor(dispatcher, conversation)
        else:
            async def _unavailable_executor(tool_name: str, _tool_args: str | dict[str, Any]) -> str:
                logger.warning("tool_dispatcher_unavailable", tool_name=tool_name)
                return orjson.dumps({"error": "TOOL_DISPATCHER_UNAVAILABLE", "tool": tool_name}).decode()

            tool_executor = _unavailable_executor

        logger.info(
            "llm_tool_trace_start",
            conversation_id=str(conversation.id) if conversation.id is not None else None,
            message_count=len(messages),
            tool_count=len(tool_names_presented),
            tool_names=tool_names_presented,
            user_text_length=len(normalized_text),
        )

        content, executed_calls = await llm_client.run_tool_call_loop(
            messages=messages,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=5,
            trace_context={"conversation_id": str(conversation.id) if conversation.id is not None else None},
        )

        logger.info(
            "llm_tool_trace_result",
            conversation_id=str(conversation.id) if conversation.id is not None else None,
            executed_call_count=len(executed_calls),
            executed_call_names=[str(call.get("name") or "") for call in executed_calls],
            content_length=len(content),
            has_internal_json_marker="INTERNAL_JSON" in content,
        )

        if executed_calls:
            logger.info(
                "llm_tool_calls_executed",
                tools=[c["name"] for c in executed_calls],
                count=len(executed_calls),
            )

        if _has_child_quote_mismatch(executed_calls):
            logger.warning("stay_quote_child_occupancy_manual_verification")
            return _finalize_response(
                _build_child_quote_handoff_response(conversation.hotel_id, executed_calls),
                scope_decision=scope_result.decision,
                executed_calls=executed_calls,
            )

        restaurant_capacity_handoff = _build_restaurant_capacity_handoff_response(
            conversation,
            executed_calls,
            target_language,
        )
        if restaurant_capacity_handoff is not None:
            return _finalize_response(
                restaurant_capacity_handoff,
                scope_decision=scope_result.decision,
                executed_calls=executed_calls,
            )
        restaurant_unavailable_response = _build_restaurant_unavailable_response(
            conversation,
            executed_calls,
            target_language,
        )
        if restaurant_unavailable_response is not None:
            return _finalize_response(
                restaurant_unavailable_response,
                scope_decision=scope_result.decision,
                executed_calls=executed_calls,
            )
        stay_or_transfer_out_of_season = _build_stay_or_transfer_out_of_season_response(
            conversation,
            executed_calls,
            target_language,
        )
        if stay_or_transfer_out_of_season is not None:
            return _finalize_response(
                stay_or_transfer_out_of_season,
                scope_decision=scope_result.decision,
                executed_calls=executed_calls,
            )

        parsed = ResponseParser.parse(content)
        parser_error_reason = ResponseParser.extract_parser_error(parsed.internal_json)
        if parser_error_reason:
            repaired_response = await _attempt_structured_output_repair(
                llm_client=llm_client,
                raw_content=content,
                language=target_language,
                parser_error_reason=parser_error_reason,
                conversation=conversation,
                executed_calls=executed_calls,
            )
            if repaired_response is not None:
                parsed = repaired_response
                parser_error_reason = ""

        intent = str(parsed.internal_json.intent or "").lower()
        language = (
            target_language
            if target_language in SUPPORTED_LANGUAGE_CODES
            else str(parsed.internal_json.language or "tr").lower()
        )
        parsed.internal_json.language = language
        _suppress_default_year_question(parsed, original_user_text)
        entities = parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else {}
        entities = _merge_entities_with_context(conversation.entities_json, entities)
        entities["scope_classifier"] = {
            "decision": scope_result.decision.value,
            "reason": scope_result.reason,
            "confidence": round(scope_result.confidence, 3),
        }
        if not parser_error_reason:
            entities.pop("response_parser", None)
        entities = _sanitize_phone_entity(entities, current_whatsapp_phone=current_whatsapp_phone)
        parsed.internal_json.entities = entities
        _apply_phone_collection_choice_override(
            parsed,
            user_text=original_user_text,
            current_whatsapp_phone=current_whatsapp_phone,
        )
        entities = parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else {}
        _force_stay_intent_when_hold_ready(
            parsed,
            conversation=conversation,
            entities=entities,
        )

        current_year = _current_reservation_year()
        requested_non_current_year = _extract_non_current_year(
            original_user_text,
            current_year=current_year,
        )
        current_intent = str(conversation.current_intent or "")
        if requested_non_current_year is not None and (
            _is_reservation_intent(str(parsed.internal_json.intent or "")) or _is_reservation_intent(current_intent)
        ):
            _apply_non_current_year_reservation_handoff(
                parsed,
                requested_year=requested_non_current_year,
                current_year=current_year,
            )
            return _finalize_response(
                parsed,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
            )
        intent_guard_meta = _apply_turn_intent_domain_guard(
            parsed,
            normalized_text=normalized_text,
            tool_names_presented=tool_names_presented,
        )
        if intent_guard_meta is not None:
            intent = str(parsed.internal_json.intent or "").lower()
            record_intent_domain_guard(
                str(intent_guard_meta.get("reason") or ""),
                str(intent_guard_meta.get("from_intent") or ""),
                str(intent_guard_meta.get("to_intent") or ""),
            )
            logger.info(
                "llm_intent_domain_guard_applied",
                conversation_id=str(conversation.id) if conversation.id is not None else None,
                from_intent=intent_guard_meta.get("from_intent"),
                to_intent=intent_guard_meta.get("to_intent"),
                reason=intent_guard_meta.get("reason"),
                tool_names=tool_names_presented,
            )
        embedded_tool_names = [
            str(item.get("name") or "")
            for item in ResponseParser.extract_tool_calls(parsed.internal_json)
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
        logger.info(
            "llm_structured_output_trace",
            conversation_id=str(conversation.id) if conversation.id is not None else None,
            parser_error_reason=parser_error_reason or None,
            parsed_intent=intent or None,
            parsed_state=str(parsed.internal_json.state or "").strip() or None,
            embedded_tool_call_count=len(embedded_tool_names),
            embedded_tool_call_names=embedded_tool_names,
            executed_call_count=len(executed_calls),
        )
        if parser_error_reason:
            logger.warning(
                "llm_structured_output_parser_error",
                conversation_id=str(conversation.id) if conversation.id is not None else None,
                reason=parser_error_reason,
                has_executed_calls=bool(executed_calls),
            )
            if not executed_calls:
                return _finalize_response(
                    _build_structured_output_error_response(
                        language,
                        parser_error_reason,
                        conversation,
                    ),
                    scope_decision=scope_result.decision,
                    language_override=language,
                )
        _suppress_restaurant_area_question(parsed, conversation.hotel_id)
        if (
            not executed_calls
            and not intent
            and not str(parsed.internal_json.state or "").strip()
            and not ResponseParser.extract_tool_calls(parsed.internal_json)
        ):
            logger.warning(
                "llm_structured_output_missing",
                conversation_id=str(conversation.id) if conversation.id is not None else None,
                message_length=len(normalized_text),
            )
        if _has_recent_media_analysis_context(conversation) and _contains_profile_unsupported_room_taxonomy(
            parsed.user_message,
            conversation.hotel_id,
        ):
            logger.warning(
                "media_room_taxonomy_profile_guard_triggered",
                conversation_id=str(conversation.id) if conversation.id is not None else None,
            )
            return _finalize_response(
                _build_media_room_type_grounded_response(conversation.hotel_id, language),
                scope_decision=scope_result.decision,
            )
        if _is_elevator_question(normalized_text):
            parsed.user_message = _build_elevator_reply(conversation.hotel_id, language)
            return _finalize_response(
                parsed,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
            )
        if language == "tr" and _is_payment_method_question(normalized_text):
            parsed.user_message = _build_turkish_payment_methods_reply(conversation.hotel_id)
            return _finalize_response(
                parsed,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
            )
        if language == "tr" and _is_parking_question(normalized_text):
            parsed.user_message = _build_turkish_parking_reply(conversation.hotel_id)
            return _finalize_response(
                parsed,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
            )
        if language == "tr" and _is_child_bedding_question(normalized_text, entities):
            parsed.user_message = _build_turkish_child_bedding_reply(conversation.hotel_id, entities)
            return _finalize_response(
                parsed,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
            )
        if (
            dispatcher is not None
            and not _executed_restaurant_hold_submission(executed_calls)
            and _should_auto_submit_restaurant_hold(parsed.internal_json, entities, normalized_text)
        ):
            fallback_calls = await _auto_submit_restaurant_hold(
                conversation=conversation,
                entities=entities,
                dispatcher=dispatcher,
            )
            if fallback_calls:
                executed_calls.extend(fallback_calls)
                restaurant_capacity_handoff = _build_restaurant_capacity_handoff_response(
                    conversation,
                    executed_calls,
                    language,
                )
                if restaurant_capacity_handoff is not None:
                    return _finalize_response(
                        restaurant_capacity_handoff,
                        scope_decision=scope_result.decision,
                        language_override=language,
                        executed_calls=executed_calls,
                    )
                restaurant_unavailable_response = _build_restaurant_unavailable_response(
                    conversation,
                    executed_calls,
                    language,
                )
                if restaurant_unavailable_response is not None:
                    return _finalize_response(
                        restaurant_unavailable_response,
                        scope_decision=scope_result.decision,
                        language_override=language,
                        executed_calls=executed_calls,
                    )
            else:
                logger.warning(
                    "restaurant_hold_submission_missing_after_ready_for_tool",
                    conversation_id=str(conversation.id) if conversation.id is not None else None,
                    state=str(parsed.internal_json.state or ""),
                    next_step=str(parsed.internal_json.next_step or ""),
                )
                return _finalize_response(
                    LLMResponse(
                        user_message=(
                            "Talebinizi aldik ancak restoran rezervasyonunu teknik olarak tamamlayamadik. "
                            "Ekibimiz sizi manuel olarak en kisa surede bilgilendirecektir."
                        ),
                        internal_json=InternalJSON(
                            language=language,
                            intent="restaurant_booking_create",
                            state="HANDOFF",
                            entities=entities,
                            required_questions=[],
                            handoff={"needed": True, "reason": "restaurant_hold_submission_failed"},
                            risk_flags=["TOOL_ERROR_REPEAT"],
                            next_step="manual_review_required",
                        ),
                    ),
                    scope_decision=scope_result.decision,
                    language_override=language,
                    executed_calls=executed_calls,
                )
        if (
            dispatcher is not None
            and not _executed_stay_hold_submission(executed_calls)
            and (
                _should_auto_submit_stay_hold(parsed.internal_json)
                or _should_auto_submit_stay_hold_from_handoff(parsed.internal_json, entities)
                or _should_auto_submit_stay_hold_from_context(
                    parsed.internal_json,
                    entities,
                    user_text=normalized_text,
                    user_message=parsed.user_message,
                )
            )
        ):
            fallback_calls, fallback_response = await _auto_submit_stay_hold(
                conversation=conversation,
                entities=entities,
                language=language,
                dispatcher=dispatcher,
            )
            if fallback_calls:
                executed_calls.extend(fallback_calls)
            if fallback_response is not None:
                return _finalize_response(
                    fallback_response,
                    scope_decision=scope_result.decision,
                    language_override=language,
                    executed_calls=executed_calls,
                )
            if not fallback_calls:
                logger.warning(
                    "stay_hold_submission_missing_after_pending_approval",
                    conversation_id=str(conversation.id) if conversation.id is not None else None,
                    state=str(parsed.internal_json.state or ""),
                    next_step=str(parsed.internal_json.next_step or ""),
                )
                return _finalize_response(
                    LLMResponse(
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
                    ),
                    scope_decision=scope_result.decision,
                    language_override=language,
                    executed_calls=executed_calls,
                )
        if (
            dispatcher is not None
            and not _executed_transfer_hold_submission(executed_calls)
            and _should_auto_submit_transfer_hold(parsed.internal_json, entities, normalized_text)
        ):
            fallback_calls = await _auto_submit_transfer_hold(
                conversation=conversation,
                entities=entities,
                dispatcher=dispatcher,
            )
            if fallback_calls:
                executed_calls.extend(fallback_calls)
            else:
                logger.warning(
                    "transfer_hold_submission_missing_after_pending_approval",
                    conversation_id=str(conversation.id) if conversation.id is not None else None,
                    state=str(parsed.internal_json.state or ""),
                    next_step=str(parsed.internal_json.next_step or ""),
                )
                return _finalize_response(
                    LLMResponse(
                        user_message=(
                            "Talebinizi aldik ancak transfer kaydini teknik olarak tamamlayamadik. "
                            "Ekibimiz sizi manuel olarak en kisa surede bilgilendirecektir."
                        ),
                        internal_json=InternalJSON(
                            language=language,
                            intent="transfer_booking_create",
                            state="HANDOFF",
                            entities=entities,
                            required_questions=[],
                            handoff={"needed": True, "reason": "transfer_hold_submission_failed"},
                            risk_flags=["TOOL_ERROR_REPEAT"],
                            next_step="manual_review_required",
                        ),
                    ),
                    scope_decision=scope_result.decision,
                    language_override=language,
                    executed_calls=executed_calls,
                )
        stay_or_transfer_out_of_season = _build_stay_or_transfer_out_of_season_response(
            conversation,
            executed_calls,
            language,
        )
        if stay_or_transfer_out_of_season is not None:
            return _finalize_response(
                stay_or_transfer_out_of_season,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
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
            return _finalize_response(
                parsed,
                scope_decision=scope_result.decision,
                language_override=language,
                executed_calls=executed_calls,
            )
        if intent == "stay_quote":
            await _backfill_availability_for_quote(
                conversation=conversation,
                dispatcher=dispatcher,
                executed_calls=executed_calls,
            )
        if intent == "stay_quote" and language == "tr" and _executed_booking_quote(executed_calls):
            deterministic_messages = _build_deterministic_turkish_stay_quote_messages(
                conversation.hotel_id,
                executed_calls,
                user_text=original_user_text,
                entities=parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else None,
            )
            if deterministic_messages:
                normalized_messages = [
                    _normalize_turkish_stay_quote_reply(message, original_user_text)
                    for message in deterministic_messages
                ]
                parsed.user_message = normalized_messages[0]
                if len(normalized_messages) > 1:
                    entities = parsed.internal_json.entities if isinstance(parsed.internal_json.entities, dict) else {}
                    entities["user_message_parts"] = normalized_messages
                    parsed.internal_json.entities = entities
            else:
                parsed.user_message = _normalize_turkish_stay_quote_reply(parsed.user_message, original_user_text)
        if _executed_stay_hold_submission(executed_calls):
            parsed.user_message = _stay_pending_approval_message(language)
            parsed.internal_json.state = "PENDING_APPROVAL"
            parsed.internal_json.next_step = "await_admin_approval"
        if _executed_restaurant_hold_submission(executed_calls):
            last_restaurant_hold = _loads_tool_payload(
                next(
                    (
                        call.get("result")
                        for call in reversed(executed_calls)
                        if str(call.get("name") or "") == "restaurant_create_hold"
                    ),
                    {},
                )
            )
            approval_request_id = str(last_restaurant_hold.get("approval_request_id") or "").strip()
            hold_status = str(last_restaurant_hold.get("status") or "").strip().upper()
            if approval_request_id:
                parsed.user_message = _restaurant_pending_approval_message(language)
                parsed.internal_json.state = "PENDING_APPROVAL"
                parsed.internal_json.next_step = "await_admin_approval"
            elif hold_status in {"ONAYLANDI", "CONFIRMED"}:
                parsed.user_message = _restaurant_confirmed_message(language)
                parsed.internal_json.state = "CONFIRMED"
                parsed.internal_json.next_step = "reservation_confirmed"
        if _executed_transfer_hold_submission(executed_calls):
            parsed.user_message = _transfer_pending_approval_message(language)
            parsed.internal_json.state = "PENDING_APPROVAL"
            parsed.internal_json.next_step = "await_admin_approval"
        _enforce_single_step_collection(parsed)
        _enforce_phone_collection_prompt(parsed)
        return _finalize_response(
            parsed,
            scope_decision=scope_result.decision,
            language_override=language,
            executed_calls=executed_calls,
        )
    except LLMUnavailableError as llm_err:
        logger.warning("llm_unavailable_fallback", error_detail=str(llm_err)[:500])
        return _finalize_response(
            LLMResponse(
                user_message=_default_reply_message(target_language),
                internal_json=InternalJSON(
                    language=target_language,
                    intent="other",
                    state="INTENT_DETECTED",
                    risk_flags=[],
                    next_step="await_user_input",
                ),
            ),
            scope_decision=scope_result.decision,
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
        idle_reset_config = get_idle_reset_config(hotel_id)
        if not idle_reset_config.enabled:
            return conversation

        last_message_at = conversation.last_message_at
        if last_message_at.tzinfo is None:
            last_message_at = last_message_at.replace(tzinfo=UTC)
        inactivity_seconds = (datetime.now(UTC) - last_message_at).total_seconds()
        idle_timeout_seconds = get_idle_close_threshold_seconds(hotel_id)
        if inactivity_seconds >= idle_timeout_seconds and conversation.id is not None:
            await repository.close(conversation.id)
            logger.info(
                "conversation_auto_reset_after_inactivity",
                hotel_id=hotel_id,
                conversation_id=str(conversation.id),
                inactivity_seconds=int(inactivity_seconds),
                idle_timeout_seconds=idle_timeout_seconds,
            )
        else:
            return conversation

    initial_language = _detect_message_language(incoming.text, "tr")
    new_conversation = Conversation(
        hotel_id=hotel_id,
        phone_hash=phone_hash,
        phone_display=incoming.phone,
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
        media_items = _extract_media_items_from_incoming(incoming)
        voice_transcript_text, voice_language, voice_policy_response = await _process_voice_message(
            hotel_id=hotel_id,
            conversation_id=conversation.id,
            media_items=media_items,
            preferred_language=conversation.language,
        )
        if voice_transcript_text:
            normalized_text = _normalize_text(voice_transcript_text)
        detected_language = _detect_message_language(
            normalized_text,
            voice_language or conversation.language,
            sticky_mode=True,
        )
        if conversation.language != detected_language:
            conversation.language = detected_language
            await conversation_repository.update_language(conversation.id, detected_language)
        media_policy_response = await _analyze_media_policy_response(
            hotel_id=hotel_id,
            conversation_id=conversation.id,
            language=detected_language,
            media_items=media_items,
            user_text=normalized_text,
        )

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=normalized_text,
            whatsapp_message_id=incoming.message_id,
            reply_to_whatsapp_message_id=incoming.reply_to_message_id,
            internal_json=audit_context,
        )
        await conversation_repository.add_message(user_msg)
        conversation.messages = await conversation_repository.get_recent_messages(
            conversation.id,
            count=CONTEXT_WINDOW_MAX_MESSAGES,
        )
        reply_context = await _resolve_reply_context(
            conversation_repository,
            conversation,
            [audit_context],
        )

        await whatsapp_client.mark_as_read(incoming.message_id)

        human_override = await _is_human_override_active(conversation.phone_hash, conversation.id)
        if human_override:
            logger.info(
                "human_override_pipeline_skipped",
                conversation_id=str(conversation.id),
                phone=_mask_phone(incoming.phone),
            )
            return

        if voice_policy_response is not None:
            llm_response = voice_policy_response
        elif media_policy_response is not None:
            llm_response = media_policy_response
        else:
            llm_response = await _run_message_pipeline(
                conversation=conversation,
                normalized_text=normalized_text,
                dispatcher=dispatcher,
                expected_language=detected_language,
                reply_context=reply_context,
                current_whatsapp_phone=incoming.phone,
            )
        current_state_value = (
            str(conversation.current_state.value)
            if hasattr(conversation.current_state, "value")
            else str(conversation.current_state or "GREETING")
        )
        next_state = str(llm_response.internal_json.state or current_state_value)
        next_intent = str(llm_response.internal_json.intent or "").strip() or None
        merged_entities = _merge_entities_with_context(
            conversation.entities_json,
            llm_response.internal_json.entities if isinstance(llm_response.internal_json.entities, dict) else {},
        )
        merged_entities = _sanitize_entities_for_intent(next_intent, merged_entities)
        llm_response.internal_json.entities = merged_entities
        conversation.entities_json = merged_entities
        next_entities = merged_entities or None
        next_risk_flags = llm_response.internal_json.risk_flags or None
        await conversation_repository.update_state(
            conversation_id=conversation.id,
            state=next_state,
            intent=next_intent,
            entities=next_entities,
            risk_flags=next_risk_flags,
        )
        handoff_lock_activated = _should_activate_handoff_lock(next_state, llm_response.internal_json.handoff)
        if handoff_lock_activated:
            await _activate_handoff_guard(
                conversation_repository=conversation_repository,
                conversation=conversation,
                llm_response=llm_response,
                phone=incoming.phone,
                tools=tools,
            )

        message_parts = _extract_user_message_parts(llm_response)
        if not message_parts:
            message_parts = [llm_response.user_message]
        if handoff_lock_activated and message_parts:
            message_parts = message_parts[:1]

        for index, raw_message in enumerate(message_parts, start=1):
            reply_text = formatter.truncate(raw_message)
            send_blocked = settings.operation_mode != "ai"
            wa_message_id: str | None = None
            if settings.operation_mode == "ai":
                try:
                    send_result = await whatsapp_client.send_text_message(to=incoming.phone, body=reply_text)
                    wa_message_id = _extract_whatsapp_message_id(send_result)
                except WhatsAppSendBlockedError:
                    logger.info(
                        "whatsapp_reply_blocked_by_mode",
                        phone=incoming.phone[:3] + "***",
                        operation_mode=settings.operation_mode,
                        reply_length=len(reply_text),
                    )

            assistant_internal_json = llm_response.internal_json.model_dump(mode="json")
            assistant_internal_json["message_part_index"] = index
            assistant_internal_json["message_part_total"] = len(message_parts)
            assistant_internal_json["send_blocked"] = send_blocked
            assistant_internal_json["human_override_blocked"] = False
            assistant_internal_json["handoff_lock_activated"] = handoff_lock_activated
            if wa_message_id:
                assistant_internal_json["whatsapp_message_id"] = wa_message_id
            if settings.operation_mode == "approval":
                assistant_internal_json["approval_pending"] = True
            assistant_tool_calls = assistant_internal_json.get("tool_calls")
            if not isinstance(assistant_tool_calls, list) or not assistant_tool_calls:
                assistant_tool_calls = None

            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=reply_text,
                whatsapp_message_id=wa_message_id,
                internal_json=assistant_internal_json,
                tool_calls=assistant_tool_calls,
            )
            await conversation_repository.add_message(assistant_msg)
            conversation.messages.append(assistant_msg)
            logger.info(
                "assistant_message_persisted",
                conversation_id=str(conversation.id),
                message_part_index=index,
                message_part_total=len(message_parts),
                persisted_tool_calls_count=len(assistant_tool_calls or []),
                persisted_intent=str(assistant_internal_json.get("intent") or "").strip() or None,
                persisted_state=str(assistant_internal_json.get("state") or "").strip() or None,
                parser_error_reason=(
                    assistant_internal_json.get("entities", {})
                    .get("response_parser", {})
                    .get("reason")
                    if isinstance(assistant_internal_json.get("entities"), dict)
                    else None
                ),
            )

        escalation_result = EscalationResult()
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
        if handoff_lock_activated:
            await _finalize_handoff_transition(
                conversation=conversation,
                llm_response=llm_response,
                phone=incoming.phone,
                tools=tools,
                db_pool=db_pool,
                escalation_result=escalation_result,
            )
    except Exception:
        logger.exception(
            "whatsapp_background_processing_failed",
            message_id=incoming.message_id,
            phone=_mask_phone(incoming.phone),
        )


async def _is_human_override_active(
    phone_hash: str,
    conversation_id: Any = None,
    redis_client: Any = None,
) -> bool:
    """Check if human override is active — Redis first, then DB fallback."""
    db_override = False
    if conversation_id is not None:
        try:
            repo = ConversationRepository()
            db_override = await repo.get_human_override(conversation_id)
        except Exception:
            db_override = False

    # Try Redis (fast path), but self-heal stale phone-level locks.
    if redis_client is not None:
        try:
            val = await redis_client.get(f"velox:human_override:{phone_hash}")
            if val is not None:
                redis_override = val == "1" or val == b"1"
                if redis_override and not db_override and conversation_id is not None:
                    await redis_client.delete(f"velox:human_override:{phone_hash}")
                    logger.info(
                        "stale_human_override_cache_cleared",
                        conversation_id=str(conversation_id),
                        phone_hash=phone_hash[:8] + "***",
                    )
                    return False
                return redis_override or db_override
        except Exception:
            logger.warning("human_override_redis_read_failed", phone_hash=phone_hash[:8] + "***")

    return db_override


def _should_activate_handoff_lock(next_state: str, handoff: dict[str, Any] | None) -> bool:
    """Return True when the conversation must switch to human-only mode."""
    if str(next_state or "").upper() == "HANDOFF":
        return True
    if not isinstance(handoff, dict):
        return False
    return bool(handoff.get("needed"))


def _resolve_handoff_assignment_role(
    llm_response: LLMResponse,
    escalation_result: EscalationResult | None = None,
) -> str:
    """Resolve the owner role for a mandatory human handoff ticket."""
    if escalation_result is not None and escalation_result.route_to_role.value != "NONE":
        return escalation_result.route_to_role.value
    escalation = (
        llm_response.internal_json.escalation
        if isinstance(llm_response.internal_json.escalation, dict)
        else {}
    )
    route_to_role = str(escalation.get("route_to_role") or "ADMIN").upper()
    if route_to_role in {"ADMIN", "SALES", "OPS", "CHEF"}:
        return route_to_role
    return "ADMIN"


def _should_send_direct_admin_handoff_notify(
    assigned_role: str,
    escalation_result: EscalationResult | None = None,
    ticket_ensured: bool = True,
) -> bool:
    """ADMIN must be notified unless escalation already guarantees an ADMIN notify action."""
    _ = assigned_role
    if not ticket_ensured:
        return True
    if escalation_result is None:
        return True
    return not (
        escalation_result.route_to_role.value == "ADMIN"
        and "notify.send" in escalation_result.actions
    )


def _build_handoff_transcript_summary(messages: list[Message], limit: int = 5) -> str:
    """Create a compact summary for immediate handoff notifications."""
    lines: list[str] = []
    for message in messages[-limit:]:
        role = str(getattr(message, "role", "unknown")).upper()
        content = str(getattr(message, "content", ""))[:200]
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)


def _extract_whatsapp_message_id(send_result: Any) -> str | None:
    """Read provider WhatsApp message id from send response payload."""
    if not isinstance(send_result, dict):
        return None
    messages = send_result.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    first = messages[0]
    if not isinstance(first, dict):
        return None
    return str(first.get("id", "")).strip() or None


async def _resolve_reply_context(
    conversation_repository: ConversationRepository,
    conversation: Conversation,
    audit_contexts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Resolve a WhatsApp reply-to target into prompt-safe context."""
    if conversation.id is None:
        return None

    reply_entries = [
        ctx for ctx in audit_contexts
        if isinstance(ctx, dict) and str(ctx.get("reply_to_message_id") or "").strip()
    ]
    if not reply_entries:
        return None

    unique_reply_ids = {
        str(ctx.get("reply_to_message_id") or "").strip()
        for ctx in reply_entries
        if str(ctx.get("reply_to_message_id") or "").strip()
    }
    if len(unique_reply_ids) != 1:
        return {
            "present": True,
            "resolved": False,
            "reason": "multiple_reply_targets",
            "reply_to_message_ids": sorted(unique_reply_ids),
        }

    reply_to_message_id = next(iter(unique_reply_ids))
    target = await conversation_repository.get_by_whatsapp_message_id(
        conversation.id,
        reply_to_message_id,
    )
    if target is None:
        return {
            "present": True,
            "resolved": False,
            "reason": "target_not_found",
            "reply_to_message_id": reply_to_message_id,
        }

    reply_to_from = str(reply_entries[0].get("reply_to_from") or "").strip() or None
    return {
        "present": True,
        "resolved": True,
        "reply_to_message_id": reply_to_message_id,
        "reply_to_from": reply_to_from,
        "target_message_db_id": str(target.id) if target.id is not None else None,
        "target_role": target.role,
        "target_content": str(target.content or "")[:500],
    }


async def _activate_handoff_guard(
    *,
    conversation_repository: ConversationRepository,
    conversation: Conversation,
    llm_response: LLMResponse,
    phone: str,
    tools: dict[str, Any],
    redis_client: Any = None,
) -> None:
    """Enable human override immediately once handoff becomes terminal."""
    _ = tools
    if conversation.id is None:
        return

    await conversation_repository.set_human_override(conversation.id, True)

    if redis_client is not None:
        try:
            await redis_client.set(f"velox:human_override:{conversation.phone_hash}", "1")
        except Exception:
            logger.warning(
                "handoff_guard_redis_sync_failed",
                conversation_id=str(conversation.id),
            )

    logger.info(
        "handoff_guard_activated",
        conversation_id=str(conversation.id),
        phone=_mask_phone(phone),
        reason=str(
            (llm_response.internal_json.handoff or {}).get("reason")
            or llm_response.internal_json.next_step
            or "human_handoff"
        ),
    )

def _build_fallback_handoff_dedupe_key(conversation: Conversation, llm_response: LLMResponse) -> str:
    """Create a stable dedupe key when escalation matrix did not provide one."""
    entities = llm_response.internal_json.entities if isinstance(llm_response.internal_json.entities, dict) else {}
    reference_id = str(
        entities.get("hold_id")
        or entities.get("reservation_id")
        or conversation.phone_hash
    )
    intent = str(llm_response.internal_json.intent or "human_handoff").strip() or "human_handoff"
    reason = str((llm_response.internal_json.handoff or {}).get("reason") or "human_handoff").strip() or "human_handoff"
    raw_key = f"HANDOFF|{intent}|{reason}|{reference_id}"
    if len(raw_key) <= TICKET_DEDUPE_KEY_MAX_LENGTH:
        return raw_key
    digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:16]
    prefix_budget = TICKET_DEDUPE_KEY_MAX_LENGTH - len("|sha1:") - len(digest)
    return f"{raw_key[:prefix_budget]}|sha1:{digest}"


def _extract_handoff_ticket_id_from_tool_calls(internal_json: InternalJSON) -> str:
    """Extract already-created handoff ticket id from structured tool call history."""
    for call in internal_json.tool_calls:
        if not isinstance(call, dict):
            continue
        tool_name = str(call.get("name") or call.get("tool") or "").strip()
        if tool_name != "handoff_create_ticket":
            continue
        result = call.get("result")
        if isinstance(result, str):
            try:
                result = orjson.loads(result)
            except orjson.JSONDecodeError:
                result = {}
        if not isinstance(result, dict):
            result = {}
        ticket_id = str(result.get("ticket_id") or "").strip()
        if ticket_id:
            return ticket_id
    return ""


_STATUS_PRIORITY = {
    "sent": 1,
    "delivered": 2,
    "read": 3,
    "failed": 4,
    "undelivered": 4,
}


def _normalize_provider_status(value: str) -> str:
    """Normalize provider status labels used in webhook events."""
    status = str(value or "").strip().lower()
    if status == "undelivered":
        return "failed"
    return status


def _status_event_timestamp_iso(timestamp: int) -> str:
    """Convert webhook event timestamps into ISO8601 UTC strings."""
    if timestamp > 0:
        return datetime.fromtimestamp(timestamp, UTC).isoformat()
    return datetime.now(UTC).isoformat()


def _event_sort_key(event: dict[str, Any]) -> tuple[str, int]:
    """Sort provider events by timestamp then by semantic priority."""
    timestamp = str(event.get("timestamp") or "")
    status = _normalize_provider_status(str(event.get("status") or ""))
    return (timestamp, _STATUS_PRIORITY.get(status, 0))


def _derive_provider_status_snapshot(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive the current provider status and status timestamps from event history."""
    if not events:
        return {
            "provider_status": "unknown",
            "provider_status_updated_at": None,
            "provider_sent_at": None,
            "delivered_at": None,
            "read_at": None,
            "failed_at": None,
            "provider_error": None,
        }

    ordered = sorted(events, key=_event_sort_key)
    latest = ordered[-1]
    sent_at = next((item.get("timestamp") for item in ordered if _normalize_provider_status(str(item.get("status") or "")) == "sent"), None)
    delivered_at = next((item.get("timestamp") for item in ordered if _normalize_provider_status(str(item.get("status") or "")) == "delivered"), None)
    read_at = next((item.get("timestamp") for item in ordered if _normalize_provider_status(str(item.get("status") or "")) == "read"), None)
    failed_event = next((item for item in reversed(ordered) if _normalize_provider_status(str(item.get("status") or "")) == "failed"), None)
    return {
        "provider_status": _normalize_provider_status(str(latest.get("status") or "unknown")),
        "provider_status_updated_at": latest.get("timestamp"),
        "provider_sent_at": sent_at,
        "delivered_at": delivered_at,
        "read_at": read_at,
        "failed_at": failed_event.get("timestamp") if failed_event else None,
        "provider_error": {
            "code": failed_event.get("error_code"),
            "title": failed_event.get("error_title"),
            "details": failed_event.get("error_details"),
        } if failed_event else None,
    }


async def _persist_message_status_event(
    conversation_repository: ConversationRepository,
    event: MessageStatusEvent,
) -> bool:
    """Persist one outbound provider status event onto the matched assistant message."""
    target = await conversation_repository.get_any_by_whatsapp_message_id(event.message_id)
    if target is None or target.id is None:
        return False

    internal = target.internal_json if isinstance(target.internal_json, dict) else {}
    provider_events_raw = internal.get("provider_events")
    provider_events = provider_events_raw if isinstance(provider_events_raw, list) else []
    normalized_status = _normalize_provider_status(event.status)
    serialized_event = {
        "status": normalized_status,
        "timestamp": _status_event_timestamp_iso(event.timestamp),
        "error_code": event.error_code,
        "error_title": event.error_title,
        "error_details": event.error_details,
    }
    deduped = [
        item for item in provider_events
        if not (
            isinstance(item, dict)
            and str(item.get("status") or "") == serialized_event["status"]
            and str(item.get("timestamp") or "") == serialized_event["timestamp"]
        )
    ]
    deduped.append(serialized_event)
    deduped = sorted(
        [item for item in deduped if isinstance(item, dict)],
        key=_event_sort_key,
    )[-10:]

    internal["provider_events"] = deduped
    internal.update(_derive_provider_status_snapshot(deduped))
    await conversation_repository.update_message_internal_json(target.id, internal)
    return True


async def _finalize_handoff_transition(
    *,
    conversation: Conversation,
    llm_response: LLMResponse,
    phone: str,
    tools: dict[str, Any],
    db_pool: Any,
    escalation_result: EscalationResult | None = None,
) -> None:
    """Ensure every HANDOFF has a ticket and an ADMIN-visible operational signal."""
    if conversation.id is None:
        return

    handoff_tool = tools.get("handoff")
    notify_tool = tools.get("notify")
    assigned_role = _resolve_handoff_assignment_role(llm_response, escalation_result)
    dedupe_key = (
        escalation_result.dedupe_key
        if escalation_result is not None and escalation_result.dedupe_key
        else _build_fallback_handoff_dedupe_key(conversation, llm_response)
    )
    level = str(
        escalation_result.level.value
        if escalation_result is not None and escalation_result.level.value != "L0"
        else (llm_response.internal_json.escalation or {}).get("level") or "L2"
    )
    priority = str(
        escalation_result.sla_hint
        if escalation_result is not None and escalation_result.sla_hint in {"low", "medium", "high"}
        else (llm_response.internal_json.escalation or {}).get("sla_hint") or "high"
    )
    requested_action = str(
        (llm_response.internal_json.handoff or {}).get("reason")
        or (escalation_result.reason if escalation_result is not None else "")
        or llm_response.internal_json.next_step
        or llm_response.internal_json.intent
        or "human_handoff"
    )
    transcript_summary = _build_handoff_transcript_summary(conversation.messages)

    ticket_id = _extract_handoff_ticket_id_from_tool_calls(llm_response.internal_json)
    ticket_ensured = bool(ticket_id)
    if handoff_tool is not None and db_pool is not None:
        try:
            if ticket_ensured:
                pass
            elif dedupe_key and await EscalationEngine.check_dedupe(dedupe_key, db_pool):
                ticket_ensured = True
            else:
                ticket_result = await handoff_tool.create_ticket(
                    hotel_id=conversation.hotel_id,
                    conversation_id=str(conversation.id),
                    reason=requested_action,
                    transcript_summary=transcript_summary,
                    priority=priority,
                    assigned_to_role=assigned_role,
                    dedupe_key=dedupe_key,
                    level=level,
                    intent=str(llm_response.internal_json.intent or "human_handoff"),
                    phone=phone,
                    risk_flags=list(llm_response.internal_json.risk_flags or []),
                    requested_action=requested_action,
                )
                ticket_id = str(ticket_result.get("ticket_id") or "")
                ticket_ensured = True
        except Exception:
            logger.exception(
                "handoff_ticket_required_failed",
                conversation_id=str(conversation.id),
                assigned_to_role=assigned_role,
            )
    else:
        logger.warning(
            "handoff_ticket_tool_missing",
            conversation_id=str(conversation.id),
            has_handoff_tool=handoff_tool is not None,
            has_db_pool=db_pool is not None,
        )

    if notify_tool is None or not _should_send_direct_admin_handoff_notify(
        assigned_role,
        escalation_result,
        ticket_ensured=ticket_ensured,
    ):
        return

    profile = get_profile(conversation.hotel_id)
    hotel_name = str(
        getattr(profile, "hotel_name", None)
        or getattr(profile, "name", None)
        or f"Hotel #{conversation.hotel_id}"
    )
    try:
        notify_metadata = {
            "format_standard": "A11.8",
            "level": level,
            "intent": str(llm_response.internal_json.intent or "human_handoff"),
            "hotel_name": hotel_name,
            "guest_name": "Unknown",
            "phone": phone,
            "transcript_summary": transcript_summary,
            "requested_action": requested_action,
            "reference_id": ticket_id or str(conversation.id),
            "risk_flags": list(llm_response.internal_json.risk_flags or []),
            "priority": priority,
            "handoff_transition": True,
            "handoff_ticket_ensured": ticket_ensured,
            "handoff_assigned_role": assigned_role,
        }
        await notify_tool.send(
            hotel_id=conversation.hotel_id,
            to_role="ADMIN",
            channel="panel",
            message="Immediate handoff notification",
            metadata=notify_metadata,
        )
        await send_admin_whatsapp_alerts(
            hotel_id=conversation.hotel_id,
            message=NotifySendTool._format_message_for_delivery(
                hotel_id=conversation.hotel_id,
                to_role="ADMIN",
                message="Immediate handoff notification",
                metadata=notify_metadata,
            ),
        )
    except Exception:
        logger.exception(
            "handoff_admin_notify_failed",
            conversation_id=str(conversation.id),
        )


async def _process_burst_aggregated(
    aggregated: AggregatedMessage,
    hotel_id: int,
    dispatcher: Any,
    escalation_engine: Any,
    tools: dict[str, Any],
    db_pool: Any,
    redis_client: Any = None,
) -> None:
    """Process an aggregated burst payload through the standard pipeline.

    Each original message is stored individually for audit, but the LLM
    receives a single merged user turn so it can produce one coherent reply.
    """
    conversation_repository = ConversationRepository()
    whatsapp_client = get_whatsapp_client()
    phone_hash = _hash_phone(aggregated.phone)

    try:
        # Re-use the first audit context for conversation creation
        first_audit = aggregated.audit_contexts[0] if aggregated.audit_contexts else {}

        # Build a minimal IncomingMessage for conversation lookup
        first_incoming = IncomingMessage(
            message_id=aggregated.message_ids[0],
            phone=aggregated.phone,
            display_name=aggregated.display_name,
            text=aggregated.original_texts[0],
            timestamp=aggregated.first_timestamp,
            message_type=aggregated.message_type,
            phone_number_id=aggregated.phone_number_id,
            display_phone_number=aggregated.display_phone_number,
            media_id=str(aggregated.media_items[0].get("media_id") or "").strip() if aggregated.media_items else None,
            media_mime_type=(
                str(aggregated.media_items[0].get("mime_type") or "").strip() if aggregated.media_items else None
            ),
            media_sha256=str(aggregated.media_items[0].get("sha256") or "").strip() if aggregated.media_items else None,
            media_caption=(
                str(aggregated.media_items[0].get("caption") or "").strip() if aggregated.media_items else None
            ),
        )
        conversation = await _create_or_get_conversation(conversation_repository, first_incoming, hotel_id)
        if conversation.id is None:
            raise RuntimeError("Conversation id is missing.")

        # Detect language from the combined text
        combined_normalized = _normalize_text(aggregated.combined_text)
        detected_language = _detect_message_language(
            combined_normalized,
            conversation.language,
            sticky_mode=True,
        )
        if conversation.language != detected_language:
            conversation.language = detected_language
            await conversation_repository.update_language(conversation.id, detected_language)
        media_items = _extract_media_items_from_aggregated(aggregated)
        voice_transcript_text, voice_language, voice_policy_response = await _process_voice_message(
            hotel_id=hotel_id,
            conversation_id=conversation.id,
            media_items=media_items,
            preferred_language=conversation.language,
        )
        if voice_transcript_text:
            combined_normalized = _normalize_text(voice_transcript_text)
            detected_language = _detect_message_language(
                combined_normalized,
                voice_language or conversation.language,
                sticky_mode=True,
            )
            if conversation.language != detected_language:
                conversation.language = detected_language
                await conversation_repository.update_language(conversation.id, detected_language)
        media_policy_response = await _analyze_media_policy_response(
            hotel_id=hotel_id,
            conversation_id=conversation.id,
            language=detected_language,
            media_items=media_items,
            user_text=combined_normalized,
        )

        # Store each original message as a separate DB record (audit trail)
        user_messages: list[Message] = []
        for i, text in enumerate(aggregated.original_texts):
            audit = aggregated.audit_contexts[i] if i < len(aggregated.audit_contexts) else first_audit
            burst_audit = {
                **audit,
                "burst_part_index": i + 1,
                "burst_part_total": aggregated.part_count,
            }
            msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=_normalize_text(text),
                whatsapp_message_id=str(audit.get("message_id") or "").strip() or None,
                reply_to_whatsapp_message_id=str(audit.get("reply_to_message_id") or "").strip() or None,
                internal_json=burst_audit,
            )
            user_messages.append(msg)

        if len(user_messages) == 1:
            await conversation_repository.add_message(user_messages[0])
        else:
            await conversation_repository.add_messages_batch(user_messages)

        conversation.messages = await conversation_repository.get_recent_messages(
            conversation.id,
            count=CONTEXT_WINDOW_MAX_MESSAGES,
        )
        reply_context = await _resolve_reply_context(
            conversation_repository,
            conversation,
            aggregated.audit_contexts,
        )

        # Mark all original messages as read
        for mid in aggregated.message_ids:
            try:
                await whatsapp_client.mark_as_read(mid)
            except Exception:
                logger.warning("burst_mark_as_read_failed", message_id=mid)

        human_override = await _is_human_override_active(phone_hash, conversation.id, redis_client)
        if human_override:
            logger.info(
                "human_override_pipeline_skipped",
                conversation_id=str(conversation.id),
                phone=_mask_phone(aggregated.phone),
            )
            return

        # Build burst metadata for prompt builder
        burst_metadata: dict[str, Any] | None = None
        if aggregated.part_count > 1:
            burst_metadata = {
                "part_count": aggregated.part_count,
                "span_seconds": round(aggregated.last_timestamp - aggregated.first_timestamp, 1),
                "message_ids": aggregated.message_ids,
            }

        # Run LLM pipeline with the combined text
        if voice_policy_response is not None:
            llm_response = voice_policy_response
        elif media_policy_response is not None:
            llm_response = media_policy_response
        else:
            llm_response = await _run_message_pipeline(
                conversation=conversation,
                normalized_text=combined_normalized,
                dispatcher=dispatcher,
                expected_language=detected_language,
                burst_metadata=burst_metadata,
                reply_context=reply_context,
                current_whatsapp_phone=aggregated.phone,
            )

        # State update (same as original pipeline)
        current_state_value = (
            str(conversation.current_state.value)
            if hasattr(conversation.current_state, "value")
            else str(conversation.current_state or "GREETING")
        )
        next_state = str(llm_response.internal_json.state or current_state_value)
        next_intent = str(llm_response.internal_json.intent or "").strip() or None
        merged_entities = _merge_entities_with_context(
            conversation.entities_json,
            llm_response.internal_json.entities if isinstance(llm_response.internal_json.entities, dict) else {},
        )
        merged_entities = _sanitize_entities_for_intent(next_intent, merged_entities)
        llm_response.internal_json.entities = merged_entities
        conversation.entities_json = merged_entities
        next_entities = merged_entities or None
        next_risk_flags = llm_response.internal_json.risk_flags or None
        await conversation_repository.update_state(
            conversation_id=conversation.id,
            state=next_state,
            intent=next_intent,
            entities=next_entities,
            risk_flags=next_risk_flags,
        )
        handoff_lock_activated = _should_activate_handoff_lock(next_state, llm_response.internal_json.handoff)
        if handoff_lock_activated:
            await _activate_handoff_guard(
                conversation_repository=conversation_repository,
                conversation=conversation,
                llm_response=llm_response,
                phone=aggregated.phone,
                tools=tools,
                redis_client=redis_client,
            )

        # Send reply (single unified response)
        message_parts = _extract_user_message_parts(llm_response)
        if not message_parts:
            message_parts = [llm_response.user_message]
        if handoff_lock_activated and message_parts:
            message_parts = message_parts[:1]

        for index, raw_message in enumerate(message_parts, start=1):
            reply_text = formatter.truncate(raw_message)
            send_blocked = settings.operation_mode != "ai"
            wa_message_id: str | None = None
            if settings.operation_mode == "ai":
                try:
                    send_result = await whatsapp_client.send_text_message(to=aggregated.phone, body=reply_text)
                    wa_message_id = _extract_whatsapp_message_id(send_result)
                except WhatsAppSendBlockedError:
                    logger.info(
                        "whatsapp_reply_blocked_by_mode",
                        phone=aggregated.phone[:3] + "***",
                        operation_mode=settings.operation_mode,
                        reply_length=len(reply_text),
                    )

            assistant_internal_json = llm_response.internal_json.model_dump(mode="json")
            assistant_internal_json["message_part_index"] = index
            assistant_internal_json["message_part_total"] = len(message_parts)
            assistant_internal_json["send_blocked"] = send_blocked
            assistant_internal_json["human_override_blocked"] = False
            assistant_internal_json["handoff_lock_activated"] = handoff_lock_activated
            if wa_message_id:
                assistant_internal_json["whatsapp_message_id"] = wa_message_id
            if burst_metadata:
                assistant_internal_json["burst_metadata"] = burst_metadata
            if settings.operation_mode == "approval":
                assistant_internal_json["approval_pending"] = True
            assistant_tool_calls = assistant_internal_json.get("tool_calls")
            if not isinstance(assistant_tool_calls, list) or not assistant_tool_calls:
                assistant_tool_calls = None

            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=reply_text,
                whatsapp_message_id=wa_message_id,
                internal_json=assistant_internal_json,
                tool_calls=assistant_tool_calls,
            )
            await conversation_repository.add_message(assistant_msg)
            conversation.messages.append(assistant_msg)
            logger.info(
                "assistant_message_persisted",
                conversation_id=str(conversation.id),
                message_part_index=index,
                message_part_total=len(message_parts),
                persisted_tool_calls_count=len(assistant_tool_calls or []),
                persisted_intent=str(assistant_internal_json.get("intent") or "").strip() or None,
                persisted_state=str(assistant_internal_json.get("state") or "").strip() or None,
                parser_error_reason=(
                    assistant_internal_json.get("entities", {})
                    .get("response_parser", {})
                    .get("reason")
                    if isinstance(assistant_internal_json.get("entities"), dict)
                    else None
                ),
            )

        # Escalation post-processing
        escalation_result = EscalationResult()
        if escalation_engine is not None and db_pool is not None and "handoff" in tools and "notify" in tools:
            escalation_result = await post_process_escalation(
                user_message_text=combined_normalized,
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
        if handoff_lock_activated:
            await _finalize_handoff_transition(
                conversation=conversation,
                llm_response=llm_response,
                phone=aggregated.phone,
                tools=tools,
                db_pool=db_pool,
                escalation_result=escalation_result,
            )
    except Exception:
        logger.exception(
            "whatsapp_burst_processing_failed",
            phone=_mask_phone(aggregated.phone),
            message_count=aggregated.part_count,
            message_ids=aggregated.message_ids[:3],
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
    redis_client: Any | None = None,
) -> None:
    """Route incoming message through burst buffer (or direct processing fallback)."""
    phone_hash = _hash_phone(incoming.phone)

    buffered = BufferedMessage(
        message_id=incoming.message_id,
        phone=incoming.phone,
        display_name=incoming.display_name,
        text=incoming.text,
        timestamp=incoming.timestamp,
        message_type=incoming.message_type,
        phone_number_id=incoming.phone_number_id,
        display_phone_number=incoming.display_phone_number,
        media_id=incoming.media_id,
        media_mime_type=incoming.media_mime_type,
        media_sha256=incoming.media_sha256,
        media_caption=incoming.media_caption,
        audit_context=audit_context,
    )

    async def _burst_callback(aggregated: AggregatedMessage, h_id: int) -> None:
        await _process_burst_aggregated(
            aggregated=aggregated,
            hotel_id=h_id,
            dispatcher=dispatcher,
            escalation_engine=escalation_engine,
            tools=tools,
            db_pool=db_pool,
            redis_client=redis_client,
        )

    background_tasks.add_task(
        enqueue_or_fallback,
        redis_client,
        hotel_id,
        phone_hash,
        buffered,
        _burst_callback,
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
        status_events = webhook_handler.parse_status_events(body)
        if status_events:
            conversation_repository = ConversationRepository()
            for event in status_events:
                matched = False
                try:
                    matched = await _persist_message_status_event(conversation_repository, event)
                except Exception:
                    logger.exception(
                        "whatsapp_webhook_status_persist_failed",
                        wa_message_id=event.message_id,
                        status=event.status,
                    )
                base_payload = {
                    "wa_message_id": event.message_id,
                    "status": event.status,
                    "recipient": _mask_phone(event.recipient_id),
                    "status_timestamp": event.timestamp,
                    "matched_message": matched,
                }
                if event.status.lower() in {"failed", "undelivered"}:
                    logger.warning(
                        "whatsapp_webhook_status_failed",
                        **base_payload,
                        error_code=event.error_code,
                        error_title=event.error_title,
                    )
                else:
                    logger.info("whatsapp_webhook_status_event", **base_payload)
        else:
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
        await sync_operation_mode_from_redis(redis_client)
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
        "wa_id": incoming.phone,
        "wa_id_masked": _mask_phone(incoming.phone),
        "wa_id_hash": phone_hash,
        "message_id": incoming.message_id,
        "message_type": incoming.message_type,
        "reply_to_message_id": incoming.reply_to_message_id,
        "reply_to_from": incoming.reply_to_from,
        "media": {
            "id": incoming.media_id,
            "type": incoming.message_type if incoming.media_id else "",
            "mime_type": incoming.media_mime_type,
            "sha256": incoming.media_sha256,
            "caption": incoming.media_caption,
        }
        if incoming.media_id
        else {},
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
        redis_client=redis_client,
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
