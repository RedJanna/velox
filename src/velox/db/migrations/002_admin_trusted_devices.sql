-- Velox (NexlumeAI) — Admin trusted devices and remembered sessions

CREATE TABLE admin_trusted_devices (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id           INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    hotel_id                INTEGER NOT NULL REFERENCES hotels(hotel_id),
    selector                VARCHAR(32) UNIQUE NOT NULL,
    token_hash              VARCHAR(64) NOT NULL,
    device_label            VARCHAR(120) NOT NULL,
    verification_preset     VARCHAR(20) NOT NULL,
    session_preset          VARCHAR(20) NOT NULL,
    last_verified_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    verification_expires_at TIMESTAMPTZ NOT NULL,
    session_expires_at      TIMESTAMPTZ NOT NULL,
    last_seen_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_admin_trusted_devices_user_active
    ON admin_trusted_devices(admin_user_id, session_expires_at DESC)
    WHERE revoked_at IS NULL;

CREATE INDEX idx_admin_trusted_devices_selector_active
    ON admin_trusted_devices(selector)
    WHERE revoked_at IS NULL;
