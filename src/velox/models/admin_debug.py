"""Pydantic models for admin debug run orchestration and reporting."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class DebugRunMode(StrEnum):
    """Supported admin debug run modes."""

    AGGRESSIVE_REPORT_ONLY = "aggressive_report_only"


class DebugRunStatus(StrEnum):
    """Lifecycle states for one debug run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DebugFindingSeverity(StrEnum):
    """Severity levels persisted for detected findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DebugFindingCategory(StrEnum):
    """Supported finding categories."""

    JAVASCRIPT_ERROR = "javascript_error"
    CONSOLE_WARNING = "console_warning"
    NETWORK_FAILURE = "network_failure"
    BROKEN_INTERACTION = "broken_interaction"
    UI_OVERLAP = "ui_overlap"
    POPUP_ISSUE = "popup_issue"
    IFRAME_ISSUE = "iframe_issue"
    ROUTING_ISSUE = "routing_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    AUTH_SESSION_ISSUE = "auth_session_issue"
    ACCESSIBILITY_ISSUE = "accessibility_issue"


class DebugArtifactType(StrEnum):
    """Artifact types stored for one run/finding."""

    SCREENSHOT = "screenshot"
    CONSOLE_LOG = "console_log"
    NETWORK_LOG = "network_log"
    DOM_SNAPSHOT = "dom_snapshot"
    TRACE = "trace"


class DebugRunScope(BaseModel):
    """Requested scope for one report-only debug run."""

    target: Literal["current_view", "all_panel"] = "all_panel"
    target_view: str | None = Field(default=None, min_length=1, max_length=80)
    include_chatlab_iframe: bool = True
    include_popups: bool = True
    include_modals: bool = True
    scan_intensity: Literal["aggressive"] = "aggressive"
    report_only: bool = True

    @model_validator(mode="after")
    def validate_scope(self) -> DebugRunScope:
        """Normalize target scope and keep report-only mode locked."""
        if self.target == "current_view" and not self.target_view:
            raise ValueError("target_view is required when target is current_view.")
        if self.target == "all_panel":
            self.target_view = None
        self.report_only = True
        return self


class DebugRunSummary(BaseModel):
    """Aggregated counters for one debug run."""

    finding_count: int = Field(default=0, ge=0)
    critical_count: int = Field(default=0, ge=0)
    high_count: int = Field(default=0, ge=0)
    medium_count: int = Field(default=0, ge=0)
    low_count: int = Field(default=0, ge=0)
    info_count: int = Field(default=0, ge=0)
    screens_scanned: int = Field(default=0, ge=0)
    iframes_scanned: int = Field(default=0, ge=0)
    popups_scanned: int = Field(default=0, ge=0)
    blocked_mutation_attempts: int = Field(default=0, ge=0)
    duration_seconds: int = Field(default=0, ge=0)


class DebugRunCreateRequest(BaseModel):
    """API payload for creating one admin debug run."""

    mode: DebugRunMode = DebugRunMode.AGGRESSIVE_REPORT_ONLY
    scope: DebugRunScope = Field(default_factory=DebugRunScope)


class DebugRunListItem(BaseModel):
    """Compact run item for list screens."""

    id: str
    hotel_id: int
    triggered_by_user_id: int
    retry_of_run_id: str | None = None
    mode: DebugRunMode
    status: DebugRunStatus
    scope: DebugRunScope
    summary: DebugRunSummary
    finding_count: int = Field(default=0, ge=0)
    queued_at: str
    started_at: str | None = None
    finished_at: str | None = None
    last_heartbeat_at: str | None = None
    cancel_requested_at: str | None = None
    failure_reason: str | None = None


class DebugRunResponse(DebugRunListItem):
    """Detailed debug run response."""

    artifact_count: int = Field(default=0, ge=0)
    worker_meta: dict[str, Any] = Field(default_factory=dict)


class DebugRunListResponse(BaseModel):
    """Pageless debug run list response."""

    items: list[DebugRunListItem] = Field(default_factory=list)


class DebugRunActionResponse(BaseModel):
    """Response for cancel and retry endpoints."""

    run: DebugRunResponse
    message: str


class DebugWorkerStatusResponse(BaseModel):
    """Worker readiness and active-run state for the admin panel."""

    worker_ready: bool
    browser_scan_available: bool = False
    browser_scan_mode: str = "public"
    browser_scan_target: str | None = None
    browser_scan_reason: str | None = None
    active_run_id: str | None = None
    active_run_status: DebugRunStatus | None = None
    active_run_message: str | None = None


class DebugFindingResponse(BaseModel):
    """One persisted finding shown in the admin panel."""

    id: str
    run_id: str
    hotel_id: int
    category: DebugFindingCategory
    severity: DebugFindingSeverity
    screen: str
    action_label: str | None = None
    description: str
    steps: list[str] = Field(default_factory=list)
    technical_cause: str | None = None
    suggested_fix: str | None = None
    fingerprint: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class DebugArtifactResponse(BaseModel):
    """Artifact metadata persisted for one run/finding."""

    id: str
    run_id: str
    finding_id: str | None = None
    artifact_type: DebugArtifactType
    storage_path: str
    mime_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    content_url: str | None = None


class DebugArtifactListResponse(BaseModel):
    """Pageless artifact list response."""

    items: list[DebugArtifactResponse] = Field(default_factory=list)


class DebugFindingListResponse(BaseModel):
    """Pageless finding list response."""

    items: list[DebugFindingResponse] = Field(default_factory=list)
