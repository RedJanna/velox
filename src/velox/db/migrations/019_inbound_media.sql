-- Inbound WhatsApp media analysis records

CREATE TABLE IF NOT EXISTS inbound_media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    conversation_id UUID REFERENCES conversations(id),
    whatsapp_message_id VARCHAR(128) NOT NULL,
    whatsapp_media_id VARCHAR(128) NOT NULL,
    media_type VARCHAR(32) NOT NULL,
    mime_type VARCHAR(128) NOT NULL DEFAULT '',
    caption TEXT,
    file_size_bytes INTEGER,
    sha256 VARCHAR(64),
    storage_path TEXT,
    analysis_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    analysis_model VARCHAR(64),
    analysis_confidence NUMERIC(5,4),
    analysis_json JSONB NOT NULL DEFAULT '{}',
    risk_flags TEXT[] NOT NULL DEFAULT '{}',
    error_type VARCHAR(64),
    error_detail TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_inbound_media_wa_unique
    ON inbound_media (whatsapp_message_id, whatsapp_media_id);

CREATE INDEX IF NOT EXISTS idx_inbound_media_conversation_created
    ON inbound_media (conversation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_inbound_media_status_created
    ON inbound_media (analysis_status, created_at DESC);
