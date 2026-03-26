-- Chat Lab attachment storage for image/document/audio message composer

CREATE TABLE IF NOT EXISTS chat_lab_assets (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id            INTEGER NOT NULL REFERENCES hotels(hotel_id),
    kind                VARCHAR(16) NOT NULL,
    mime_type           VARCHAR(128) NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    storage_path        TEXT NOT NULL,
    size_bytes          INTEGER NOT NULL CHECK (size_bytes > 0),
    sha256              VARCHAR(64) NOT NULL,
    status              VARCHAR(16) NOT NULL DEFAULT 'uploaded',
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    attached_at         TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ,
    attached_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_chat_lab_assets_hotel_status
    ON chat_lab_assets (hotel_id, status, uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_lab_assets_expires
    ON chat_lab_assets (expires_at)
    WHERE status = 'uploaded' AND expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_chat_lab_assets_kind'
    ) THEN
        ALTER TABLE chat_lab_assets
            ADD CONSTRAINT chk_chat_lab_assets_kind
            CHECK (kind IN ('image', 'document', 'audio'));
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_chat_lab_assets_status'
    ) THEN
        ALTER TABLE chat_lab_assets
            ADD CONSTRAINT chk_chat_lab_assets_status
            CHECK (status IN ('uploaded', 'attached', 'deleted', 'expired', 'failed'));
    END IF;
END$$;
