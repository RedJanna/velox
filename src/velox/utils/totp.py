"""Time-based one-time password helpers for admin login."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

TOTP_DIGITS = 6
TOTP_INTERVAL_SECONDS = 30
TOTP_SECRET_LENGTH = 32


def generate_totp_secret(length: int = TOTP_SECRET_LENGTH) -> str:
    """Generate a Base32 TOTP secret without padding."""
    random_bytes = secrets.token_bytes(length)
    return base64.b32encode(random_bytes).decode("ascii").rstrip("=")


def build_otpauth_uri(secret: str, account_name: str, issuer: str) -> str:
    """Build an otpauth URI compatible with Google Authenticator."""
    normalized_secret = normalize_totp_secret(secret)
    label = quote(f"{issuer}:{account_name}")
    issuer_param = quote(issuer)
    return (
        f"otpauth://totp/{label}?secret={normalized_secret}"
        f"&issuer={issuer_param}&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_INTERVAL_SECONDS}"
    )


def normalize_totp_secret(secret: str) -> str:
    """Normalize a Base32 TOTP secret for decoding."""
    cleaned = "".join(secret.strip().upper().split())
    if not cleaned:
        raise ValueError("TOTP secret is empty.")
    padding = "=" * ((8 - len(cleaned) % 8) % 8)
    try:
        base64.b32decode(cleaned + padding, casefold=True)
    except Exception as exc:  # pragma: no cover - decoder is the validation boundary
        raise ValueError("TOTP secret is not valid Base32.") from exc
    return cleaned


def verify_totp_code(
    secret: str,
    code: str,
    *,
    at_time: int | None = None,
    valid_window: int = 1,
) -> bool:
    """Verify a TOTP code using RFC 6238 compatible SHA1 HMAC."""
    normalized_code = "".join(code.strip().split())
    if not (normalized_code.isdigit() and len(normalized_code) == TOTP_DIGITS):
        return False

    normalized_secret = normalize_totp_secret(secret)
    timestamp = int(time.time()) if at_time is None else at_time
    counter = timestamp // TOTP_INTERVAL_SECONDS
    for offset in range(-valid_window, valid_window + 1):
        candidate = _totp_at_counter(normalized_secret, counter + offset)
        if hmac.compare_digest(candidate, normalized_code):
            return True
    return False


def generate_totp_code(secret: str, *, at_time: int | None = None) -> str:
    """Generate the current TOTP code for a secret."""
    normalized_secret = normalize_totp_secret(secret)
    timestamp = int(time.time()) if at_time is None else at_time
    counter = timestamp // TOTP_INTERVAL_SECONDS
    return _totp_at_counter(normalized_secret, counter)


def _totp_at_counter(secret: str, counter: int) -> str:
    """Generate a TOTP code for a normalized secret and counter."""
    if counter < 0:
        return "0" * TOTP_DIGITS

    padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    payload = struct.pack(">Q", counter)
    digest = hmac.new(key, payload, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary_code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary_code % (10**TOTP_DIGITS)).zfill(TOTP_DIGITS)
