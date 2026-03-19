-- 010: Persist WhatsApp provider ids in dedicated message columns for indexed reply resolution.

ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS whatsapp_message_id VARCHAR(128),
    ADD COLUMN IF NOT EXISTS reply_to_whatsapp_message_id VARCHAR(128);

UPDATE messages
SET whatsapp_message_id = internal_json->>'whatsapp_message_id'
WHERE whatsapp_message_id IS NULL
  AND internal_json IS NOT NULL
  AND internal_json ? 'whatsapp_message_id';

UPDATE messages
SET whatsapp_message_id = internal_json->>'message_id'
WHERE whatsapp_message_id IS NULL
  AND internal_json IS NOT NULL
  AND internal_json ? 'message_id';

UPDATE messages
SET reply_to_whatsapp_message_id = internal_json->>'reply_to_whatsapp_message_id'
WHERE reply_to_whatsapp_message_id IS NULL
  AND internal_json IS NOT NULL
  AND internal_json ? 'reply_to_whatsapp_message_id';

UPDATE messages
SET reply_to_whatsapp_message_id = internal_json->>'reply_to_message_id'
WHERE reply_to_whatsapp_message_id IS NULL
  AND internal_json IS NOT NULL
  AND internal_json ? 'reply_to_message_id';

CREATE INDEX IF NOT EXISTS idx_messages_conversation_whatsapp_message_id
    ON messages (conversation_id, whatsapp_message_id)
    WHERE whatsapp_message_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_conversation_reply_to_whatsapp_message_id
    ON messages (conversation_id, reply_to_whatsapp_message_id)
    WHERE reply_to_whatsapp_message_id IS NOT NULL;
