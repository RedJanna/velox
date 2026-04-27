-- 030: Admin access-control foundation with hotel departments and user-level permission overrides.

ALTER TABLE admin_users
    ADD COLUMN IF NOT EXISTS department_code VARCHAR(50);

UPDATE admin_users
SET department_code = CASE role
    WHEN 'ADMIN' THEN 'MANAGEMENT'
    WHEN 'SALES' THEN 'RESERVATION_SALES'
    WHEN 'OPS' THEN 'FRONT_OFFICE'
    WHEN 'CHEF' THEN 'FOOD_BEVERAGE'
    ELSE 'OTHER'
END
WHERE department_code IS NULL OR btrim(department_code) = '';

ALTER TABLE admin_users
    ALTER COLUMN department_code SET NOT NULL;

ALTER TABLE admin_users
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE admin_users
SET updated_at = COALESCE(updated_at, created_at, now());

CREATE INDEX IF NOT EXISTS idx_admin_users_hotel_department
ON admin_users(hotel_id, department_code);

CREATE TABLE IF NOT EXISTS admin_user_permission_overrides (
    admin_user_id INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    permission_key VARCHAR(80) NOT NULL,
    is_allowed BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (admin_user_id, permission_key)
);

CREATE INDEX IF NOT EXISTS idx_admin_user_permission_overrides_user
ON admin_user_permission_overrides(admin_user_id);
