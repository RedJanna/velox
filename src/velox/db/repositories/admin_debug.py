"""Repository for admin debug runs, findings, and artifacts."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.db.database import execute, fetch, fetchrow, get_pool
from velox.models.admin_debug import (
    DebugArtifactResponse,
    DebugArtifactType,
    DebugFindingCategory,
    DebugFindingResponse,
    DebugFindingSeverity,
    DebugRunListItem,
    DebugRunMode,
    DebugRunResponse,
    DebugRunScope,
    DebugRunStatus,
    DebugRunSummary,
)
from velox.utils.json import decode_json_object, decode_json_value

logger = structlog.get_logger(__name__)


def _json_dumps(payload: Any) -> str:
    return orjson.dumps(payload).decode()


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _coerce_summary(raw: Any, finding_count: int = 0) -> DebugRunSummary:
    payload = decode_json_object(raw)
    if finding_count and not payload.get("finding_count"):
        payload["finding_count"] = finding_count
    return DebugRunSummary.model_validate(payload or {"finding_count": finding_count})


def _row_to_run_list_item(row: asyncpg.Record) -> DebugRunListItem:
    finding_count = int(row.get("finding_count") or 0)
    return DebugRunListItem(
        id=str(row["id"]),
        hotel_id=int(row["hotel_id"]),
        triggered_by_user_id=int(row["triggered_by_user_id"]),
        retry_of_run_id=str(row["retry_of_run_id"]) if row.get("retry_of_run_id") else None,
        mode=DebugRunMode(str(row["mode"])),
        status=DebugRunStatus(str(row["status"])),
        scope=DebugRunScope.model_validate(decode_json_object(row.get("scope_json"))),
        summary=_coerce_summary(row.get("summary_json"), finding_count=finding_count),
        finding_count=finding_count,
        queued_at=_iso(row.get("queued_at")) or "",
        started_at=_iso(row.get("started_at")),
        finished_at=_iso(row.get("finished_at")),
        last_heartbeat_at=_iso(row.get("last_heartbeat_at")),
        cancel_requested_at=_iso(row.get("cancel_requested_at")),
        failure_reason=str(row["failure_reason"]) if row.get("failure_reason") else None,
    )


def _row_to_run_response(row: asyncpg.Record) -> DebugRunResponse:
    base = _row_to_run_list_item(row)
    return DebugRunResponse(
        **base.model_dump(),
        artifact_count=int(row.get("artifact_count") or 0),
        worker_meta=decode_json_object(row.get("worker_meta_json")),
    )


def _row_to_finding(row: asyncpg.Record) -> DebugFindingResponse:
    steps = decode_json_value(row.get("steps_json"))
    return DebugFindingResponse(
        id=str(row["id"]),
        run_id=str(row["run_id"]),
        hotel_id=int(row["hotel_id"]),
        category=DebugFindingCategory(str(row["category"])),
        severity=DebugFindingSeverity(str(row["severity"])),
        screen=str(row["screen"]),
        action_label=str(row["action_label"]) if row.get("action_label") else None,
        description=str(row["description"]),
        steps=[str(item) for item in steps] if isinstance(steps, list) else [],
        technical_cause=str(row["technical_cause"]) if row.get("technical_cause") else None,
        suggested_fix=str(row["suggested_fix"]) if row.get("suggested_fix") else None,
        fingerprint=str(row["fingerprint"]),
        evidence=decode_json_object(row.get("evidence_json")),
        created_at=_iso(row.get("created_at")) or "",
    )


def _row_to_artifact(row: asyncpg.Record) -> DebugArtifactResponse:
    return DebugArtifactResponse(
        id=str(row["id"]),
        run_id=str(row["run_id"]),
        finding_id=str(row["finding_id"]) if row.get("finding_id") else None,
        artifact_type=DebugArtifactType(str(row["artifact_type"])),
        storage_path=str(row["storage_path"]),
        mime_type=str(row["mime_type"]),
        metadata=decode_json_object(row.get("metadata_json")),
        created_at=_iso(row.get("created_at")) or "",
    )


class AdminDebugRepository:
    """CRUD and lifecycle helpers for admin debug runs."""

    async def create_run(
        self,
        *,
        hotel_id: int,
        triggered_by_user_id: int,
        mode: DebugRunMode,
        scope: DebugRunScope,
        retry_of_run_id: UUID | None = None,
    ) -> DebugRunResponse:
        row = await fetchrow(
            """
            INSERT INTO admin_debug_runs (
                hotel_id,
                triggered_by_user_id,
                retry_of_run_id,
                mode,
                scope_json,
                summary_json,
                worker_meta_json
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, '{}'::jsonb, '{}'::jsonb)
            RETURNING id
            """,
            hotel_id,
            triggered_by_user_id,
            retry_of_run_id,
            mode.value,
            _json_dumps(scope.model_dump(mode="json")),
        )
        if row is None:
            raise RuntimeError("Failed to create admin debug run.")
        result = await self.get_run(run_id=UUID(str(row["id"])), hotel_id=hotel_id)
        if result is None:
            raise RuntimeError("Created admin debug run could not be reloaded.")
        return result

    async def get_run(self, *, run_id: UUID, hotel_id: int) -> DebugRunResponse | None:
        row = await fetchrow(
            """
            SELECT
                r.*,
                COALESCE((SELECT COUNT(*) FROM admin_debug_findings f WHERE f.run_id = r.id), 0) AS finding_count,
                COALESCE((SELECT COUNT(*) FROM admin_debug_artifacts a WHERE a.run_id = r.id), 0) AS artifact_count
            FROM admin_debug_runs r
            WHERE r.id = $1
              AND r.hotel_id = $2
            """,
            run_id,
            hotel_id,
        )
        if row is None:
            return None
        return _row_to_run_response(row)

    async def list_runs(
        self,
        *,
        hotel_id: int,
        status: DebugRunStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[DebugRunListItem]:
        rows = await fetch(
            """
            SELECT
                r.*,
                COALESCE((SELECT COUNT(*) FROM admin_debug_findings f WHERE f.run_id = r.id), 0) AS finding_count
            FROM admin_debug_runs r
            WHERE r.hotel_id = $1
              AND ($2::text IS NULL OR r.status = $2)
            ORDER BY r.queued_at DESC
            LIMIT $3 OFFSET $4
            """,
            hotel_id,
            status.value if status else None,
            limit,
            offset,
        )
        return [_row_to_run_list_item(row) for row in rows]

    async def claim_next_queued_run(self, *, hotel_id: int | None = None) -> DebugRunResponse | None:
        pool = get_pool()
        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                WITH next_run AS (
                    SELECT id
                    FROM admin_debug_runs
                    WHERE status = 'queued'
                      AND cancel_requested_at IS NULL
                      AND ($1::int IS NULL OR hotel_id = $1)
                    ORDER BY queued_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE admin_debug_runs AS run
                SET status = 'running',
                    started_at = COALESCE(run.started_at, now()),
                    last_heartbeat_at = now()
                FROM next_run
                WHERE run.id = next_run.id
                RETURNING run.*
                """,
                hotel_id,
            )
        if row is None:
            return None
        result = await self.get_run(run_id=UUID(str(row["id"])), hotel_id=int(row["hotel_id"]))
        if result is None:
            logger.warning("admin_debug_claimed_run_missing_after_update", run_id=str(row["id"]))
        return result

    async def mark_running(
        self,
        *,
        run_id: UUID,
        hotel_id: int,
        worker_meta_json: dict[str, Any] | None = None,
    ) -> DebugRunResponse | None:
        row = await fetchrow(
            """
            UPDATE admin_debug_runs
            SET status = 'running',
                started_at = COALESCE(started_at, now()),
                last_heartbeat_at = now(),
                worker_meta_json = COALESCE($3::jsonb, worker_meta_json)
            WHERE id = $1
              AND hotel_id = $2
              AND status = 'queued'
            RETURNING id
            """,
            run_id,
            hotel_id,
            _json_dumps(worker_meta_json or {}),
        )
        if row is None:
            return None
        return await self.get_run(run_id=run_id, hotel_id=hotel_id)

    async def mark_completed(
        self,
        *,
        run_id: UUID,
        hotel_id: int,
        summary_json: dict[str, Any],
    ) -> DebugRunResponse | None:
        row = await fetchrow(
            """
            UPDATE admin_debug_runs
            SET status = 'completed',
                summary_json = $3::jsonb,
                finished_at = now(),
                last_heartbeat_at = now(),
                failure_reason = NULL
            WHERE id = $1
              AND hotel_id = $2
              AND status = 'running'
            RETURNING id
            """,
            run_id,
            hotel_id,
            _json_dumps(summary_json),
        )
        if row is None:
            return None
        return await self.get_run(run_id=run_id, hotel_id=hotel_id)

    async def mark_failed(
        self,
        *,
        run_id: UUID,
        hotel_id: int,
        failure_reason: str,
    ) -> DebugRunResponse | None:
        row = await fetchrow(
            """
            UPDATE admin_debug_runs
            SET status = 'failed',
                failure_reason = $3,
                finished_at = now(),
                last_heartbeat_at = now()
            WHERE id = $1
              AND hotel_id = $2
              AND status IN ('queued', 'running')
            RETURNING id
            """,
            run_id,
            hotel_id,
            failure_reason.strip(),
        )
        if row is None:
            return None
        return await self.get_run(run_id=run_id, hotel_id=hotel_id)

    async def request_cancel(self, *, run_id: UUID, hotel_id: int) -> DebugRunResponse | None:
        row = await fetchrow(
            """
            UPDATE admin_debug_runs
            SET status = CASE WHEN status = 'queued' THEN 'cancelled' ELSE status END,
                finished_at = CASE WHEN status = 'queued' THEN now() ELSE finished_at END,
                cancel_requested_at = CASE
                    WHEN status = 'running' THEN now()
                    ELSE cancel_requested_at
                END
            WHERE id = $1
              AND hotel_id = $2
              AND status IN ('queued', 'running')
            RETURNING id
            """,
            run_id,
            hotel_id,
        )
        if row is None:
            return None
        return await self.get_run(run_id=run_id, hotel_id=hotel_id)

    async def mark_cancelled(
        self,
        *,
        run_id: UUID,
        hotel_id: int,
        summary_json: dict[str, Any] | None = None,
    ) -> DebugRunResponse | None:
        row = await fetchrow(
            """
            UPDATE admin_debug_runs
            SET status = 'cancelled',
                finished_at = now(),
                last_heartbeat_at = now(),
                summary_json = CASE WHEN $3::jsonb IS NULL THEN summary_json ELSE $3::jsonb END
            WHERE id = $1
              AND hotel_id = $2
              AND status = 'running'
            RETURNING id
            """,
            run_id,
            hotel_id,
            _json_dumps(summary_json) if summary_json is not None else None,
        )
        if row is None:
            return None
        return await self.get_run(run_id=run_id, hotel_id=hotel_id)

    async def touch_heartbeat(self, *, run_id: UUID, hotel_id: int) -> None:
        await execute(
            """
            UPDATE admin_debug_runs
            SET last_heartbeat_at = now()
            WHERE id = $1
              AND hotel_id = $2
              AND status = 'running'
            """,
            run_id,
            hotel_id,
        )

    async def append_finding(
        self,
        *,
        run_id: UUID,
        hotel_id: int,
        category: DebugFindingCategory,
        severity: DebugFindingSeverity,
        screen: str,
        description: str,
        action_label: str | None = None,
        steps: list[str] | None = None,
        technical_cause: str | None = None,
        suggested_fix: str | None = None,
        fingerprint: str,
        evidence: dict[str, Any] | None = None,
    ) -> DebugFindingResponse:
        row = await fetchrow(
            """
            INSERT INTO admin_debug_findings (
                run_id,
                hotel_id,
                category,
                severity,
                screen,
                action_label,
                description,
                steps_json,
                technical_cause,
                suggested_fix,
                fingerprint,
                evidence_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12::jsonb)
            RETURNING *
            """,
            run_id,
            hotel_id,
            category.value,
            severity.value,
            screen.strip(),
            action_label.strip() if action_label else None,
            description.strip(),
            _json_dumps(steps or []),
            technical_cause.strip() if technical_cause else None,
            suggested_fix.strip() if suggested_fix else None,
            fingerprint.strip(),
            _json_dumps(evidence or {}),
        )
        if row is None:
            raise RuntimeError("Failed to append admin debug finding.")
        return _row_to_finding(row)

    async def append_artifact(
        self,
        *,
        run_id: UUID,
        artifact_type: DebugArtifactType,
        storage_path: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
        finding_id: UUID | None = None,
    ) -> DebugArtifactResponse:
        row = await fetchrow(
            """
            INSERT INTO admin_debug_artifacts (
                run_id,
                finding_id,
                artifact_type,
                storage_path,
                mime_type,
                metadata_json
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING *
            """,
            run_id,
            finding_id,
            artifact_type.value,
            storage_path.strip(),
            mime_type.strip(),
            _json_dumps(metadata or {}),
        )
        if row is None:
            raise RuntimeError("Failed to append admin debug artifact.")
        return _row_to_artifact(row)

    async def list_findings(
        self,
        *,
        run_id: UUID,
        hotel_id: int,
        severity: DebugFindingSeverity | None = None,
        category: DebugFindingCategory | None = None,
        screen: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DebugFindingResponse]:
        rows = await fetch(
            """
            SELECT finding.*
            FROM admin_debug_findings AS finding
            JOIN admin_debug_runs AS run
              ON run.id = finding.run_id
            WHERE finding.run_id = $1
              AND finding.hotel_id = $2
              AND run.hotel_id = $2
              AND ($3::text IS NULL OR finding.severity = $3)
              AND ($4::text IS NULL OR finding.category = $4)
              AND ($5::text IS NULL OR finding.screen ILIKE $5)
            ORDER BY finding.created_at DESC
            LIMIT $6 OFFSET $7
            """,
            run_id,
            hotel_id,
            severity.value if severity else None,
            category.value if category else None,
            f"%{screen.strip()}%" if screen else None,
            limit,
            offset,
        )
        return [_row_to_finding(row) for row in rows]

    async def list_artifacts_for_run(self, *, run_id: UUID, hotel_id: int) -> list[DebugArtifactResponse]:
        rows = await fetch(
            """
            SELECT artifact.*
            FROM admin_debug_artifacts AS artifact
            JOIN admin_debug_runs AS run
              ON run.id = artifact.run_id
            WHERE artifact.run_id = $1
              AND run.hotel_id = $2
            ORDER BY artifact.created_at DESC
            """,
            run_id,
            hotel_id,
        )
        return [_row_to_artifact(row) for row in rows]
