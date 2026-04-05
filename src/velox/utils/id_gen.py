"""Sequential and unique ID generation for domain entities."""

from datetime import UTC, datetime
from typing import Final

from velox.db.database import fetchval

_SAFE_TARGETS: Final[dict[tuple[str, str], str]] = {
    ("stay_holds", "hold_id"): "SELECT COUNT(*) FROM stay_holds",
    ("restaurant_holds", "hold_id"): "SELECT COUNT(*) FROM restaurant_holds",
    ("transfer_holds", "hold_id"): "SELECT COUNT(*) FROM transfer_holds",
    ("approval_requests", "request_id"): "SELECT COUNT(*) FROM approval_requests",
    ("payment_requests", "request_id"): "SELECT COUNT(*) FROM payment_requests",
    ("tickets", "ticket_id"): "SELECT COUNT(*) FROM tickets",
    ("notifications", "notification_id"): "SELECT COUNT(*) FROM notifications",
}


async def next_sequential_id(prefix: str, table: str, column: str) -> str:
    """Generate the next sequential ID with the given prefix."""
    query = _SAFE_TARGETS.get((table, column))
    if query is None:
        raise ValueError(f"Unsupported table/column combination: {table}.{column}")

    count = await fetchval(query)
    if isinstance(count, int):
        current_count = count
    elif isinstance(count, str):
        current_count = int(count) if count.strip() else 0
    elif isinstance(count, (bytes, bytearray)):
        decoded = count.decode(errors="ignore").strip()
        current_count = int(decoded) if decoded else 0
    else:
        current_count = 0
    next_num = current_count + 1
    return f"{prefix}{next_num:03d}"


def _coerce_int(value: object) -> int:
    """Best-effort int parser for DB scalar values."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value.strip()) if value.strip() else 0
    if isinstance(value, (bytes, bytearray)):
        decoded = value.decode(errors="ignore").strip()
        return int(decoded) if decoded else 0
    return 0


async def next_reservation_no(hotel_id: int) -> str:
    """Generate the next reservation number in VLX-{hotel_id}-{YYMM}-{seq} format."""
    now = datetime.now(UTC)
    yymm = now.strftime("%y%m")
    prefix = f"VLX-{hotel_id}-{yymm}-"

    max_seq = await fetchval(
        """
        SELECT MAX(
            CAST(
                SUBSTRING(reservation_no FROM LENGTH($1) + 1) AS integer
            )
        )
        FROM stay_holds
        WHERE reservation_no LIKE $1 || '%'
        """,
        prefix,
    )
    next_seq = _coerce_int(max_seq) + 1
    return f"{prefix}{next_seq:04d}"
