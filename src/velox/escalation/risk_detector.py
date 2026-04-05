"""Risk flag detection from LLM output and user message analysis."""

import re

import structlog

from velox.config.constants import RiskFlag
from velox.models.conversation import InternalJSON

logger = structlog.get_logger(__name__)

RISK_PATTERNS: dict[RiskFlag, list[re.Pattern[str]]] = {
    RiskFlag.LEGAL_REQUEST: [
        re.compile(
            r"\b(avukat|lawyer|dava|lawsuit|mahkeme|court|hukuk|legal|savc[ıi]|prosecutor)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.SECURITY_INCIDENT: [
        re.compile(
            r"\b(h[ıi]rs[ıi]z|thief|stolen|cald[ıi]|robbery|g[uü]venlik\s*ihlal|security\s*breach|break.?in)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.THREAT_SELF_HARM: [
        re.compile(
            r"\b(intihar|suicide|kendime\s*zarar|self.?harm|[oö]lmek\s*ist|want\s*to\s*die)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.MEDICAL_EMERGENCY: [
        re.compile(
            (
                r"\b(ambulans|ambulance|acil\s*t[ıi]bbi|emergency\s*medical|kalp\s*krizi|heart\s*attack|"
                r"bayıld[ıi]|fainted|kan[ıi]yor|bleeding|zehirlen|poisoning)\b"
            ),
            re.IGNORECASE,
        ),
    ],
    RiskFlag.ANGRY_COMPLAINT: [
        re.compile(
            (
                r"\b(rezalet|disgrace|utan[ıi]n|shame\s*on|berbat|terrible|asla\s*gelmem|never\s*come\s*back|"
                r"[şs]ikayet\s*edece[gğ]im|will\s*complain)\b"
            ),
            re.IGNORECASE,
        ),
    ],
    RiskFlag.PAYMENT_CONFUSION: [
        re.compile(
            r"\b([oö]deme.*anla[sş]am|payment.*confus|nereye.*[oö]de|where.*pay|fazla.*[cç]ek|overcharge)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.CHARGEBACK_MENTION: [
        re.compile(
            r"\b(chargeback|itiraz|dispute|banka.*iade|bank.*refund|kart.*iade|card.*dispute)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.REFUND_DISPUTE: [
        re.compile(
            r"\b(iade.*iste|refund.*request|param[ıi].*geri|money\s*back|iade.*yap[ıi]lmad|refund.*not.*processed)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.HARASSMENT_HATE: [
        re.compile(
            r"\b(taciz|harassment|tehdit|threat|k[uü]f[uü]r|profanity|ırk[cç]|racist)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.FRAUD_SIGNAL: [
        re.compile(
            r"\b(sahte|fake|doland[ıi]r|fraud|scam|ka[cç]ak|illegal)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.GROUP_BOOKING: [
        re.compile(r"\b(grup|group|(\d{2,})\s*(ki[sş]i|person|people|pax))\b", re.IGNORECASE),
    ],
    RiskFlag.SPECIAL_EVENT: [
        re.compile(
            (
                r"\b(d[oö][gğ]um\s*g[uü]n[uü]|birthday|balayı|honeymoon|y[ıi]ld[oö]n[uü]m[uü]|anniversary|"
                r"evlilik\s*teklifi|proposal|organizasyon|event)\b"
            ),
            re.IGNORECASE,
        ),
    ],
    RiskFlag.ALLERGY_ALERT: [
        re.compile(
            (
                r"\b(alerji|allergy|allergic|gl[uü]ten|lakto|lactose|f[ıi]st[ıi]k|peanut|yumurta\s*alerji|"
                r"egg\s*allergy|[cç][oö]lyak|celiac|vegan|vegetarian|vejetaryen|vejeteryan)\b"
            ),
            re.IGNORECASE,
        ),
    ],
    RiskFlag.PHYSICAL_OPERATION_REQUEST: [
        re.compile(
            (
                r"\b(sipari[sş]|order|room\s*service|oda\s*servis[i]?)\b"
            ),
            re.IGNORECASE,
        ),
        re.compile(
            r"(istiyorum|g[oö]nder|odama|odamıza|hazırla|hazirla|getir|deliver|prepare|servis\s*yap|g[oö]nderilsin)",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.MENU_HALLUCINATION_RISK: [
        re.compile(
            (
                r"\b(men[uü]|menu|yemek\s*listesi|ne\s*var|neler\s*var|yemek\s*[oö]ner|"
                r"tatl[ıi]\s*[cç]e[sş]it|i[cç]ecek\s*listesi|food\s*list|dish|course)\b"
            ),
            re.IGNORECASE,
        ),
    ],
    RiskFlag.ACCESSIBILITY_NEED: [
        re.compile(
            r"\b(engelli|disabled|tekerlekli\s*sandalye|wheelchair|eri[sş]ilebilir|accessible|asans[oö]r|elevator)\b",
            re.IGNORECASE,
        ),
    ],
    RiskFlag.VIP_REQUEST: [
        re.compile(
            (
                r"\b(vip|[oö]zel\s*kar[sş][ıi]lama|special\s*welcome|s[uü]rpriz|surprise|[oö]zel\s*istek|"
                r"special\s*request)\b"
            ),
            re.IGNORECASE,
        ),
    ],
    RiskFlag.LOST_ITEM: [
        re.compile(
            r"\b(kay[ıi]p|lost|unuttum|forgot|b[ıi]rakt[ıi]m|left\s*behind|e[sş]ya|belongings|item)\b",
            re.IGNORECASE,
        ),
    ],
}


def detect_risk_flags_from_message(user_message: str) -> list[RiskFlag]:
    """Scan user message text and return detected risk flags."""
    detected: list[RiskFlag] = []
    for flag, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(user_message):
                detected.append(flag)
                break
    return detected


def detect_risk_flags_from_internal_json(internal_json: InternalJSON) -> list[RiskFlag]:
    """Extract valid RiskFlag values from INTERNAL_JSON.risk_flags."""
    detected: list[RiskFlag] = []
    for flag_str in internal_json.risk_flags:
        try:
            detected.append(RiskFlag(flag_str))
        except ValueError:
            logger.warning("unknown_risk_flag_from_internal_json", risk_flag=flag_str)
    return detected


def detect_all_risk_flags(user_message: str, internal_json: InternalJSON) -> list[RiskFlag]:
    """Merge risk flags from LLM output and message pattern detection."""
    from_message = detect_risk_flags_from_message(user_message)
    from_llm = detect_risk_flags_from_internal_json(internal_json)
    seen: set[RiskFlag] = set()
    merged: list[RiskFlag] = []
    for flag in from_llm + from_message:
        if flag not in seen:
            seen.add(flag)
            merged.append(flag)
    return merged
