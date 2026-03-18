"""Burst-message buffer: debounce, aggregate, and serialize per-conversation processing.

When a guest sends multiple WhatsApp messages in rapid succession (e.g. "Merhaba" +
"yarın akşam yemeği için" + "2 kişilik masa"), this module collects them into a single
aggregated payload before handing off to the LLM pipeline.  This avoids race conditions,
duplicate responses, and wasted LLM calls.

Components
----------
* **Redis buffer** — incoming messages are RPUSH'd into a per-phone sorted list.
* **Debounce timer** — a Redis key with short TTL; each new message resets the timer.
  When the timer expires (no new message within the window), the buffer is flushed.
* **Aggregator** — reads all buffered messages, orders by original timestamp, and
  produces a single ``AggregatedMessage`` for downstream processing.
* **Distributed conversation lock** — a Redis SETNX lock that prevents two replicas
  from processing the same conversation simultaneously.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import orjson
import structlog

from velox.config.settings import settings

logger = structlog.get_logger(__name__)

# Redis key patterns
_BUFFER_KEY = "burst:buf:{hotel_id}:{phone_hash}"
_TIMER_KEY = "burst:tmr:{hotel_id}:{phone_hash}"
_LOCK_KEY = "burst:lock:{hotel_id}:{phone_hash}"

# Debounce watcher polling interval (seconds)
_POLL_INTERVAL = 0.4


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class BufferedMessage:
    """Single message stored in the Redis buffer."""

    message_id: str
    phone: str
    display_name: str
    text: str
    timestamp: int
    message_type: str
    phone_number_id: str | None = None
    display_phone_number: str | None = None
    audit_context: dict[str, Any] = field(default_factory=dict)
    enqueued_at: float = 0.0


@dataclass(slots=True)
class AggregatedMessage:
    """Result of flushing and merging the burst buffer."""

    phone: str
    display_name: str
    phone_number_id: str | None
    display_phone_number: str | None
    combined_text: str
    original_texts: list[str]
    message_ids: list[str]
    first_timestamp: int
    last_timestamp: int
    part_count: int
    message_type: str
    audit_contexts: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------
def _serialize(msg: BufferedMessage) -> bytes:
    return orjson.dumps(
        {
            "message_id": msg.message_id,
            "phone": msg.phone,
            "display_name": msg.display_name,
            "text": msg.text,
            "timestamp": msg.timestamp,
            "message_type": msg.message_type,
            "phone_number_id": msg.phone_number_id,
            "display_phone_number": msg.display_phone_number,
            "audit_context": msg.audit_context,
            "enqueued_at": msg.enqueued_at,
        }
    )


def _deserialize(raw: bytes | str) -> BufferedMessage:
    data = orjson.loads(raw)
    return BufferedMessage(**data)


# ---------------------------------------------------------------------------
# Key builders
# ---------------------------------------------------------------------------
def _buf_key(hotel_id: int, phone_hash: str) -> str:
    return _BUFFER_KEY.format(hotel_id=hotel_id, phone_hash=phone_hash)


def _tmr_key(hotel_id: int, phone_hash: str) -> str:
    return _TIMER_KEY.format(hotel_id=hotel_id, phone_hash=phone_hash)


def _lock_key(hotel_id: int, phone_hash: str) -> str:
    return _LOCK_KEY.format(hotel_id=hotel_id, phone_hash=phone_hash)


# ---------------------------------------------------------------------------
# Distributed conversation lock
# ---------------------------------------------------------------------------
class ConversationLock:
    """Redis-based distributed lock for per-conversation serialization."""

    def __init__(self, redis: Any, hotel_id: int, phone_hash: str) -> None:
        self._redis = redis
        self._key = _lock_key(hotel_id, phone_hash)
        self._ttl = settings.burst_lock_ttl_seconds

    async def acquire(self, retries: int = 3, retry_delay: float = 1.0) -> bool:
        """Try to acquire the lock with optional retries."""
        for attempt in range(retries):
            acquired = await self._redis.set(self._key, "1", ex=self._ttl, nx=True)
            if acquired:
                return True
            if attempt < retries - 1:
                await asyncio.sleep(retry_delay)
        return False

    async def release(self) -> None:
        """Release the lock."""
        try:
            await self._redis.delete(self._key)
        except Exception:
            logger.warning("burst_lock_release_failed", key=self._key)


# ---------------------------------------------------------------------------
# Core buffer operations
# ---------------------------------------------------------------------------
async def enqueue_message(
    redis: Any,
    hotel_id: int,
    phone_hash: str,
    msg: BufferedMessage,
    process_callback: Any,
) -> None:
    """Add a message to the burst buffer and manage the debounce timer.

    Parameters
    ----------
    redis : aioredis / redis.asyncio client
    hotel_id : resolved hotel id
    phone_hash : hashed phone number
    msg : the incoming message to buffer
    process_callback : ``async def(AggregatedMessage, hotel_id, ...)``
        Called when the buffer is flushed.  The webhook module passes a
        closure that feeds the aggregated payload into the existing
        ``_process_incoming_message`` pipeline.
    """
    buf_key = _buf_key(hotel_id, phone_hash)
    tmr_key = _tmr_key(hotel_id, phone_hash)

    msg.enqueued_at = time.time()
    await redis.rpush(buf_key, _serialize(msg))
    # Safety TTL on the buffer list so orphan keys expire
    await redis.expire(buf_key, int(settings.burst_max_wait_seconds) + 10)

    buffer_size = await redis.llen(buf_key)

    # Hard cap — flush immediately if too many messages queued
    if buffer_size >= settings.burst_max_messages:
        logger.info(
            "burst_hard_cap_flush",
            hotel_id=hotel_id,
            phone_hash=phone_hash[:8],
            buffer_size=buffer_size,
        )
        await _flush_and_process(redis, hotel_id, phone_hash, process_callback)
        return

    # Media message — flush immediately (media needs immediate context)
    if msg.message_type not in ("text",):
        logger.info(
            "burst_media_flush",
            hotel_id=hotel_id,
            phone_hash=phone_hash[:8],
            message_type=msg.message_type,
        )
        await _flush_and_process(redis, hotel_id, phone_hash, process_callback)
        return

    # Debounce: set/reset timer
    debounce_ms = int(settings.burst_debounce_seconds * 1000)
    is_new_timer = await redis.set(tmr_key, "1", px=debounce_ms, nx=True)

    if is_new_timer:
        # First message in burst — start a watcher task
        asyncio.create_task(
            _debounce_watcher(redis, hotel_id, phone_hash, process_callback)
        )
    else:
        # Subsequent message — reset the timer
        await redis.pexpire(tmr_key, debounce_ms)


async def _debounce_watcher(
    redis: Any,
    hotel_id: int,
    phone_hash: str,
    process_callback: Any,
) -> None:
    """Poll until the debounce timer expires, then flush the buffer."""
    tmr_key = _tmr_key(hotel_id, phone_hash)
    buf_key = _buf_key(hotel_id, phone_hash)
    max_wait = settings.burst_max_wait_seconds
    started = time.monotonic()

    try:
        while True:
            await asyncio.sleep(_POLL_INTERVAL)

            # Hard timeout guard
            elapsed = time.monotonic() - started
            if elapsed >= max_wait:
                logger.info(
                    "burst_max_wait_flush",
                    hotel_id=hotel_id,
                    phone_hash=phone_hash[:8],
                    elapsed_s=round(elapsed, 1),
                )
                break

            # Timer key gone means debounce window expired
            timer_alive = await redis.exists(tmr_key)
            if not timer_alive:
                break

        # Only flush if there are messages in the buffer
        buffer_size = await redis.llen(buf_key)
        if buffer_size > 0:
            await _flush_and_process(redis, hotel_id, phone_hash, process_callback)
    except Exception:
        logger.exception(
            "burst_debounce_watcher_error",
            hotel_id=hotel_id,
            phone_hash=phone_hash[:8],
        )


async def _flush_and_process(
    redis: Any,
    hotel_id: int,
    phone_hash: str,
    process_callback: Any,
) -> None:
    """Atomically drain the buffer, aggregate messages, acquire lock, and process."""
    buf_key = _buf_key(hotel_id, phone_hash)
    tmr_key = _tmr_key(hotel_id, phone_hash)

    # Atomically read + delete the buffer (pipeline for atomicity)
    pipe = redis.pipeline(transaction=True)
    pipe.lrange(buf_key, 0, -1)
    pipe.delete(buf_key)
    pipe.delete(tmr_key)
    results = await pipe.execute()
    raw_entries: list[bytes] = results[0]

    if not raw_entries:
        return

    # Deserialize and sort by original WhatsApp timestamp
    buffered: list[BufferedMessage] = []
    for raw in raw_entries:
        try:
            buffered.append(_deserialize(raw))
        except Exception:
            logger.warning("burst_deserialize_failed", raw_preview=str(raw)[:80])

    if not buffered:
        return

    buffered.sort(key=lambda m: m.timestamp)

    aggregated = _aggregate(buffered)

    logger.info(
        "burst_aggregated",
        hotel_id=hotel_id,
        phone_hash=phone_hash[:8],
        message_count=aggregated.part_count,
        first_ts=aggregated.first_timestamp,
        last_ts=aggregated.last_timestamp,
        debounce_span_ms=int((aggregated.last_timestamp - aggregated.first_timestamp) * 1000)
        if aggregated.part_count > 1
        else 0,
    )

    # Acquire conversation lock
    lock = ConversationLock(redis, hotel_id, phone_hash)
    acquired = await lock.acquire(retries=5, retry_delay=1.5)
    if not acquired:
        logger.error(
            "burst_lock_acquisition_failed",
            hotel_id=hotel_id,
            phone_hash=phone_hash[:8],
            message_count=aggregated.part_count,
        )
        # Re-enqueue messages so they are not lost
        for bm in buffered:
            await redis.rpush(buf_key, _serialize(bm))
        await redis.expire(buf_key, int(settings.burst_max_wait_seconds) + 10)
        return

    try:
        await process_callback(aggregated, hotel_id)
    except Exception:
        logger.exception(
            "burst_process_callback_error",
            hotel_id=hotel_id,
            phone_hash=phone_hash[:8],
        )
    finally:
        await lock.release()

        # After releasing the lock, check if new messages arrived during processing
        pending = await redis.llen(buf_key)
        if pending > 0:
            logger.info(
                "burst_post_lock_requeue",
                hotel_id=hotel_id,
                phone_hash=phone_hash[:8],
                pending=pending,
            )
            asyncio.create_task(
                _flush_and_process(redis, hotel_id, phone_hash, process_callback)
            )


def _aggregate(messages: list[BufferedMessage]) -> AggregatedMessage:
    """Merge sorted buffered messages into a single aggregated payload."""
    texts = [m.text for m in messages]
    first = messages[0]
    last = messages[-1]

    if len(messages) == 1:
        combined = texts[0]
    else:
        combined = "\n".join(texts)

    return AggregatedMessage(
        phone=first.phone,
        display_name=first.display_name,
        phone_number_id=first.phone_number_id,
        display_phone_number=first.display_phone_number,
        combined_text=combined,
        original_texts=texts,
        message_ids=[m.message_id for m in messages],
        first_timestamp=first.timestamp,
        last_timestamp=last.timestamp,
        part_count=len(messages),
        message_type=first.message_type,
        audit_contexts=[m.audit_context for m in messages],
    )


# ---------------------------------------------------------------------------
# Fallback for when Redis is unavailable
# ---------------------------------------------------------------------------
class InMemoryBurstBuffer:
    """Process-local fallback that still provides conversation-level locking.

    This does NOT aggregate across replicas, but it prevents race conditions
    within a single app process — matching the existing test_chat.py pattern.
    """

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._guard = asyncio.Lock()
        self._buffers: dict[str, list[BufferedMessage]] = {}
        self._timers: dict[str, asyncio.Task[None]] = {}

    def _key(self, hotel_id: int, phone_hash: str) -> str:
        return f"{hotel_id}:{phone_hash}"

    async def _get_lock(self, key: str) -> asyncio.Lock:
        async with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock

    async def enqueue_message(
        self,
        hotel_id: int,
        phone_hash: str,
        msg: BufferedMessage,
        process_callback: Any,
    ) -> None:
        key = self._key(hotel_id, phone_hash)
        if key not in self._buffers:
            self._buffers[key] = []
        self._buffers[key].append(msg)

        # Hard cap
        if len(self._buffers[key]) >= settings.burst_max_messages:
            await self._flush(key, hotel_id, phone_hash, process_callback)
            return

        # Media
        if msg.message_type not in ("text",):
            await self._flush(key, hotel_id, phone_hash, process_callback)
            return

        # Debounce: cancel existing timer, start new one
        existing = self._timers.get(key)
        if existing is not None and not existing.done():
            existing.cancel()

        self._timers[key] = asyncio.create_task(
            self._debounce_then_flush(key, hotel_id, phone_hash, process_callback)
        )

    async def _debounce_then_flush(
        self,
        key: str,
        hotel_id: int,
        phone_hash: str,
        process_callback: Any,
    ) -> None:
        try:
            await asyncio.sleep(settings.burst_debounce_seconds)
            await self._flush(key, hotel_id, phone_hash, process_callback)
        except asyncio.CancelledError:
            pass  # Timer reset by a new message

    async def _flush(
        self,
        key: str,
        hotel_id: int,
        phone_hash: str,
        process_callback: Any,
    ) -> None:
        # Cancel pending timer
        existing = self._timers.pop(key, None)
        if existing is not None and not existing.done():
            existing.cancel()

        messages = self._buffers.pop(key, [])
        if not messages:
            return

        messages.sort(key=lambda m: m.timestamp)
        aggregated = _aggregate(messages)

        lock = await self._get_lock(key)
        async with lock:
            try:
                await process_callback(aggregated, hotel_id)
            except Exception:
                logger.exception(
                    "burst_local_process_error",
                    hotel_id=hotel_id,
                    phone_hash=phone_hash[:8],
                )


# Process-level singleton for Redis-unavailable fallback
_local_buffer = InMemoryBurstBuffer()


async def enqueue_or_fallback(
    redis: Any | None,
    hotel_id: int,
    phone_hash: str,
    msg: BufferedMessage,
    process_callback: Any,
) -> None:
    """Route to Redis-backed buffer or in-memory fallback."""
    if redis is not None:
        try:
            await enqueue_message(redis, hotel_id, phone_hash, msg, process_callback)
            return
        except Exception:
            logger.warning(
                "burst_redis_error_fallback_to_local",
                hotel_id=hotel_id,
                phone_hash=phone_hash[:8],
            )
    await _local_buffer.enqueue_message(hotel_id, phone_hash, msg, process_callback)
