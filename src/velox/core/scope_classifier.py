"""Deterministic scope classifier for hotel-reception boundaries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ScopeDecision(StrEnum):
    """Decision returned by the reception scope classifier."""

    IN_SCOPE = "in_scope"
    NEAR_SCOPE = "near_scope"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True, slots=True)
class ScopeResult:
    """Classifier output payload for logging and routing."""

    decision: ScopeDecision
    reason: str
    confidence: float


_IN_SCOPE_TERMS = (
    "rezervasyon",
    "reservation",
    "booking",
    "checkin",
    "check-in",
    "checkout",
    "check-out",
    "room",
    "oda",
    "price",
    "fiyat",
    "transfer",
    "havalimani",
    "airport",
    "restaurant",
    "restoran",
    "wifi",
    "pool",
    "spa",
    "parking",
    "otopark",
    "cancellation",
    "iptal",
    "invoice",
    "fatura",
    "payment",
    "odeme",
    "menü",
    "menu",
    "yemek",
    "kahvaltı",
    "kahvalti",
    "akşam yemeği",
    "aksam yemegi",
    "oda servisi",
    "room service",
    "sipariş",
    "siparis",
    "vegan",
    "alerji",
    "allergy",
    "diyet",
)

_NEAR_SCOPE_TERMS = (
    "eczane",
    "pharmacy",
    "atm",
    "market",
    "taxi",
    "taksi",
    "nearby",
    "yakinda",
    "yakın",
    "transport",
    "metro",
    "bus",
    "otobus",
)

_OUT_OF_SCOPE_PATTERNS = (
    re.compile(r"\b(kod|code|python|javascript|debug|regex|sql)\b", re.IGNORECASE),
    re.compile(r"\b(stock|crypto|bitcoin|yatirim|investment|borsa)\b", re.IGNORECASE),
    re.compile(r"\b(diagnosis|tedavi|reçete|recete|medical|hastalik)\b", re.IGNORECASE),
    re.compile(r"\b(lawsuit|mahkeme|hukuk|legal advice|avukat)\b", re.IGNORECASE),
    re.compile(r"\b(homework|odev|exam|sinav|tez)\b", re.IGNORECASE),
)


def classify_reception_scope(user_text: str) -> ScopeResult:
    """Classify whether a user request is in-scope for hotel reception support."""
    text = (user_text or "").strip().lower()
    if not text:
        return ScopeResult(decision=ScopeDecision.IN_SCOPE, reason="empty_message", confidence=0.51)

    has_in_scope_signal = any(token in text for token in _IN_SCOPE_TERMS)
    has_near_scope_signal = any(token in text for token in _NEAR_SCOPE_TERMS)
    has_out_scope_signal = any(pattern.search(text) for pattern in _OUT_OF_SCOPE_PATTERNS)

    if has_in_scope_signal:
        return ScopeResult(decision=ScopeDecision.IN_SCOPE, reason="hotel_domain_match", confidence=0.95)
    if has_near_scope_signal:
        return ScopeResult(decision=ScopeDecision.NEAR_SCOPE, reason="guest_convenience_match", confidence=0.8)
    if has_out_scope_signal:
        return ScopeResult(decision=ScopeDecision.OUT_OF_SCOPE, reason="non_reception_domain", confidence=0.9)

    # Prefer a safe allow-by-default path to avoid over-refusal.
    return ScopeResult(decision=ScopeDecision.IN_SCOPE, reason="no_strong_out_scope_signal", confidence=0.55)
