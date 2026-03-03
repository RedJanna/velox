"""WhatsApp webhook routes for verification and incoming messages."""

from collections import defaultdict, deque
import hashlib
import re
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
import orjson
import structlog

from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.adapters.whatsapp.webhook import IncomingMessage, WhatsAppWebhook
from velox.config.settings import settings
from velox.db.repositories.conversation import ConversationRepository
from velox.models.conversation import Conversation, Message

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

DEDUPE_TTL_SECONDS = 3600
MAX_TEXT_LENGTH = 4096

PAYMENT_DATA_PATTERN = re.compile(
    r"(\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b)|(\bcvv\b)|(\botp\b)",
    flags=re.IGNORECASE,
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


async def _run_message_pipeline(_conversation: Conversation, normalized_text: str) -> str:
    """Run message pipeline and return assistant reply text."""
    if PAYMENT_DATA_PATTERN.search(normalized_text):
        return _payment_warning_message()
    # Task 06 will replace this fallback with LLM + tools pipeline.
    return _default_reply_message()


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


async def _process_incoming_message(incoming: IncomingMessage) -> None:
    """Background pipeline: log message, generate response, and send via WhatsApp."""
    conversation_repository = ConversationRepository()
    whatsapp_client = get_whatsapp_client()

    try:
        conversation = await _create_or_get_conversation(conversation_repository, incoming)
        if conversation.id is None:
            raise RuntimeError("Conversation id is missing.")

        normalized_text = _normalize_text(incoming.text)

        await conversation_repository.add_message(
            Message(
                conversation_id=conversation.id,
                role="user",
                content=normalized_text,
            )
        )

        await whatsapp_client.mark_as_read(incoming.message_id)

        reply_text = await _run_message_pipeline(conversation, normalized_text)
        reply_text = formatter.truncate(reply_text)
        await whatsapp_client.send_text_message(to=incoming.phone, body=reply_text)

        await conversation_repository.add_message(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=reply_text,
            )
        )
    except Exception:
        logger.exception(
            "whatsapp_background_processing_failed",
            message_id=incoming.message_id,
            phone=_mask_phone(incoming.phone),
        )


def _schedule_background_task(background_tasks: BackgroundTasks, incoming: IncomingMessage) -> None:
    """Add incoming message task to FastAPI background worker."""
    background_tasks.add_task(_process_incoming_message, incoming)


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> str:
    """Meta webhook verification endpoint."""
    challenge = webhook_handler.verify_subscription(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return challenge


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

    _schedule_background_task(background_tasks, incoming)
    logger.info("whatsapp_webhook_message_accepted", phone=_mask_phone(incoming.phone), message_type=incoming.message_type)
    return {"status": "accepted"}
