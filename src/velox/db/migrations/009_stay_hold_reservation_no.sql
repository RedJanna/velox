-- 009: Add reservation_no column to stay_holds and backfill existing records.

ALTER TABLE stay_holds ADD COLUMN IF NOT EXISTS reservation_no VARCHAR(30) UNIQUE;

-- Backfill existing records with VLX-{hotel_id}-{YYMM}-{seq} format.
WITH numbered AS (
    SELECT hold_id, hotel_id, created_at,
        ROW_NUMBER() OVER (
            PARTITION BY hotel_id, date_trunc('month', created_at)
            ORDER BY created_at
        ) AS seq
    FROM stay_holds
    WHERE reservation_no IS NULL
)
UPDATE stay_holds sh
SET reservation_no = 'VLX-' || n.hotel_id || '-' ||
    to_char(n.created_at, 'YYMM') || '-' || lpad(n.seq::text, 4, '0')
FROM numbered n
WHERE sh.hold_id = n.hold_id AND sh.reservation_no IS NULL;

CREATE INDEX IF NOT EXISTS idx_stay_reservation_no
    ON stay_holds(reservation_no) WHERE reservation_no IS NOT NULL;
