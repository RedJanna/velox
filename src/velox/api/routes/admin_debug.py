"""Admin debug run API routes."""

from __future__ import annotations

from asyncio import Task
from typing import Annotated, Any
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from velox.api.middleware.auth import TokenData, require_role
from velox.config.constants import Role
from velox.db.repositories.admin_debug import AdminDebugRepository
from velox.models.admin_debug import (
    DebugFindingCategory,
    DebugFindingListResponse,
    DebugFindingSeverity,
    DebugRunActionResponse,
    DebugRunCreateRequest,
    DebugRunListResponse,
    DebugRunResponse,
    DebugRunStatus,
    DebugWorkerStatusResponse,
)

router = APIRouter(prefix="/admin/debug", tags=["admin-debug"])


def _repository() -> AdminDebugRepository:
    return AdminDebugRepository()


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug run not found.")


@router.post("/runs", response_model=DebugRunResponse)
async def create_debug_run(
    payload: DebugRunCreateRequest,
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
) -> DebugRunResponse:
    """Create one report-only debug run for the current hotel scope."""
    try:
        return await repository.create_run(
            hotel_id=current_user.hotel_id,
            triggered_by_user_id=current_user.user_id,
            mode=payload.mode,
            scope=payload.scope,
        )
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu otel için zaten aktif bir hata taraması var.",
        ) from exc


@router.get("/runs", response_model=DebugRunListResponse)
async def list_debug_runs(
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
    status_filter: Annotated[DebugRunStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DebugRunListResponse:
    """List debug runs for the current hotel."""
    items = await repository.list_runs(
        hotel_id=current_user.hotel_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return DebugRunListResponse(items=items)


@router.get("/status", response_model=DebugWorkerStatusResponse)
async def debug_worker_status(
    request: Request,
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
) -> DebugWorkerStatusResponse:
    """Expose worker readiness and active-run state for the current hotel."""
    _ = current_user
    task: Task[Any] | None = getattr(request.app.state, "debug_runner_task", None)
    runs = await repository.list_runs(
        hotel_id=current_user.hotel_id,
        limit=5,
        offset=0,
    )
    active_run = next((item for item in runs if item.status in {DebugRunStatus.QUEUED, DebugRunStatus.RUNNING}), None)
    worker_ready = bool(task is not None and not task.done())
    if not worker_ready:
        message = "Debug worker hazır değil."
    elif active_run is not None:
        message = "Aktif hata taraması sürüyor."
    else:
        message = "Debug worker hazır."
    return DebugWorkerStatusResponse(
        worker_ready=worker_ready,
        active_run_id=active_run.id if active_run else None,
        active_run_status=active_run.status if active_run else None,
        active_run_message=message,
    )


@router.get("/runs/{run_id}", response_model=DebugRunResponse)
async def get_debug_run(
    run_id: UUID,
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
) -> DebugRunResponse:
    """Return one debug run detail for the current hotel."""
    run = await repository.get_run(run_id=run_id, hotel_id=current_user.hotel_id)
    if run is None:
        raise _not_found()
    return run


@router.get("/runs/{run_id}/findings", response_model=DebugFindingListResponse)
async def list_debug_findings(
    run_id: UUID,
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
    severity: Annotated[DebugFindingSeverity | None, Query()] = None,
    category: Annotated[DebugFindingCategory | None, Query()] = None,
    screen: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DebugFindingListResponse:
    """List findings for one debug run."""
    run = await repository.get_run(run_id=run_id, hotel_id=current_user.hotel_id)
    if run is None:
        raise _not_found()
    items = await repository.list_findings(
        run_id=run_id,
        hotel_id=current_user.hotel_id,
        severity=severity,
        category=category,
        screen=screen,
        limit=limit,
        offset=offset,
    )
    return DebugFindingListResponse(items=items)


@router.post("/runs/{run_id}/cancel", response_model=DebugRunActionResponse)
async def cancel_debug_run(
    run_id: UUID,
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
) -> DebugRunActionResponse:
    """Cancel one queued or running debug run."""
    run = await repository.request_cancel(run_id=run_id, hotel_id=current_user.hotel_id)
    if run is None:
        raise _not_found()
    if run.status == DebugRunStatus.CANCELLED:
        message = "Debug taraması iptal edildi."
    else:
        message = "Debug taraması için iptal isteği kaydedildi."
    return DebugRunActionResponse(run=run, message=message)


@router.post("/runs/{run_id}/retry", response_model=DebugRunActionResponse)
async def retry_debug_run(
    run_id: UUID,
    current_user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    repository: Annotated[AdminDebugRepository, Depends(_repository)],
) -> DebugRunActionResponse:
    """Create a new debug run using the scope of a previous run."""
    source_run = await repository.get_run(run_id=run_id, hotel_id=current_user.hotel_id)
    if source_run is None:
        raise _not_found()
    try:
        run = await repository.create_run(
            hotel_id=current_user.hotel_id,
            triggered_by_user_id=current_user.user_id,
            mode=source_run.mode,
            scope=source_run.scope,
            retry_of_run_id=run_id,
        )
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu otel için zaten aktif bir hata taraması var.",
        ) from exc
    return DebugRunActionResponse(run=run, message="Debug taraması yeniden kuyruğa alındı.")
