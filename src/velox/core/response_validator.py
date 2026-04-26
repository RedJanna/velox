"""Lightweight response validator and tone guard for guest-facing replies."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from velox.core.fallback_response_library import (
    menu_not_available_fallback,
    order_commitment_fallback,
    out_of_scope_refusal,
    unresolved_handoff_fallback,
)
from velox.core.scope_classifier import ScopeDecision
from velox.models.conversation import LLMResponse

_TECHNICAL_LEAK_PATTERN = re.compile(
    r"(traceback|exception|stack\s*trace|internal server error|sqlstate|api[_ -]?key|token=|http[s]?://)",
    re.IGNORECASE,
)
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_ALLOWED_PUBLIC_LINK_HOSTS = {
    "maps.app.goo.gl",
    "maps.google.com",
    "google.com",
    "www.google.com",
    "m.google.com",
}
_CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
_MULTI_EXCLAMATION_PATTERN = re.compile(r"!{2,}")
_RUDE_TR_PATTERN = re.compile(r"\b(saçma|sacma|uğraşamam|ugrasamam|bilmiyorum)\b", re.IGNORECASE)
_OUT_SCOPE_TR_HINTS = ("dogrudan destek saglayamiyorum", "konaklamaniz", "otel hizmetlerimiz")
_OUT_SCOPE_EN_HINTS = ("cannot support that topic directly", "stay", "hotel services")
_OUT_SCOPE_RU_HINTS = ("не могу напрямую помочь", "проживанием", "услугами отеля")

# Pattern to detect operational commitments without real tool backing.
_OPERATIONAL_COMMITMENT_PATTERN = re.compile(
    r"(haz[ıi]rlat[ıi]yorum|haz[ıi]rlan[ıi]yor|g[oö]nderiliyor|g[oö]nderiyorum|"
    r"sipari[sş]iniz.*haz[ıi]r|servis\s*ediliyor|getiriliyor|ayarl[ıi]yorum|"
    r"rezervasyon(?:unuzu| talebinizi)?\s*(olu[sş]turuyorum|i[sş]leme\s*al[ıi]yorum|"
    r"tamaml[ıi]yorum|onaya\s*iletiyorum)|"
    r"preparing\s*your|sending\s*to\s*your\s*room|your\s*order\s*is|delivering|"
    r"creating\s*your\s*reservation|processing\s*your\s*reservation|"
    r"your\s*reservation\s*is\s*(being\s*)?(created|processed|confirmed))",
    re.IGNORECASE,
)

# Pattern to detect menu item claims without data source
_MENU_ITEM_PATTERN = re.compile(
    r"(men[uü]\s*[oö]neri|men[uü]\s*se[cç]enek|ba[sş]lang[ıi][cç]|"
    r"ana\s*yemek|tatl[ıi]\s*se[cç]enek|aperitif|dessert\s*option|"
    r"starter|main\s*course|appetizer)",
    re.IGNORECASE,
)


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
        text = unresolved_handoff_fallback(language)
        _mark_mandatory_handoff(
            response,
            reason="empty_or_unreliable_assistant_response",
            risk_flag="UNRESOLVED_CASE",
        )
        rules_applied.append("empty_message_fallback")

    if _contains_technical_leak(text):
        text = unresolved_handoff_fallback(language)
        _mark_mandatory_handoff(
            response,
            reason="unsafe_or_unreliable_assistant_response",
            risk_flag="UNRESOLVED_CASE",
        )
        rules_applied.append("technical_leak_fallback")

    if scope_decision == ScopeDecision.OUT_OF_SCOPE and not _is_scope_refusal(text, language):
        text = out_of_scope_refusal(language)
        rules_applied.append("out_of_scope_refusal_enforced")

    # Guard: Detect operational commitments without any tool call backing
    tool_calls = response.internal_json.tool_calls or []
    if not tool_calls and _OPERATIONAL_COMMITMENT_PATTERN.search(text):
        text = _replace_commitment_with_handoff(text, language)
        _mark_mandatory_handoff(
            response,
            reason="toolless_operational_commitment",
            risk_flag="PHYSICAL_OPERATION_REQUEST",
            route_to_role="OPS",
            level="L1",
            sla_hint="medium",
            next_step="handoff_to_ops",
        )
        rules_applied.append("toolless_commitment_blocked")

    # Guard: Detect menu item recommendations without menu data source
    if not tool_calls and _MENU_ITEM_PATTERN.search(text):
        text = menu_not_available_fallback(language)
        notifications = response.internal_json.notifications or []
        notifications.append({
            "channel": "panel",
            "to_role": "CHEF",
            "message": "Misafir menu/yemek bilgisi talep etti. Dogrulanmis menu verisi mevcut degil.",
        })
        response.internal_json.notifications = notifications
        if "MENU_HALLUCINATION_RISK" not in response.internal_json.risk_flags:
            response.internal_json.risk_flags.append("MENU_HALLUCINATION_RISK")
        _mark_mandatory_handoff(
            response,
            reason="menu_information_requires_human_verification",
            risk_flag="MENU_HALLUCINATION_RISK",
            route_to_role="CHEF",
            level="L1",
            sla_hint="medium",
            next_step="handoff_to_restaurant_team",
        )
        rules_applied.append("menu_hallucination_risk_flagged")

    text = _normalize_tone(text, language)
    response.user_message = text
    response.internal_json.language = language

    if rules_applied:
        entities = response.internal_json.entities if isinstance(response.internal_json.entities, dict) else {}
        raw_validator_meta = entities.get("response_validator")
        validator_meta: dict[str, Any] = raw_validator_meta if isinstance(raw_validator_meta, dict) else {}
        if not isinstance(validator_meta, dict):
            validator_meta = {}
        validator_meta["applied"] = True
        validator_meta["rules"] = rules_applied
        entities["response_validator"] = validator_meta
        response.internal_json.entities = entities

    return response


def _mark_mandatory_handoff(
    response: LLMResponse,
    *,
    reason: str,
    risk_flag: str,
    route_to_role: str = "ADMIN",
    level: str = "L2",
    sla_hint: str = "high",
    next_step: str = "handoff_to_admin",
) -> None:
    """Mark a response as a terminal handoff when reliability is insufficient."""
    handoff = response.internal_json.handoff if isinstance(response.internal_json.handoff, dict) else {}
    handoff["needed"] = True
    handoff["reason"] = reason
    response.internal_json.handoff = handoff
    response.internal_json.state = "HANDOFF"
    response.internal_json.required_questions = []

    risk_flags = list(response.internal_json.risk_flags or [])
    if risk_flag not in risk_flags:
        risk_flags.append(risk_flag)
    response.internal_json.risk_flags = risk_flags

    escalation = response.internal_json.escalation if isinstance(response.internal_json.escalation, dict) else {}
    escalation.update(
        {
            "level": level,
            "route_to_role": route_to_role,
            "reason": reason,
            "sla_hint": sla_hint,
        }
    )
    response.internal_json.escalation = escalation
    response.internal_json.next_step = next_step


def _clean_text(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    value = _CODE_BLOCK_PATTERN.sub("", value).strip()
    value = value.replace("`", "")
    return _MULTI_EXCLAMATION_PATTERN.sub("!", value)


def _normalize_tone(text: str, language: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned

    if language == "tr":
        cleaned = _RUDE_TR_PATTERN.sub("yardimci olamam", cleaned)
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _replace_commitment_with_handoff(_text: str, language: str) -> str:
    """Replace operational commitment text with a safe handoff message.

    When the LLM promises a physical action (e.g. 'preparing your order')
    without any tool call to back it up, we replace that promise with a
    message that routes the request to the appropriate team.
    """
    return order_commitment_fallback(language)


def _contains_technical_leak(text: str) -> bool:
    """Return True when text includes a technical leak that should be blocked."""
    urls = _URL_PATTERN.findall(text)
    if not urls:
        return _TECHNICAL_LEAK_PATTERN.search(text) is not None

    if all(_is_allowed_public_location_link(url) for url in urls):
        text_without_urls = _URL_PATTERN.sub(" ", text)
        return _TECHNICAL_LEAK_PATTERN.search(text_without_urls) is not None

    return True


def _is_allowed_public_location_link(url: str) -> bool:
    """Allow only guest-facing Google Maps links in replies."""
    cleaned = url.strip().rstrip(".,);]}>\"'")
    parsed = urlsplit(cleaned)
    host = parsed.netloc.casefold().split("@")[-1].split(":", 1)[0]
    if host not in _ALLOWED_PUBLIC_LINK_HOSTS:
        return False

    if host in {"google.com", "www.google.com", "m.google.com"}:
        return parsed.path.startswith("/maps")

    return True


def _is_scope_refusal(text: str, language: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if language == "en":
        return all(token in normalized for token in _OUT_SCOPE_EN_HINTS)
    if language == "ru":
        return all(token in normalized for token in _OUT_SCOPE_RU_HINTS)
    return all(token in normalized for token in _OUT_SCOPE_TR_HINTS)
