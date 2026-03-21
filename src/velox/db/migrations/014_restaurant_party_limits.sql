ALTER TABLE restaurant_capacity_windows
    ADD COLUMN IF NOT EXISTS total_party_size_limit INTEGER,
    ADD COLUMN IF NOT EXISTS booked_party_size INTEGER NOT NULL DEFAULT 0;

ALTER TABLE restaurant_settings
    ADD COLUMN IF NOT EXISTS daily_max_party_size_enabled BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS daily_max_party_size_count INTEGER NOT NULL DEFAULT 200;
