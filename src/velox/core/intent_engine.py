"""Lightweight local intent detection helpers for testing and fallback use."""

import re

from velox.config.constants import Intent

_COMPLAINT_PATTERN = re.compile(
    r"\b(rezalet|berbat|sikayet|complaint|awful|terrible)\b",
    re.IGNORECASE,
)
_HANDOFF_PATTERN = re.compile(
    r"\b(insan|yetkili|operator|human|representative|agent)\b",
    re.IGNORECASE,
)
_TRANSFER_PATTERN = re.compile(
    r"\b(transfer|havalimani|airport|dalaman|antalya)\b",
    re.IGNORECASE,
)
_FAQ_PATTERN = re.compile(
    r"\b(wifi|check[- ]?in|check[- ]?out|kahvalti|breakfast|pool|parking)\b",
    re.IGNORECASE,
)
_BOOKING_PATTERN = re.compile(
    r"\b(oda|rezervasyon|reservation|availability|musait)\b",
    re.IGNORECASE,
)


def detect_intent(message: str) -> Intent:
    """Detect a coarse intent from user text using deterministic rules."""
    text = message.strip()
    if _COMPLAINT_PATTERN.search(text):
        return Intent.COMPLAINT
    if _HANDOFF_PATTERN.search(text):
        return Intent.HUMAN_HANDOFF
    if _TRANSFER_PATTERN.search(text):
        return Intent.TRANSFER_INFO
    if _FAQ_PATTERN.search(text):
        return Intent.FAQ_INFO
    if _BOOKING_PATTERN.search(text):
        return Intent.STAY_AVAILABILITY
    return Intent.OTHER
