-- 033: Public QR restaurant ordering flow, two customer confirmations, and staff approval states.

ALTER TABLE restaurant_ai_order_logs
    ADD COLUMN IF NOT EXISTS service_type VARCHAR(32),
    ADD COLUMN IF NOT EXISTS meal_period VARCHAR(32),
    ADD COLUMN IF NOT EXISTS language_code VARCHAR(12),
    ADD COLUMN IF NOT EXISTS table_no VARCHAR(80),
    ADD COLUMN IF NOT EXISTS customer_confirmation_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS customer_confirmed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS staff_decision_by VARCHAR(80),
    ADD COLUMN IF NOT EXISTS staff_decision_at TIMESTAMPTZ;

ALTER TABLE restaurant_ai_order_logs
    DROP CONSTRAINT IF EXISTS chk_restaurant_ai_order_confirmation_status;

ALTER TABLE restaurant_ai_order_logs
    ADD CONSTRAINT chk_restaurant_ai_order_confirmation_status
        CHECK (confirmation_status IN (
            'draft',
            'customer_confirmed_once',
            'customer_confirmed_twice',
            'sent_to_staff',
            'pending_staff_approval',
            'accepted_by_staff',
            'rejected_by_staff',
            'preparing',
            'completed',
            'cancelled',
            'pending_confirmation',
            'confirmed',
            'sent_to_waiter',
            'failed'
        ));

ALTER TABLE restaurant_ai_order_logs
    DROP CONSTRAINT IF EXISTS chk_restaurant_ai_order_service_type;

ALTER TABLE restaurant_ai_order_logs
    ADD CONSTRAINT chk_restaurant_ai_order_service_type
        CHECK (service_type IS NULL OR service_type IN ('table_service', 'room_service'));

ALTER TABLE restaurant_ai_order_logs
    DROP CONSTRAINT IF EXISTS chk_restaurant_ai_order_meal_period;

ALTER TABLE restaurant_ai_order_logs
    ADD CONSTRAINT chk_restaurant_ai_order_meal_period
        CHECK (meal_period IS NULL OR meal_period IN ('breakfast', 'lunch', 'dinner'));

ALTER TABLE restaurant_ai_order_logs
    DROP CONSTRAINT IF EXISTS chk_restaurant_ai_order_customer_confirmations;

ALTER TABLE restaurant_ai_order_logs
    ADD CONSTRAINT chk_restaurant_ai_order_customer_confirmations
        CHECK (customer_confirmation_count BETWEEN 0 AND 2);

CREATE INDEX IF NOT EXISTS idx_restaurant_ai_order_logs_public_queue
ON restaurant_ai_order_logs(hotel_id, confirmation_status, created_at DESC);

CREATE TABLE IF NOT EXISTS restaurant_public_order_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
    order_id VARCHAR(60),
    event_type VARCHAR(80) NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_public_order_audit_hotel_created
ON restaurant_public_order_audit_logs(hotel_id, created_at DESC);
