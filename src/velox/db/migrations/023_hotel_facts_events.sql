-- Migration 023: Publish/rollback audit trail for hotel facts

CREATE TABLE IF NOT EXISTS hotel_facts_events (
    event_id      BIGSERIAL PRIMARY KEY,
    hotel_id      INTEGER NOT NULL REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    version       INTEGER NOT NULL,
    checksum      TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    actor         TEXT NOT NULL DEFAULT 'system',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_hotel_facts_events_version
        FOREIGN KEY (hotel_id, version)
        REFERENCES hotel_facts_versions(hotel_id, version)
        ON DELETE CASCADE
);

ALTER TABLE hotel_facts_events
    ADD COLUMN IF NOT EXISTS event_id BIGINT;

CREATE SEQUENCE IF NOT EXISTS hotel_facts_events_event_id_seq;

ALTER TABLE hotel_facts_events
    ALTER COLUMN event_id SET DEFAULT nextval('hotel_facts_events_event_id_seq');

UPDATE hotel_facts_events
SET event_id = nextval('hotel_facts_events_event_id_seq')
WHERE event_id IS NULL;

ALTER TABLE hotel_facts_events
    ALTER COLUMN event_id SET NOT NULL;

ALTER TABLE hotel_facts_events
    ADD COLUMN IF NOT EXISTS checksum TEXT;

ALTER TABLE hotel_facts_events
    ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE hotel_facts_events
    ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ NOT NULL DEFAULT now();

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'hotel_facts_events'
          AND column_name = 'event_payload'
    ) THEN
        EXECUTE '
            UPDATE hotel_facts_events
            SET metadata_json = event_payload
            WHERE (metadata_json = ''{}''::jsonb OR metadata_json IS NULL)
              AND event_payload IS NOT NULL
        ';
    END IF;
END
$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'hotel_facts_events'
          AND column_name = 'created_at'
    ) THEN
        EXECUTE '
            UPDATE hotel_facts_events
            SET occurred_at = created_at
            WHERE created_at IS NOT NULL
        ';
    END IF;
END
$$;

UPDATE hotel_facts_events AS e
SET checksum = v.checksum
FROM hotel_facts_versions AS v
WHERE e.checksum IS NULL
  AND v.hotel_id = e.hotel_id
  AND v.version = e.version;

UPDATE hotel_facts_events
SET checksum = 'unknown'
WHERE checksum IS NULL;

ALTER TABLE hotel_facts_events
    ALTER COLUMN checksum SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_hotel_facts_events_hotel_time
    ON hotel_facts_events(hotel_id, occurred_at DESC, event_id DESC);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_hotel_facts_events_type'
    ) THEN
        ALTER TABLE hotel_facts_events
            ADD CONSTRAINT chk_hotel_facts_events_type
            CHECK (event_type = ANY (ARRAY['PUBLISH'::text, 'ROLLBACK'::text]))
            NOT VALID;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_hotel_facts_events_version'
    ) THEN
        ALTER TABLE hotel_facts_events
            ADD CONSTRAINT fk_hotel_facts_events_version
                FOREIGN KEY (hotel_id, version)
                REFERENCES hotel_facts_versions(hotel_id, version)
                ON DELETE CASCADE
                NOT VALID;
    END IF;
END
$$;
