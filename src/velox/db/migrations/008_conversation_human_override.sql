-- 008: Add human_override flag to conversations
-- When true, the system still generates AI replies but does NOT send them
-- via WhatsApp. Admin can toggle this per conversation from the panel.

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS human_override BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN conversations.human_override
    IS 'When true, AI replies are generated but never sent to the guest. Admin toggles this for human takeover.';
