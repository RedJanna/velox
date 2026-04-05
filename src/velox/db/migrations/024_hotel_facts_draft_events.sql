-- Migration 024: Allow DRAFT_SAVE audit events for hotel facts.

ALTER TABLE hotel_facts_events
    DROP CONSTRAINT IF EXISTS chk_hotel_facts_events_type;

ALTER TABLE hotel_facts_events
    ADD CONSTRAINT chk_hotel_facts_events_type
    CHECK (
        event_type = ANY (
            ARRAY[
                'PUBLISH'::text,
                'ROLLBACK'::text,
                'DRAFT_SAVE'::text
            ]
        )
    )
    NOT VALID;
