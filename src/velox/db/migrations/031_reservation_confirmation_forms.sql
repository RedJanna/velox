-- 031: Reservation confirmation HTML forms and secure public delivery links.

CREATE TABLE IF NOT EXISTS reservation_confirmation_forms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    form_type VARCHAR(32) NOT NULL,
    reference_id VARCHAR(80),
    language VARCHAR(8) NOT NULL DEFAULT 'en',
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    token_prefix VARCHAR(12) NOT NULL,
    html_snapshot TEXT NOT NULL,
    whatsapp_message TEXT NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE',
    generated_by VARCHAR(80) NOT NULL DEFAULT 'system',
    sent_at TIMESTAMPTZ,
    whatsapp_message_id VARCHAR(160),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '30 days'),
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_confirmation_form_type
        CHECK (form_type IN ('accommodation', 'restaurant', 'transfer')),
    CONSTRAINT chk_confirmation_form_status
        CHECK (status IN ('ACTIVE', 'SENT', 'DELIVERY_FAILED', 'REVOKED', 'EXPIRED'))
);

CREATE INDEX IF NOT EXISTS idx_confirmation_forms_hotel_reference
ON reservation_confirmation_forms(hotel_id, form_type, reference_id);

CREATE INDEX IF NOT EXISTS idx_confirmation_forms_public_lookup
ON reservation_confirmation_forms(token_hash)
WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_confirmation_forms_expiry
ON reservation_confirmation_forms(expires_at)
WHERE revoked_at IS NULL;
