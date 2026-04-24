-- Migration 011: Backfill restaurant foundation tables/columns for fresh databases.

BEGIN;

CREATE TABLE IF NOT EXISTS restaurant_settings (
    hotel_id INTEGER PRIMARY KEY REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    daily_max_reservations_enabled BOOLEAN NOT NULL DEFAULT false,
    daily_max_reservations_count INTEGER NOT NULL DEFAULT 50,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS restaurant_floor_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL DEFAULT 'Ana Plan',
    layout_data JSONB NOT NULL DEFAULT '{"canvas_width": 1200, "canvas_height": 800, "floor_theme": "CREAM_MARBLE_CLASSIC", "tables": [], "shapes": []}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_floor_plans_hotel
    ON restaurant_floor_plans(hotel_id, is_active, updated_at DESC);

CREATE TABLE IF NOT EXISTS restaurant_tables (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    floor_plan_id UUID NOT NULL REFERENCES restaurant_floor_plans(id) ON DELETE CASCADE,
    table_id VARCHAR(64) NOT NULL,
    table_type VARCHAR(32) NOT NULL,
    capacity INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_restaurant_tables_hotel_table
    ON restaurant_tables(hotel_id, table_id);

CREATE INDEX IF NOT EXISTS idx_restaurant_tables_floor_plan
    ON restaurant_tables(floor_plan_id, is_active);

ALTER TABLE restaurant_holds
    ADD COLUMN IF NOT EXISTS table_type VARCHAR(32),
    ADD COLUMN IF NOT EXISTS table_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS arrived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS no_show_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS extended_minutes INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_restaurant_holds_table_id
    ON restaurant_holds(hotel_id, date, table_id)
    WHERE table_id IS NOT NULL;

COMMIT;
