BEGIN;

-- Canonical workflow states beyond legacy APPROVED/CONFIRMED flow.
ALTER TABLE stay_holds
    ADD COLUMN IF NOT EXISTS workflow_state VARCHAR(30) NOT NULL DEFAULT 'PENDING_APPROVAL',
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS pms_create_started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS pms_create_completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS manual_review_reason TEXT,
    ADD COLUMN IF NOT EXISTS approval_idempotency_key VARCHAR(100),
    ADD COLUMN IF NOT EXISTS create_idempotency_key VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_stay_holds_workflow_state
    ON stay_holds(hotel_id, workflow_state);

CREATE INDEX IF NOT EXISTS idx_stay_holds_expires_at
    ON stay_holds(expires_at)
    WHERE workflow_state = 'PENDING_APPROVAL';

CREATE UNIQUE INDEX IF NOT EXISTS uq_stay_holds_approval_idem
    ON stay_holds(hotel_id, approval_idempotency_key)
    WHERE approval_idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_stay_holds_create_idem
    ON stay_holds(hotel_id, create_idempotency_key)
    WHERE create_idempotency_key IS NOT NULL;

COMMIT;

