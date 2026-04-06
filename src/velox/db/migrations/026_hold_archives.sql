-- 026: Add archive tracking fields for holds (stay/restaurant/transfer).

ALTER TABLE stay_holds
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS archived_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS archived_reason TEXT;

ALTER TABLE restaurant_holds
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS archived_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS archived_reason TEXT;

ALTER TABLE transfer_holds
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS archived_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS archived_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_stay_holds_archived_at
    ON stay_holds(hotel_id, archived_at);

CREATE INDEX IF NOT EXISTS idx_restaurant_holds_archived_at
    ON restaurant_holds(hotel_id, archived_at);

CREATE INDEX IF NOT EXISTS idx_transfer_holds_archived_at
    ON transfer_holds(hotel_id, archived_at);
