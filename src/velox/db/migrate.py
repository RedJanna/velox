"""Versioned SQL migration runner for existing and fresh Velox databases."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg
import structlog

from velox.db.database import close_db_pool, init_db_pool
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)

MIGRATION_TIMEOUT_SECONDS = 60
MIGRATION_SIGNATURES = {
    "001": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'hotels'
        )
    """,
    "002": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'admin_trusted_devices'
        )
    """,
    "003": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'messages'
              AND column_name = 'client_message_id'
        )
    """,
    "004": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'notification_phones'
        )
    """,
    "005": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'stay_holds'
              AND column_name = 'workflow_state'
        )
    """,
    "006": """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public' AND indexname = 'idx_conversations_hotel_last_message'
        )
    """,
    "007": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'whatsapp_numbers'
        )
    """,
    "008": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'conversations'
              AND column_name = 'human_override'
        )
    """,
    "009": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'stay_holds'
              AND column_name = 'reservation_no'
        )
    """,
    "010": """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'messages'
              AND column_name = 'whatsapp_message_id'
        )
    """,
}


@dataclass(frozen=True)
class SqlMigration:
    """Represents one versioned SQL migration file."""

    version: str
    filename: str
    path: Path
    signature_query: str | None = None


def _migration_dir() -> Path:
    """Resolve the SQL migration directory for local and container runs."""
    return get_project_root(__file__) / "src" / "velox" / "db" / "migrations"


def _load_sql_migrations() -> list[SqlMigration]:
    """Return sorted SQL migrations discovered on disk."""
    migrations: list[SqlMigration] = []
    for path in sorted(_migration_dir().glob("[0-9][0-9][0-9]_*.sql")):
        version = path.stem.split("_", maxsplit=1)[0]
        migrations.append(
            SqlMigration(
                version=version,
                filename=path.name,
                path=path,
                signature_query=MIGRATION_SIGNATURES.get(version),
            )
        )
    return migrations


async def _ensure_schema_migrations_table(conn: asyncpg.Connection) -> None:
    """Create migration history table when absent."""
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(16) PRIMARY KEY,
            filename TEXT NOT NULL,
            applied_via VARCHAR(16) NOT NULL DEFAULT 'executed',
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        timeout=MIGRATION_TIMEOUT_SECONDS,
    )


async def _applied_versions(conn: asyncpg.Connection) -> set[str]:
    """Return already recorded migration versions."""
    rows = await conn.fetch(
        "SELECT version FROM schema_migrations ORDER BY version",
        timeout=MIGRATION_TIMEOUT_SECONDS,
    )
    return {str(row["version"]) for row in rows}


async def _record_migration(
    conn: asyncpg.Connection,
    migration: SqlMigration,
    *,
    applied_via: str,
) -> None:
    """Record executed or detected migration into history table."""
    await conn.execute(
        """
        INSERT INTO schema_migrations (version, filename, applied_via)
        VALUES ($1, $2, $3)
        ON CONFLICT (version) DO NOTHING
        """,
        migration.version,
        migration.filename,
        applied_via,
        timeout=MIGRATION_TIMEOUT_SECONDS,
    )


async def _bootstrap_existing_history(
    conn: asyncpg.Connection,
    migrations: list[SqlMigration],
) -> list[str]:
    """Backfill history rows for schemas that already contain a migration's signature."""
    recorded = await _applied_versions(conn)
    detected: list[str] = []
    for migration in migrations:
        if migration.version in recorded or not migration.signature_query:
            continue
        exists = bool(await conn.fetchval(migration.signature_query, timeout=MIGRATION_TIMEOUT_SECONDS))
        if not exists:
            continue
        await _record_migration(conn, migration, applied_via="detected")
        detected.append(migration.filename)
    return detected


async def apply_pending_migrations(pool: asyncpg.Pool) -> dict[str, Any]:
    """Apply missing SQL migrations and return a structured status payload."""
    migrations = _load_sql_migrations()
    async with pool.acquire() as conn:
        await _ensure_schema_migrations_table(conn)
        detected = await _bootstrap_existing_history(conn, migrations)
        recorded = await _applied_versions(conn)

        executed: list[str] = []
        for migration in migrations:
            if migration.version in recorded:
                continue
            sql = migration.path.read_text(encoding="utf-8")
            logger.info("db_migration_apply_start", version=migration.version, filename=migration.filename)
            await conn.execute(sql, timeout=MIGRATION_TIMEOUT_SECONDS)
            await _record_migration(conn, migration, applied_via="executed")
            recorded.add(migration.version)
            executed.append(migration.filename)
            logger.info("db_migration_apply_done", version=migration.version, filename=migration.filename)

    pending = [migration.filename for migration in migrations if migration.version not in recorded]
    return {
        "ok": not pending,
        "detected_existing": detected,
        "executed": executed,
        "pending": pending,
    }


async def _run_cli() -> None:
    """CLI entry point used by `python -m velox.db.migrate`."""
    pool = await init_db_pool()
    try:
        result = await apply_pending_migrations(pool)
        logger.info("db_migration_status", **result)
    finally:
        await close_db_pool()


if __name__ == "__main__":
    asyncio.run(_run_cli())
