"""Proactive conversation idle-reset background worker.

When the bot sends a reply and the customer does not respond within the
configured timeout, the conversation is automatically closed.  A warning
WhatsApp message is sent a configurable number of minutes before the close,
and a farewell message is sent when the conversation is actually closed.

All timing thresholds and message templates are read from each hotel's
``ConversationIdleResetConfig`` inside ``HotelProfile``, so they can be
tuned per-hotel from the admin panel.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.core.conversation_idle_policy import (
    get_idle_close_threshold_seconds,
    get_idle_reset_config,
    get_idle_warning_threshold_seconds,
    render_idle_reset_message,
)
from velox.core.hotel_profile_loader import get_all_profiles
from velox.db.repositories.conversation import ConversationRepository
from velox.models.hotel_profile import ConversationIdleResetConfig

logger = structlog.get_logger(__name__)

# How often the background loop runs a sweep (seconds).
CHECK_INTERVAL_SECONDS = 60

# In-memory set that tracks conversation IDs for which a warning has already
# been sent during this process lifetime.  Cleared automatically when the
# conversation is closed or when the process restarts.
_warned_conversation_ids: set[str] = set()
def _compute_idle_query_bounds() -> tuple[int, int, int]:
    """Return warning-range and close-threshold bounds across hotel configs.

    Returns tuple:
    - warning_min_seconds
    - warning_max_seconds
    - close_min_seconds
    """
    configs: list[ConversationIdleResetConfig] = [ConversationIdleResetConfig()]
    for profile in get_all_profiles().values():
        configs.append(profile.conversation_idle_reset)

    warning_starts: list[int] = []
    close_thresholds: list[int] = []
    for cfg in configs:
        if not cfg.enabled:
            continue
        close_seconds = max(0, int(cfg.idle_timeout_minutes) * 60)
        warning_start = max(0, int(cfg.idle_timeout_minutes - cfg.warning_before_minutes) * 60)
        warning_starts.append(warning_start)
        close_thresholds.append(close_seconds)

    if not close_thresholds:
        default_cfg = ConversationIdleResetConfig()
        close_seconds = max(0, int(default_cfg.idle_timeout_minutes) * 60)
        warning_start = max(0, int(default_cfg.idle_timeout_minutes - default_cfg.warning_before_minutes) * 60)
        warning_starts = [warning_start]
        close_thresholds = [close_seconds]

    warning_min = min(warning_starts)
    warning_max = max(close_thresholds) + CHECK_INTERVAL_SECONDS
    close_min = min(close_thresholds)
    return warning_min, warning_max, close_min


async def _send_whatsapp_safe(phone: str, body: str, *, context: dict[str, Any]) -> bool:
    """Send a WhatsApp text message, swallowing errors so the sweep continues."""
    try:
        client = get_whatsapp_client()
        await client.send_text_message(phone, body, force=True)
        return True
    except Exception:
        logger.exception("idle_reset_send_failed", **context)
        return False


async def _process_warnings(repo: ConversationRepository) -> int:
    """Send warning messages for conversations approaching timeout.

    Returns the number of warnings sent.
    """
    sent = 0
    warning_start, warning_end, _ = _compute_idle_query_bounds()

    warn_candidates = await repo.get_idle_after_assistant_in_range(warning_start, warning_end)
    for conv in warn_candidates:
        if conv.id is None or conv.phone_display is None:
            continue
        conv_id_str = str(conv.id)
        if conv_id_str in _warned_conversation_ids:
            continue

        cfg = get_idle_reset_config(conv.hotel_id)
        if not cfg.enabled:
            continue

        # Verify per-hotel timing is actually in the warning window.
        from datetime import UTC, datetime
        last = conv.last_message_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        elapsed = (datetime.now(UTC) - last).total_seconds()
        hotel_warning_threshold = get_idle_warning_threshold_seconds(conv.hotel_id)
        hotel_close_threshold = get_idle_close_threshold_seconds(conv.hotel_id)
        if elapsed < hotel_warning_threshold or elapsed >= hotel_close_threshold:
            continue

        body = render_idle_reset_message(cfg, conv.language, "warning")
        ok = await _send_whatsapp_safe(conv.phone_display, body, context={
            "conversation_id": conv_id_str,
            "hotel_id": conv.hotel_id,
            "kind": "warning",
        })
        if ok:
            _warned_conversation_ids.add(conv_id_str)
            sent += 1
            logger.info(
                "idle_reset_warning_sent",
                conversation_id=conv_id_str,
                hotel_id=conv.hotel_id,
            )

    return sent


async def _process_closes(repo: ConversationRepository) -> int:
    """Close stale conversations and send farewell messages.

    Returns the number of conversations closed.
    """
    closed = 0
    _, _, close_threshold = _compute_idle_query_bounds()

    stale = await repo.get_idle_after_assistant(close_threshold)
    for conv in stale:
        if conv.id is None:
            continue

        cfg = get_idle_reset_config(conv.hotel_id)
        if not cfg.enabled:
            continue

        # Verify per-hotel threshold
        from datetime import UTC, datetime
        last = conv.last_message_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        elapsed = (datetime.now(UTC) - last).total_seconds()
        hotel_close_threshold = get_idle_close_threshold_seconds(conv.hotel_id)
        if elapsed < hotel_close_threshold:
            continue

        conv_id_str = str(conv.id)

        # Send farewell message before closing
        if conv.phone_display:
            body = render_idle_reset_message(cfg, conv.language, "closed")
            await _send_whatsapp_safe(conv.phone_display, body, context={
                "conversation_id": conv_id_str,
                "hotel_id": conv.hotel_id,
                "kind": "closed",
            })

        await repo.close(conv.id)
        _warned_conversation_ids.discard(conv_id_str)
        closed += 1
        logger.info(
            "conversation_proactive_idle_reset",
            conversation_id=conv_id_str,
            hotel_id=conv.hotel_id,
        )

    return closed


async def run_idle_reset_loop() -> None:
    """Long-running background loop that periodically checks for idle
    conversations, sends warning messages, and closes timed-out ones.

    Designed to be launched via ``asyncio.create_task()`` from the
    application lifespan.
    """
    repo = ConversationRepository()
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            warnings_sent = await _process_warnings(repo)
            closed_count = await _process_closes(repo)
            if warnings_sent or closed_count:
                logger.info(
                    "idle_reset_sweep_complete",
                    warnings_sent=warnings_sent,
                    closed_count=closed_count,
                )
        except asyncio.CancelledError:
            logger.info("idle_reset_background_loop_cancelled")
            return
        except Exception:
            logger.exception("idle_reset_loop_unexpected_error")
            await asyncio.sleep(60)


def clear_warned_ids() -> None:
    """Clear the in-memory warned-IDs set.  Useful for testing."""
    _warned_conversation_ids.clear()
