"""Idempotency primitives for approval and supplier-create operations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

IDEMPOTENCY_NAMESPACE_APPROVAL = "approval"
IDEMPOTENCY_NAMESPACE_CREATE = "create"


@dataclass(frozen=True, slots=True)
class IdempotencyInput:
    """Stable input used for deterministic idempotency key generation."""

    namespace: str
    reference_id: str
    hotel_id: int
    version: int = 1


def build_idempotency_key(payload: IdempotencyInput) -> str:
    """Builds a deterministic idempotency key safe for unique constraints."""
    raw = (
        f"v{payload.version}:{payload.namespace}:"
        f"hotel:{payload.hotel_id}:ref:{payload.reference_id}"
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"idem_{digest}"
