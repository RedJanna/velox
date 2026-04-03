"""Lightweight response validator and tone guard for guest-facing replies."""

from __future__ import annotations

import re
from typing import Any

from velox.core.fallback_response_library import out_of_scope_refusal, response_validation_fallback
from velox.core.scope_classifier import ScopeDecision
from velox.models.conversation import LLMResponse

_TECHNICAL_LEAK_PATTERN = re.compile(
    r"(traceback|exception|stack\s*trace|internal server error|sqlstate|api[_ -]?key|token=|http[s]?://)",
    re.IGNORECASE,
)
_CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
_MULTI_EXCLAMATION_PATTERN = re.compile(r"!{2,}")
_RUDE_TR_PATTERN = re.compile(r"\b(saçma|sacma|uğraşamam|ugrasamam|bilmiyorum)\b", re.IGNORECASE)
_OUT_SCOPE_TR_HINTS = ("dogrudan destek saglayamiyorum", "konaklamaniz", "otel hizmetlerimiz")
_OUT_SCOPE_EN_HINTS = ("cannot support that topic directly", "stay", "hotel services")
_OUT_SCOPE_RU_HINTS = ("не могу напрямую помочь", "проживанием", "услугами отеля")


def validate_guest_response(
    response: LLMResponse,
    *,
    default_language: str,
    scope_decision: ScopeDecision | None = None,
) -> LLMResponse:
    """Validate response text and apply deterministic guardrails when needed."""
    language = str(response.internal_json.language or default_language or "tr").lower()
    text = _clean_text(response.user_message)
    rules_applied: list[str] = []

    if not text:
        text = response_validation_fallback(language)
        rules_applied.append("empty_message_fallback")

    if _TECHNICAL_LEAK_PATTERN.search(text):
        text = response_validation_fallback(language)
        rules_applied.append("technical_leak_fallback")

    if scope_decision == ScopeDecision.OUT_OF_SCOPE and not _is_scope_refusal(text, language):
        text = out_of_scope_refusal(language)
        rules_applied.append("out_of_scope_refusal_enforced")

    text = _normalize_tone(text, language)
    response.user_message = text
    response.internal_json.language = language

    if rules_applied:
        entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
        validator_meta: dict[str, Any] = entities.get("response_validator") if isinstance(entities, dict) else {}
        if not isinstance(validator_meta, dict):
            validator_meta = {}
        validator_meta["applied"] = True
        validator_meta["rules"] = rules_applied
        entities["response_validator"] = validator_meta
        response.internal_json.entities = entities

    return response


def _clean_text(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    value = _CODE_BLOCK_PATTERN.sub("", value).strip()
    value = value.replace("`", "")
    value = _MULTI_EXCLAMATION_PATTERN.sub("!", value)
    return value


def _normalize_tone(text: str, language: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned

    if language == "tr":
        cleaned = _RUDE_TR_PATTERN.sub("yardimci olamam", cleaned)
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _is_scope_refusal(text: str, language: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if language == "en":
        return all(token in normalized for token in _OUT_SCOPE_EN_HINTS)
    if language == "ru":
        return all(token in normalized for token in _OUT_SCOPE_RU_HINTS)
    return all(token in normalized for token in _OUT_SCOPE_TR_HINTS)
