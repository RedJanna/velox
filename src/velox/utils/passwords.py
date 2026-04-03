"""Password hashing helpers backed directly by bcrypt."""

from __future__ import annotations

import bcrypt

BCRYPT_PASSWORD_MAX_BYTES = 72


def ensure_password_within_bcrypt_limit(password: str) -> str:
    """Reject passwords that exceed bcrypt's byte-length limit."""
    if len(password.encode("utf-8")) > BCRYPT_PASSWORD_MAX_BYTES:
        raise ValueError(f"Password must be at most {BCRYPT_PASSWORD_MAX_BYTES} bytes")
    return password


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    ensure_password_within_bcrypt_limit(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (TypeError, ValueError):
        return False
