"""Elektraweb PMS adapter package."""

from velox.adapters.elektraweb.client import close_elektraweb_client, get_elektraweb_client
from velox.adapters.elektraweb.endpoints import (
    availability,
    cancel_reservation,
    create_reservation,
    get_reservation,
    modify_reservation,
    quote,
    sync_reservation_card_fields,
)
from velox.adapters.elektraweb.mapper import kebab_to_snake, normalize_keys

__all__ = [
    "get_elektraweb_client",
    "close_elektraweb_client",
    "availability",
    "quote",
    "create_reservation",
    "get_reservation",
    "modify_reservation",
    "cancel_reservation",
    "sync_reservation_card_fields",
    "normalize_keys",
    "kebab_to_snake",
]
