BEGIN;

CREATE TABLE IF NOT EXISTS whatsapp_integrations (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    business_id VARCHAR(64),
    waba_id VARCHAR(64),
    phone_number_id VARCHAR(64) NOT NULL,
    display_phone_number VARCHAR(32),
    verified_name VARCHAR(255),
    quality_rating VARCHAR(32),
    messaging_limit VARCHAR(64),
    token_ciphertext TEXT,
    token_last4 VARCHAR(8),
    token_expires_at TIMESTAMPTZ,
    token_scopes_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    webhook_verify_token_ciphertext TEXT,
    webhook_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
    connection_status VARCHAR(32) NOT NULL DEFAULT 'draft',
    last_health_check_at TIMESTAMPTZ,
    last_error_code VARCHAR(128),
    last_error_message TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by_admin_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    rotated_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT chk_whatsapp_integrations_connection_status CHECK (
        connection_status IN (
            'draft',
            'oauth_pending',
            'assets_pending',
            'webhook_pending',
            'active',
            'degraded',
            'revoked',
            'error'
        )
    ),
    CONSTRAINT chk_whatsapp_integrations_webhook_status CHECK (
        webhook_status IN ('unknown', 'pending', 'verified', 'failed')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_integrations_hotel_active
    ON whatsapp_integrations(hotel_id)
    WHERE is_active = true;

CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_integrations_phone_active
    ON whatsapp_integrations(phone_number_id)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_whatsapp_integrations_hotel_status
    ON whatsapp_integrations(hotel_id, connection_status);

CREATE TABLE IF NOT EXISTS whatsapp_connect_sessions (
    id UUID PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    state_token VARCHAR(128) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL DEFAULT 'created',
    token_ciphertext TEXT,
    token_last4 VARCHAR(8),
    selected_business_id VARCHAR(64),
    selected_waba_id VARCHAR(64),
    selected_phone_number_id VARCHAR(64),
    error_code VARCHAR(128),
    error_message TEXT,
    created_by_admin_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT chk_whatsapp_connect_sessions_status CHECK (
        status IN (
            'created',
            'oauth_opened',
            'authorized',
            'assets_selected',
            'completed',
            'expired',
            'cancelled',
            'error'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_connect_sessions_hotel_created
    ON whatsapp_connect_sessions(hotel_id, created_at DESC);

CREATE TABLE IF NOT EXISTS whatsapp_templates (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    waba_id VARCHAR(64) NOT NULL,
    meta_template_id VARCHAR(128),
    name VARCHAR(255) NOT NULL,
    language VARCHAR(32) NOT NULL,
    category VARCHAR(64),
    status VARCHAR(64) NOT NULL DEFAULT 'UNKNOWN',
    components_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    rejection_reason TEXT,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_templates_unique
    ON whatsapp_templates(hotel_id, waba_id, name, language);

CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_status
    ON whatsapp_templates(hotel_id, status);

CREATE TABLE IF NOT EXISTS whatsapp_connection_events (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    integration_id BIGINT REFERENCES whatsapp_integrations(id) ON DELETE SET NULL,
    connect_session_id UUID REFERENCES whatsapp_connect_sessions(id) ON DELETE SET NULL,
    actor_admin_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    safe_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_connection_events_hotel_created
    ON whatsapp_connection_events(hotel_id, created_at DESC);

COMMIT;
