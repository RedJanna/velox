BEGIN;

-- Admin conversation list: hotel scope + state/date filters + recency order.
CREATE INDEX IF NOT EXISTS idx_conversations_hotel_last_message
    ON conversations(hotel_id, last_message_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_hotel_created_at
    ON conversations(hotel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_hotel_state_created
    ON conversations(hotel_id, current_state, created_at DESC);

-- LATERAL assistant/user lookups in admin conversation views.
CREATE INDEX IF NOT EXISTS idx_messages_conv_role_created_desc
    ON messages(conversation_id, role, created_at DESC);

-- Admin ticket queue: role-scoped and unscoped list queries.
CREATE INDEX IF NOT EXISTS idx_tickets_hotel_priority_created
    ON tickets(hotel_id, priority, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tickets_hotel_role_priority_created
    ON tickets(hotel_id, assigned_to_role, priority, created_at DESC);

COMMIT;
