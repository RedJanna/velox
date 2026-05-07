"""Lightweight response validator and tone guard for guest-facing replies."""

from __future__ import annotations

import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit

from velox.core.fallback_response_library import (
    hotel_fact_conflict_fallback,
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
_STAY_LIVE_CLAIM_PATTERN = re.compile(
    r"("
    r"\b\d+(?:[.,]\d{1,2})?\s*(?:eur|€|usd|\$|gbp|£|try|tl|₺)\b|"
    r"fiyat|ücret|ucret|müsait|musait|available|availability|"
    r"room\s+(?:is\s+)?available|oda\s+(?:müsait|musait)"
    r")",
    re.IGNORECASE,
)
_STAY_LIVE_TOOL_NAMES = {"booking_availability", "booking_quote"}
_CAMPAIGN_CLAIM_MARKERS = (
    "kampanya",
    "kampanyali",
    "campaign",
    "promotion",
    "promo",
    "advert",
    "reklam",
)
_MULTI_MEAL_BOARD_CLAIM_MARKERS = (
    "2 ogun",
    "iki ogun",
    "kahvalti + aksam",
    "kahvalti ve aksam",
    "kahvalti aksam",
    "aksam yemegi dahil",
    "dinner included",
    "breakfast and dinner",
    "breakfast + dinner",
    "half board",
    "yarim pansiyon",
    "full board",
    "tam pansiyon",
    "all inclusive",
    "her sey dahil",
)
_MULTI_MEAL_BOARD_CODES = {"HB", "FB", "AI"}
_CAMPAIGN_PROFILE_KEY_MARKERS = (
    "campaign",
    "campaigns",
    "promotion",
    "promotions",
    "promo",
    "kampanya",
    "kampanyalar",
)


def validate_guest_response(
    response: LLMResponse,
    *,
    default_language: str,
    scope_decision: ScopeDecision | None = None,
    hotel_id: int | None = None,
    hotel_profile: Any | None = None,
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
    if _is_ungrounded_stay_live_claim(response, text, tool_calls):
        text = unresolved_handoff_fallback(language)
        _mark_mandatory_handoff(
            response,
            reason="ungrounded_stay_price_or_availability",
            risk_flag="UNRESOLVED_CASE",
            route_to_role="SALES",
            level="L2",
            sla_hint="high",
            next_step="handoff_to_live_price_team",
        )
        rules_applied.append("ungrounded_stay_live_claim_blocked")

    if _is_unverified_campaign_or_board_claim(
        text,
        hotel_id=hotel_id,
        hotel_profile=hotel_profile,
    ):
        profile = _resolve_hotel_profile(hotel_id, hotel_profile)
        text = hotel_fact_conflict_fallback(language, _profile_board_summary(profile, language))
        _append_profile_conflict_notification(response)
        _mark_mandatory_handoff(
            response,
            reason="guest_claim_conflicts_with_hotel_profile",
            risk_flag="DATA_INCONSISTENCY",
            route_to_role="ADMIN",
            level="L2",
            sla_hint="high",
            next_step="handoff_to_admin",
        )
        rules_applied.append("unsupported_hotel_fact_claim_blocked")

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

    # Guard: Keep menu item claims inside automation without human handoff.
    if not tool_calls and _MENU_ITEM_PATTERN.search(text):
        text = menu_not_available_fallback(language)
        response.internal_json.handoff = {"needed": False, "reason": None}
        if str(response.internal_json.state or "").upper() == "HANDOFF":
            response.internal_json.state = "ANSWERED"
        response.internal_json.escalation = {"level": "L0", "route_to_role": "NONE"}
        response.internal_json.next_step = "continue_menu_automation"
        rules_applied.append("menu_information_automation_fallback")

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


def _is_ungrounded_stay_live_claim(
    response: LLMResponse,
    text: str,
    tool_calls: list[Any],
) -> bool:
    """Return True when stay price/availability is claimed without live booking tools."""
    intent = str(response.internal_json.intent or "").strip().lower()
    if intent not in {"stay_quote", "stay_availability"}:
        return False
    if response.internal_json.required_questions:
        return False
    executed_tool_names = {
        str(item.get("tool") or item.get("name") or "").strip()
        for item in tool_calls
        if isinstance(item, dict)
    }
    if executed_tool_names.intersection(_STAY_LIVE_TOOL_NAMES):
        return False
    return _STAY_LIVE_CLAIM_PATTERN.search(text) is not None


def _clean_text(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    value = _CODE_BLOCK_PATTERN.sub("", value).strip()
    value = value.replace("`", "")
    return _MULTI_EXCLAMATION_PATTERN.sub("!", value)


def _canonical_text(value: str) -> str:
    """Normalize text for policy marker checks."""
    lowered = str(value or "").casefold().replace("ı", "i")
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    stripped = re.sub(r"[^a-z0-9]+", " ", stripped)
    return " ".join(stripped.split())


def _resolve_hotel_profile(hotel_id: int | None, hotel_profile: Any | None = None) -> Any | None:
    """Return the supplied or cached HOTEL_PROFILE without failing validation."""
    if hotel_profile is not None:
        return hotel_profile
    if hotel_id is None:
        return None
    try:
        from velox.core.hotel_profile_loader import get_profile, load_all_profiles

        profile = get_profile(int(hotel_id))
        if profile is None:
            profile = load_all_profiles().get(int(hotel_id))
        return profile
    except Exception:
        return None


def _is_unverified_campaign_or_board_claim(
    text: str,
    *,
    hotel_id: int | None,
    hotel_profile: Any | None = None,
) -> bool:
    """Detect campaign/meal-plan claims that are absent from HOTEL_PROFILE."""
    canonical = _canonical_text(text)
    if not canonical:
        return False

    claims_campaign = any(marker in canonical for marker in _CAMPAIGN_CLAIM_MARKERS)
    claims_multi_meal_board = any(marker in canonical for marker in _MULTI_MEAL_BOARD_CLAIM_MARKERS)
    if not claims_campaign and not claims_multi_meal_board:
        return False

    profile = _resolve_hotel_profile(hotel_id, hotel_profile)
    if profile is None:
        return True

    if claims_multi_meal_board and not _profile_allows_multi_meal_board(profile):
        return True
    if claims_campaign and not _profile_has_campaign_context(profile):
        return True
    return False


def _profile_allows_multi_meal_board(profile: Any) -> bool:
    """Return True when HOTEL_PROFILE defines a board type beyond bed and breakfast."""
    for board in getattr(profile, "board_types", []) or []:
        code = str(getattr(board, "code", "") or "").strip().upper()
        if code in _MULTI_MEAL_BOARD_CODES:
            return True
        name = getattr(board, "name", None)
        name_text = " ".join(
            str(getattr(name, attr, "") or "")
            for attr in ("tr", "en")
            if getattr(name, attr, "")
        )
        canonical_name = _canonical_text(name_text)
        if any(marker in canonical_name for marker in _MULTI_MEAL_BOARD_CLAIM_MARKERS):
            return True
    return False


def _profile_has_campaign_context(profile: Any) -> bool:
    """Return True only when HOTEL_PROFILE explicitly carries campaign/promotion fields."""
    try:
        payload = profile.model_dump(mode="json")
    except Exception:
        payload = getattr(profile, "model_extra", None) or {}
    return _contains_campaign_key(payload)


def _contains_campaign_key(value: Any) -> bool:
    """Scan profile keys, not guest text, for explicit campaign configuration."""
    if isinstance(value, dict):
        for key, nested in value.items():
            canonical_key = _canonical_text(str(key))
            if any(marker in canonical_key for marker in _CAMPAIGN_PROFILE_KEY_MARKERS):
                return True
            if _contains_campaign_key(nested):
                return True
    if isinstance(value, list):
        return any(_contains_campaign_key(item) for item in value)
    return False


def _profile_board_summary(profile: Any | None, language: str) -> str:
    """Build a short guest-safe summary of configured board types."""
    if profile is None:
        return ""
    names: list[str] = []
    for board in getattr(profile, "board_types", []) or []:
        name = getattr(board, "name", None)
        preferred = str(getattr(name, language, "") or "").strip() if name is not None else ""
        fallback = str(getattr(name, "tr", "") or getattr(name, "en", "") or "").strip() if name is not None else ""
        code = str(getattr(board, "code", "") or "").strip()
        label = preferred or fallback or code
        if label and label not in names:
            names.append(label)
    return ", ".join(names[:3])


def _append_profile_conflict_notification(response: LLMResponse) -> None:
    """Add an admin-visible note for profile/source conflicts without exposing PII."""
    notifications = list(response.internal_json.notifications or [])
    notifications.append(
        {
            "channel": "panel",
            "to_role": "ADMIN",
            "message": (
                "Misafir kampanya/pansiyon/ogun iddiasi kaynak verilerle dogrulanamadi. "
                "Otel profili esas alindi ve insan devrine yonlendirildi."
            ),
        }
    )
    response.internal_json.notifications = notifications


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
