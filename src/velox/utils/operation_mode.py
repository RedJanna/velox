"""Shared helpers for persisted operation mode management."""

from __future__ import annotations

from typing import Any

import structlog

from velox.config.settings import settings

logger = structlog.get_logger(__name__)

REDIS_OPERATION_MODE_KEY = "velox:operation_mode"
VALID_OPERATION_MODES = {"test", "ai", "approval", "off"}


async def sync_operation_mode_from_redis(redis_client: Any) -> str:
    """Refresh in-memory operation mode from Redis when available."""
    if redis_client is None:
        return settings.operation_mode
    try:
        stored_mode = await redis_client.get(REDIS_OPERATION_MODE_KEY)
    except Exception:
        logger.warning("operation_mode_redis_read_failed")
        return settings.operation_mode
    if isinstance(stored_mode, str) and stored_mode in VALID_OPERATION_MODES:
        settings.operation_mode = stored_mode
    return settings.operation_mode
