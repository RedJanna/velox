"""Utilities for customer-visible reservation notes."""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_SUFFIX_RE = re.compile(r"[.!?]+$")
_SENTENCE_START_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿÇĞİÖŞÜçğıöşüА-Яа-я]")

_NO_NOTE_VALUES = {
    "",
    "yok",
    "yoktur",
    "özel istek yok",
    "ozel istek yok",
    "hayir",
    "hayır",
    "none",
    "no",
    "no special request",
    "no special requests",
    "nothing",
    "nothing special",
    "n/a",
    "na",
}

_NO_NOTE_PATTERNS = (
    re.compile(r"\bozel( bir)? istek yok\b", flags=re.IGNORECASE),
    re.compile(r"\bözel( bir)? istek yok\b", flags=re.IGNORECASE),
    re.compile(r"\bozel talep yok\b", flags=re.IGNORECASE),
    re.compile(r"\bözel talep yok\b", flags=re.IGNORECASE),
    re.compile(r"\bherhangi bir ozel istek yok\b", flags=re.IGNORECASE),
    re.compile(r"\bno special request(s)?\b", flags=re.IGNORECASE),
    re.compile(r"\bnothing special\b", flags=re.IGNORECASE),
)

_INTERNAL_JARGON_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bpms\b", flags=re.IGNORECASE), "rezervasyon sistemi"),
    (re.compile(r"\bops\b", flags=re.IGNORECASE), "operasyon ekibi"),
    (re.compile(r"\badmin\b", flags=re.IGNORECASE), "yetkili ekip"),
    (re.compile(r"\bhandoff\b", flags=re.IGNORECASE), "ilgili ekip yönlendirmesi"),
    (re.compile(r"\bescalat(?:e|ion)\b", flags=re.IGNORECASE), "ilgili ekip yönlendirmesi"),
    (re.compile(r"\bticket\b", flags=re.IGNORECASE), "takip kaydı"),
    (re.compile(r"\bapi\b", flags=re.IGNORECASE), "sistem"),
    (re.compile(r"\bworkflow\b", flags=re.IGNORECASE), "süreç"),
)


def _normalize_text(value: str | None) -> str:
    """Normalize spacing and trim surrounding punctuation noise."""
    text = _WHITESPACE_RE.sub(" ", str(value or "").strip())
    return text.strip(" \t\r\n\"'`")


def _looks_like_no_note(text: str) -> bool:
    """Return True when note indicates there is no extra request."""
    lowered = text.casefold()
    if lowered in _NO_NOTE_VALUES:
        return True
    return any(pattern.search(text) for pattern in _NO_NOTE_PATTERNS)


def _replace_internal_jargon(text: str) -> str:
    """Rewrite internal operational jargon into customer-facing wording."""
    cleaned = text
    for pattern, replacement in _INTERNAL_JARGON_REPLACEMENTS:
        cleaned = pattern.sub(replacement, cleaned)
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def format_customer_visible_note(note: str | None) -> str:
    """Return reservation note as one clear, customer-facing full sentence."""
    normalized = _normalize_text(note)
    if not normalized or _looks_like_no_note(normalized):
        return ""

    cleaned = _replace_internal_jargon(normalized)
    if not cleaned:
        return ""

    cleaned = _PUNCT_SUFFIX_RE.sub("", cleaned).strip()
    if not cleaned:
        return ""

    if _SENTENCE_START_RE.match(cleaned):
        cleaned = cleaned[0].upper() + cleaned[1:]

    prefixed = cleaned.casefold().startswith("misafirimiz şu notu iletti:")
    sentence = cleaned if prefixed else f"Misafirimiz şu notu iletti: {cleaned}"
    return f"{sentence}."
