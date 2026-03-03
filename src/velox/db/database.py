"""AsyncPG database connection pool manager."""

import asyncpg
import structlog

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

    _pool = await asyncpg.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        command_timeout=30,
    )
    logger.info("db_pool_init_done")
    return _pool


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
    return await pool.execute(query, *args)


async def fetch(query: str, *args: object) -> list[asyncpg.Record]:
    """Execute a query and return all result rows."""
    pool = get_pool()
    return await pool.fetch(query, *args)


async def fetchrow(query: str, *args: object) -> asyncpg.Record | None:
    """Execute a query and return a single row or None."""
    pool = get_pool()
    return await pool.fetchrow(query, *args)


async def fetchval(query: str, *args: object) -> object:
    """Execute a query and return a single value."""
    pool = get_pool()
    return await pool.fetchval(query, *args)
