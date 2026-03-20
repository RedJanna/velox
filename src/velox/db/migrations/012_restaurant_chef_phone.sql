-- Migration 012: Add editable chef phone to restaurant settings

BEGIN;

ALTER TABLE restaurant_settings
    ADD COLUMN IF NOT EXISTS chef_phone VARCHAR(32);

COMMIT;
