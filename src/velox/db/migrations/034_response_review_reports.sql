-- 034: Message-level response review queue for Operations Desk reporting.

CREATE TABLE IF NOT EXISTS response_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    message_role VARCHAR(16) NOT NULL,
    message_content TEXT NOT NULL,
    message_created_at TIMESTAMPTZ NOT NULL,
    conversation_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    context_messages_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    report_reason TEXT NOT NULL DEFAULT '',
    error_type VARCHAR(80) NOT NULL DEFAULT 'not_classified',
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    classification VARCHAR(30) NOT NULL DEFAULT 'needs_review',
    reported_by_user_id INTEGER,
    reported_by_username VARCHAR(120) NOT NULL DEFAULT '',
    reported_by_display_name VARCHAR(160),
    reported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_by_user_id INTEGER,
    reviewed_by_username VARCHAR(120),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    gold_standard TEXT,
    rating INTEGER,
    included_in_report BOOLEAN NOT NULL DEFAULT false,
    feedback_id VARCHAR(80),
    feedback_storage_group VARCHAR(40),
    feedback_storage_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_response_reviews_role
        CHECK (message_role IN ('assistant', 'operator', 'system')),
    CONSTRAINT chk_response_reviews_status
        CHECK (status IN ('open', 'in_review', 'finalized', 'closed')),
    CONSTRAINT chk_response_reviews_classification
        CHECK (classification IN ('needs_review', 'correct', 'incorrect', 'needs_revision')),
    CONSTRAINT chk_response_reviews_rating
        CHECK (rating IS NULL OR rating BETWEEN 1 AND 5)
);

CREATE INDEX IF NOT EXISTS idx_response_reviews_hotel_status
ON response_reviews(hotel_id, status, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_response_reviews_conversation
ON response_reviews(conversation_id, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_response_reviews_message
ON response_reviews(message_id, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_response_reviews_reporter_open
ON response_reviews(hotel_id, message_id, reported_by_user_id, status);

CREATE TABLE IF NOT EXISTS response_review_actions (
    id BIGSERIAL PRIMARY KEY,
    review_id UUID NOT NULL REFERENCES response_reviews(id) ON DELETE CASCADE,
    actor_user_id INTEGER,
    actor_username VARCHAR(120) NOT NULL DEFAULT '',
    action_type VARCHAR(60) NOT NULL,
    from_status VARCHAR(30),
    to_status VARCHAR(30),
    notes TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_response_review_actions_review
ON response_review_actions(review_id, created_at DESC);
