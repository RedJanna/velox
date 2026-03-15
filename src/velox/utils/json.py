"""Helpers for decoding JSON/JSONB values returned from asyncpg."""

from __future__ import annotations

from typing import Any

import orjson


def decode_json_value(raw: Any) -> Any:
    """Return decoded JSON for dict/list/string/bytes inputs."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, (bytes, bytearray, memoryview, str)):
        try:
            return orjson.loads(raw)
        except orjson.JSONDecodeError:
            return None
    return None


def decode_json_object(raw: Any) -> dict[str, Any]:
    """Return a decoded JSON object or an empty dict."""
    decoded = decode_json_value(raw)
    return decoded if isinstance(decoded, dict) else {}
