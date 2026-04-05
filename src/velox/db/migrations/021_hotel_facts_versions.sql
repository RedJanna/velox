-- Migration 021: Base tables for versioned hotel facts publishing

CREATE TABLE IF NOT EXISTS hotel_facts_versions (
    hotel_id                INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    version                 INTEGER NOT NULL,
    checksum                TEXT NOT NULL,
    source_profile_checksum TEXT NOT NULL,
    facts_json              JSONB NOT NULL,
    validation_json         JSONB NOT NULL DEFAULT '{"blockers": [], "warnings": []}'::jsonb,
    published_by            TEXT NOT NULL DEFAULT 'system',
    published_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (hotel_id, version)
);

CREATE INDEX IF NOT EXISTS idx_hotel_facts_versions_hotel_published
    ON hotel_facts_versions(hotel_id, published_at DESC);

CREATE TABLE IF NOT EXISTS hotel_facts_current (
    hotel_id     INTEGER PRIMARY KEY REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    version      INTEGER NOT NULL,
    checksum     TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_hotel_facts_current_version
        FOREIGN KEY (hotel_id, version)
        REFERENCES hotel_facts_versions(hotel_id, version)
        ON DELETE CASCADE
);
