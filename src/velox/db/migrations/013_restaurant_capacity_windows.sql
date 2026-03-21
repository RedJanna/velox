-- Restaurant capacity windows for total reservation limits and pax constraints

CREATE TABLE IF NOT EXISTS restaurant_capacity_windows (
    id                  SERIAL PRIMARY KEY,
    hotel_id            INTEGER NOT NULL REFERENCES hotels(hotel_id),
    date_from           DATE NOT NULL,
    date_to             DATE NOT NULL,
    start_time          TIME NOT NULL,
    end_time            TIME NOT NULL,
    area                VARCHAR(20) DEFAULT 'outdoor',
    reservation_limit   INTEGER NOT NULL,
    booked_reservations INTEGER NOT NULL DEFAULT 0,
    min_party_size      INTEGER NOT NULL DEFAULT 1,
    max_party_size      INTEGER NOT NULL DEFAULT 8,
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_capacity_windows_lookup
    ON restaurant_capacity_windows(hotel_id, date_from, date_to, area, is_active);

ALTER TABLE restaurant_slots
    ADD COLUMN IF NOT EXISTS capacity_window_id INTEGER REFERENCES restaurant_capacity_windows(id);

CREATE INDEX IF NOT EXISTS idx_restaurant_slots_capacity_window_id
    ON restaurant_slots(capacity_window_id);

ALTER TABLE restaurant_settings
    ADD COLUMN IF NOT EXISTS min_party_size INTEGER NOT NULL DEFAULT 1;

ALTER TABLE restaurant_settings
    ADD COLUMN IF NOT EXISTS max_party_size INTEGER NOT NULL DEFAULT 8;
