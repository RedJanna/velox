-- Migration 022: Add source profile payload and normalize checksum/current pointer schema

ALTER TABLE hotel_facts_versions
    ADD COLUMN IF NOT EXISTS checksum TEXT;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'hotel_facts_versions'
          AND column_name = 'facts_checksum'
    ) THEN
        EXECUTE '
            UPDATE hotel_facts_versions
            SET checksum = facts_checksum
            WHERE checksum IS NULL
        ';
    END IF;
END
$$;

UPDATE hotel_facts_versions
SET checksum = md5(
    hotel_id::text
    || ':'
    || version::text
    || ':'
    || COALESCE(source_profile_checksum, '')
)
WHERE checksum IS NULL;

ALTER TABLE hotel_facts_versions
    ALTER COLUMN checksum SET NOT NULL;

ALTER TABLE hotel_facts_versions
    ADD COLUMN IF NOT EXISTS source_profile_json JSONB;

UPDATE hotel_facts_versions
SET source_profile_json = facts_json
WHERE source_profile_json IS NULL;

ALTER TABLE hotel_facts_versions
    ALTER COLUMN source_profile_json SET NOT NULL;

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

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'hotel_facts_versions'
          AND column_name = 'is_current'
    ) THEN
        EXECUTE '
            INSERT INTO hotel_facts_current (hotel_id, version, checksum, published_at)
            SELECT hotel_id, version, checksum, published_at
            FROM hotel_facts_versions
            WHERE is_current = true
            ON CONFLICT (hotel_id) DO UPDATE
            SET version = EXCLUDED.version,
                checksum = EXCLUDED.checksum,
                published_at = EXCLUDED.published_at
        ';
    ELSE
        EXECUTE '
            INSERT INTO hotel_facts_current (hotel_id, version, checksum, published_at)
            SELECT DISTINCT ON (hotel_id) hotel_id, version, checksum, published_at
            FROM hotel_facts_versions
            ORDER BY hotel_id, version DESC
            ON CONFLICT (hotel_id) DO UPDATE
            SET version = EXCLUDED.version,
                checksum = EXCLUDED.checksum,
                published_at = EXCLUDED.published_at
        ';
    END IF;
END
$$;
