-- 032: Restaurant AI menu assistant admin catalog, waiter routing, order logs and settings.

CREATE TABLE IF NOT EXISTS restaurant_menu_catalog_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    version INTEGER NOT NULL,
    source_label VARCHAR(160) NOT NULL,
    checksum VARCHAR(96) NOT NULL,
    item_count INTEGER NOT NULL DEFAULT 0,
    imported_by VARCHAR(80) NOT NULL DEFAULT 'system',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (hotel_id, version)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_menu_catalog_versions_hotel
ON restaurant_menu_catalog_versions(hotel_id, version DESC);

CREATE TABLE IF NOT EXISTS restaurant_menu_catalog_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    menu_item_id VARCHAR(180) NOT NULL,
    venue VARCHAR(120) NOT NULL,
    menu_type VARCHAR(80) NOT NULL,
    category VARCHAR(120) NOT NULL,
    name_tr VARCHAR(180),
    name_en VARCHAR(180) NOT NULL,
    price_try NUMERIC(12, 2),
    description_tr TEXT,
    description_en TEXT,
    tags_json JSONB NOT NULL DEFAULT '[]',
    dietary_tags_json JSONB NOT NULL DEFAULT '[]',
    allergen_tags_json JSONB NOT NULL DEFAULT '[]',
    ingredients_json JSONB NOT NULL DEFAULT '[]',
    source_pdf VARCHAR(180),
    source_page INTEGER,
    status VARCHAR(24) NOT NULL DEFAULT 'active',
    manual_status VARCHAR(32) NOT NULL DEFAULT 'catalog_verified',
    notes TEXT,
    raw_json JSONB NOT NULL DEFAULT '{}',
    catalog_version INTEGER,
    created_by VARCHAR(80) NOT NULL DEFAULT 'system',
    updated_by VARCHAR(80) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (hotel_id, menu_item_id),
    CONSTRAINT chk_restaurant_menu_item_status
        CHECK (status IN ('active', 'passive', 'pending_approval')),
    CONSTRAINT chk_restaurant_menu_manual_status
        CHECK (manual_status IN ('catalog_verified', 'approval_required', 'rejected')),
    CONSTRAINT chk_restaurant_menu_price_nonnegative
        CHECK (price_try IS NULL OR price_try >= 0)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_menu_items_filter
ON restaurant_menu_catalog_items(hotel_id, status, venue, menu_type, category);

CREATE INDEX IF NOT EXISTS idx_restaurant_menu_items_name
ON restaurant_menu_catalog_items(hotel_id, lower(name_en), lower(COALESCE(name_tr, '')));

CREATE TABLE IF NOT EXISTS restaurant_menu_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    event_type VARCHAR(60) NOT NULL,
    reference_type VARCHAR(60) NOT NULL,
    reference_id VARCHAR(180),
    actor_username VARCHAR(80) NOT NULL DEFAULT 'system',
    payload_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_menu_audit_logs_hotel_created
ON restaurant_menu_audit_logs(hotel_id, created_at DESC);

CREATE TABLE IF NOT EXISTS restaurant_waiter_numbers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    waiter_name VARCHAR(120) NOT NULL,
    whatsapp_number VARCHAR(32) NOT NULL,
    role VARCHAR(80),
    venue VARCHAR(120),
    active BOOLEAN NOT NULL DEFAULT true,
    receives_order_notifications BOOLEAN NOT NULL DEFAULT true,
    created_by VARCHAR(80) NOT NULL DEFAULT 'system',
    updated_by VARCHAR(80) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_restaurant_waiter_numbers_unique_venue
ON restaurant_waiter_numbers(hotel_id, whatsapp_number, COALESCE(venue, ''));

CREATE INDEX IF NOT EXISTS idx_restaurant_waiter_numbers_routing
ON restaurant_waiter_numbers(hotel_id, active, receives_order_notifications, venue);

CREATE TABLE IF NOT EXISTS restaurant_ai_order_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(60) NOT NULL UNIQUE,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    venue VARCHAR(120),
    menu_type VARCHAR(80),
    table_or_room VARCHAR(80),
    guest_name VARCHAR(160),
    items_json JSONB NOT NULL DEFAULT '[]',
    total_try NUMERIC(12, 2),
    customer_note TEXT,
    allergy_note TEXT,
    confirmation_status VARCHAR(32) NOT NULL DEFAULT 'pending_confirmation',
    whatsapp_send_status VARCHAR(32) NOT NULL DEFAULT 'not_sent',
    selected_waiter_ids UUID[] NOT NULL DEFAULT '{}',
    waiter_delivery_json JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_restaurant_ai_order_confirmation_status
        CHECK (confirmation_status IN ('pending_confirmation', 'confirmed', 'sent_to_waiter', 'failed', 'cancelled')),
    CONSTRAINT chk_restaurant_ai_order_whatsapp_status
        CHECK (whatsapp_send_status IN ('not_sent', 'sent', 'failed', 'partial'))
);

CREATE INDEX IF NOT EXISTS idx_restaurant_ai_order_logs_hotel_created
ON restaurant_ai_order_logs(hotel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_restaurant_ai_order_logs_status
ON restaurant_ai_order_logs(hotel_id, confirmation_status, whatsapp_send_status);

CREATE TABLE IF NOT EXISTS restaurant_off_menu_request_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    requested_text TEXT NOT NULL,
    normalized_request VARCHAR(240) NOT NULL,
    detected_intent VARCHAR(80),
    venue VARCHAR(120),
    guest_context_json JSONB NOT NULL DEFAULT '{}',
    added_to_catalog BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_restaurant_off_menu_not_auto_added
        CHECK (added_to_catalog = false)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_off_menu_logs_hotel_created
ON restaurant_off_menu_request_logs(hotel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_restaurant_off_menu_logs_request
ON restaurant_off_menu_request_logs(hotel_id, lower(normalized_request));

CREATE TABLE IF NOT EXISTS restaurant_ai_message_settings (
    hotel_id INTEGER PRIMARY KEY REFERENCES hotels(hotel_id),
    off_menu_response TEXT NOT NULL,
    order_confirmation_message TEXT NOT NULL,
    whatsapp_notification_template TEXT NOT NULL,
    allergy_warning_text TEXT NOT NULL,
    menu_out_of_scope_guard_enabled BOOLEAN NOT NULL DEFAULT true,
    updated_by VARCHAR(80) NOT NULL DEFAULT 'system',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_restaurant_ai_guard_always_on
        CHECK (menu_out_of_scope_guard_enabled = true)
);
