-- Add restaurant reservation mode toggle (AI_RESTAURAN | MANUEL)
ALTER TABLE restaurant_settings
ADD COLUMN IF NOT EXISTS reservation_mode TEXT NOT NULL DEFAULT 'AI_RESTAURAN';

ALTER TABLE restaurant_settings
DROP CONSTRAINT IF EXISTS restaurant_settings_reservation_mode_check;

ALTER TABLE restaurant_settings
ADD CONSTRAINT restaurant_settings_reservation_mode_check
CHECK (reservation_mode IN ('AI_RESTAURAN', 'MANUEL'));
