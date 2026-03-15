BEGIN;

CREATE TABLE IF NOT EXISTS whatsapp_numbers (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    phone_number_id VARCHAR(64) NOT NULL UNIQUE,
    display_phone_number VARCHAR(32),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_numbers_hotel_active
    ON whatsapp_numbers(hotel_id, is_active);

CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_numbers_display_phone_unique
    ON whatsapp_numbers(display_phone_number)
    WHERE display_phone_number IS NOT NULL;

COMMIT;
