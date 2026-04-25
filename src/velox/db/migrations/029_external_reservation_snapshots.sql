-- 029: Store minimal PII-safe snapshots for external PMS reservation lookups.

CREATE TABLE IF NOT EXISTS external_reservation_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    lookup_key VARCHAR(160) NOT NULL,
    pms_reservation_id VARCHAR(80),
    voucher_no VARCHAR(80),
    phone_hash VARCHAR(64),
    checkin_date DATE,
    checkout_date DATE,
    state VARCHAR(50) NOT NULL DEFAULT '',
    total_price NUMERIC(12, 2),
    snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    source VARCHAR(40) NOT NULL DEFAULT 'elektraweb',
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_external_reservation_snapshot_lookup
ON external_reservation_snapshots(hotel_id, lookup_key);

CREATE INDEX IF NOT EXISTS idx_external_reservation_snapshot_phone_hash
ON external_reservation_snapshots(hotel_id, phone_hash)
WHERE phone_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_external_reservation_snapshot_stay_dates
ON external_reservation_snapshots(hotel_id, checkin_date, checkout_date);
