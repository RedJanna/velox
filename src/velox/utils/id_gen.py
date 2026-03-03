"""Sequential and unique ID generation for domain entities."""

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
    next_num = int(count or 0) + 1
    return f"{prefix}{next_num:03d}"
