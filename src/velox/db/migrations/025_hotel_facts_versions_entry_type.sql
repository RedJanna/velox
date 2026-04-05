-- Migration 025: Track facts version entry type (publish vs draft save).

ALTER TABLE hotel_facts_versions
    ADD COLUMN IF NOT EXISTS entry_type TEXT;

UPDATE hotel_facts_versions
SET entry_type = 'PUBLISH'
WHERE entry_type IS NULL;

ALTER TABLE hotel_facts_versions
    ALTER COLUMN entry_type SET NOT NULL;

ALTER TABLE hotel_facts_versions
    DROP CONSTRAINT IF EXISTS chk_hotel_facts_versions_entry_type;

ALTER TABLE hotel_facts_versions
    ADD CONSTRAINT chk_hotel_facts_versions_entry_type
    CHECK (
        entry_type = ANY (
            ARRAY[
                'PUBLISH'::text,
                'DRAFT_SAVE'::text
            ]
        )
    )
    NOT VALID;
