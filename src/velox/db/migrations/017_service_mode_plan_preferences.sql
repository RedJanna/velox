BEGIN;

ALTER TABLE restaurant_settings
    ADD COLUMN IF NOT EXISTS service_mode_main_plan_id UUID NULL REFERENCES restaurant_floor_plans(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS service_mode_pool_plan_id UUID NULL REFERENCES restaurant_floor_plans(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_rest_settings_service_main_plan
    ON restaurant_settings(service_mode_main_plan_id);

CREATE INDEX IF NOT EXISTS idx_rest_settings_service_pool_plan
    ON restaurant_settings(service_mode_pool_plan_id);

COMMIT;
