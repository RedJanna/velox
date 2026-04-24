-- 027: Admin debug run storage for report-only aggressive scan orchestration.

CREATE TABLE IF NOT EXISTS admin_debug_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    triggered_by_user_id INTEGER NOT NULL REFERENCES admin_users(id),
    retry_of_run_id UUID REFERENCES admin_debug_runs(id) ON DELETE SET NULL,
    mode VARCHAR(32) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'queued',
    scope_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    worker_meta_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    last_heartbeat_at TIMESTAMPTZ,
    cancel_requested_at TIMESTAMPTZ,
    failure_reason TEXT
);

CREATE TABLE IF NOT EXISTS admin_debug_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES admin_debug_runs(id) ON DELETE CASCADE,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    category VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    screen VARCHAR(120) NOT NULL,
    action_label VARCHAR(160),
    description TEXT NOT NULL,
    steps_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    technical_cause TEXT,
    suggested_fix TEXT,
    fingerprint VARCHAR(64) NOT NULL,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admin_debug_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES admin_debug_runs(id) ON DELETE CASCADE,
    finding_id UUID REFERENCES admin_debug_findings(id) ON DELETE CASCADE,
    artifact_type VARCHAR(24) NOT NULL,
    storage_path TEXT NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_debug_runs_hotel_queued
    ON admin_debug_runs (hotel_id, queued_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_debug_runs_status_queued
    ON admin_debug_runs (status, queued_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_debug_runs_one_active_per_hotel
    ON admin_debug_runs (hotel_id)
    WHERE status IN ('queued', 'running');

CREATE INDEX IF NOT EXISTS idx_admin_debug_findings_run_severity
    ON admin_debug_findings (run_id, severity);

CREATE INDEX IF NOT EXISTS idx_admin_debug_findings_run_category
    ON admin_debug_findings (run_id, category);

CREATE INDEX IF NOT EXISTS idx_admin_debug_findings_fingerprint
    ON admin_debug_findings (fingerprint);

CREATE INDEX IF NOT EXISTS idx_admin_debug_artifacts_run_created
    ON admin_debug_artifacts (run_id, created_at DESC);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_admin_debug_runs_mode'
    ) THEN
        ALTER TABLE admin_debug_runs
            ADD CONSTRAINT chk_admin_debug_runs_mode
            CHECK (mode IN ('aggressive_report_only'));
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_admin_debug_runs_status'
    ) THEN
        ALTER TABLE admin_debug_runs
            ADD CONSTRAINT chk_admin_debug_runs_status
            CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled'));
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_admin_debug_findings_category'
    ) THEN
        ALTER TABLE admin_debug_findings
            ADD CONSTRAINT chk_admin_debug_findings_category
            CHECK (
                category IN (
                    'javascript_error',
                    'console_warning',
                    'network_failure',
                    'broken_interaction',
                    'ui_overlap',
                    'popup_issue',
                    'iframe_issue',
                    'routing_issue',
                    'performance_issue',
                    'auth_session_issue',
                    'accessibility_issue'
                )
            );
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_admin_debug_findings_severity'
    ) THEN
        ALTER TABLE admin_debug_findings
            ADD CONSTRAINT chk_admin_debug_findings_severity
            CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info'));
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_admin_debug_artifacts_type'
    ) THEN
        ALTER TABLE admin_debug_artifacts
            ADD CONSTRAINT chk_admin_debug_artifacts_type
            CHECK (artifact_type IN ('screenshot', 'console_log', 'network_log', 'dom_snapshot', 'trace'));
    END IF;
END$$;
