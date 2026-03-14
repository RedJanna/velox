-- Migration 004: Notification phones for admin WhatsApp alerts
-- Admin approval oluştuğunda WhatsApp bildirimi gönderilecek telefon numaralarını yönetir.

CREATE TABLE IF NOT EXISTS notification_phones (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id    INTEGER NOT NULL REFERENCES hotels(hotel_id),
    phone       TEXT    NOT NULL,
    label       TEXT    NOT NULL DEFAULT '',
    is_default  BOOLEAN NOT NULL DEFAULT FALSE,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (hotel_id, phone)
);

CREATE INDEX idx_notification_phones_hotel_active
    ON notification_phones (hotel_id) WHERE active = TRUE;

-- Varsayılan ve zorunlu admin numarası
INSERT INTO notification_phones (hotel_id, phone, label, is_default, active)
VALUES (21966, '+905304498453', 'Admin (varsayilan)', TRUE, TRUE)
ON CONFLICT (hotel_id, phone) DO NOTHING;
