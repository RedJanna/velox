"""Signed table token helpers for the public restaurant ordering panel."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from velox.config.settings import settings


@dataclass(frozen=True)
class RestaurantTableToken:
    """Verified public table-ordering token payload."""

    hotel_id: int
    venue: str
    table_no: str
    token_version: int = 1


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign(payload: str) -> str:
    secret = settings.app_secret_key or settings.admin_jwt_secret
    digest = hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    return _b64_encode(digest)


def create_table_order_token(
    *,
    hotel_id: int,
    venue: str,
    table_no: str,
    token_version: int = 1,
) -> str:
    """Create a tamper-proof public token for one restaurant table."""
    payload: dict[str, Any] = {
        "hotel_id": hotel_id,
        "venue": venue.strip(),
        "table_no": table_no.strip(),
        "token_version": token_version,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    encoded = _b64_encode(payload_json.encode("utf-8"))
    return f"{encoded}.{_sign(encoded)}"


def verify_table_order_token(token: str) -> RestaurantTableToken | None:
    """Verify one public table token and return its payload if valid."""
    value = token.strip()
    if "." not in value:
        return None
    encoded, signature = value.rsplit(".", maxsplit=1)
    expected = _sign(encoded)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_b64_decode(encoded).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        hotel_id = int(payload["hotel_id"])
        venue = str(payload["venue"]).strip()
        table_no = str(payload["table_no"]).strip()
        token_version = int(payload.get("token_version") or 1)
    except (KeyError, TypeError, ValueError):
        return None
    if hotel_id < 1 or not venue or not table_no:
        return None
    return RestaurantTableToken(
        hotel_id=hotel_id,
        venue=venue,
        table_no=table_no,
        token_version=token_version,
    )
