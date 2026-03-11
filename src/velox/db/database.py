"""AsyncPG database connection pool manager."""

import asyncio
from time import perf_counter
from typing import cast

import asyncpg  # type: ignore[import-untyped]
import structlog

from velox.config.constants import (
    MAX_STARTUP_RETRIES,
    STARTUP_DEPENDENCY_TIMEOUT_SECONDS,
    STARTUP_RETRY_BACKOFF_SECONDS,
)
from velox.config.settings import settings

logger = structlog.get_logger(__name__)

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> asyncpg.Pool:
    """Initialize the asyncpg connection pool. Call once at app startup."""
    global _pool
    if _pool is not None:
        return _pool

    logger.info(
        "db_pool_init_start",
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
    )

    last_error: Exception | None = None
    for attempt in range(1, MAX_STARTUP_RETRIES + 1):
        started = perf_counter()
        try:
            pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                min_size=settings.db_pool_min,
                max_size=settings.db_pool_max,
                command_timeout=30,
                timeout=STARTUP_DEPENDENCY_TIMEOUT_SECONDS,
            )
            _pool = pool
            logger.info(
                "db_pool_init_done",
                attempt_number=attempt,
                duration_ms=int((perf_counter() - started) * 1000),
            )
            return pool
        except Exception as exc:
            last_error = exc
            logger.warning(
                "db_pool_init_failed",
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                attempt_number=attempt,
                duration_ms=int((perf_counter() - started) * 1000),
                error_type=type(exc).__name__,
            )
            if attempt >= MAX_STARTUP_RETRIES:
                break
            backoff = STARTUP_RETRY_BACKOFF_SECONDS[
                min(attempt - 1, len(STARTUP_RETRY_BACKOFF_SECONDS) - 1)
            ]
            await asyncio.sleep(backoff)

    logger.error(
        "db_pool_init_exhausted",
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        max_attempts=MAX_STARTUP_RETRIES,
        error_type=type(last_error).__name__ if last_error is not None else None,
    )
    raise RuntimeError("Database dependency unavailable during startup.") from last_error


async def close_db_pool() -> None:
    """Close the asyncpg connection pool. Call once at app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("db_pool_closed")


def get_pool() -> asyncpg.Pool:
    """Get the current connection pool. Raises RuntimeError if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _pool


async def execute(query: str, *args: object) -> str:
    """Execute a query that does not return rows (INSERT/UPDATE/DELETE)."""
    pool = get_pool()
    return cast(str, await pool.execute(query, *args))


async def fetch(query: str, *args: object) -> list[asyncpg.Record]:
    """Execute a query and return all result rows."""
    pool = get_pool()
    return cast(list[asyncpg.Record], await pool.fetch(query, *args))


async def fetchrow(query: str, *args: object) -> asyncpg.Record | None:
    """Execute a query and return a single row or None."""
    pool = get_pool()
    return await pool.fetchrow(query, *args)


async def fetchval(query: str, *args: object) -> object:
    """Execute a query and return a single value."""
    pool = get_pool()
    return cast(object, await pool.fetchval(query, *args))
