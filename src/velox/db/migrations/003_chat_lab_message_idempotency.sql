-- Chat Lab idempotency hardening for duplicate send protection

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS client_message_id VARCHAR(128);

UPDATE messages
SET client_message_id = internal_json->>'client_message_id'
WHERE client_message_id IS NULL
  AND internal_json IS NOT NULL
  AND internal_json ? 'client_message_id';

CREATE INDEX IF NOT EXISTS idx_messages_client_message_id
ON messages (conversation_id, client_message_id)
WHERE client_message_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_conversation_role_client_message_id
ON messages (conversation_id, role, client_message_id)
WHERE client_message_id IS NOT NULL
  AND role IN ('user', 'assistant');
