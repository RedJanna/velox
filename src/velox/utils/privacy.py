"""Privacy helpers for hashing and masking sensitive values."""

from __future__ import annotations

import hashlib

from velox.config.settings import settings


def hash_phone(phone: str) -> str:
    """Return a deterministic phone hash, salted when configured."""
    normalized = phone.strip()
    salt = settings.phone_hash_salt.strip()
    payload = f"{salt}{normalized}" if salt else normalized
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

