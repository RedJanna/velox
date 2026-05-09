"""Deterministic trigger matching for structured hotel information."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from velox.models.hotel_information import HotelInformationDataset, HotelInformationEntry

_CHAR_NORMALIZATION_TABLE = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "Ş": "s",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
)
_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_TRIGGER_MATCH_THRESHOLD = 0.42
_STOPWORDS = {
    "acaba",
    "bir",
    "bu",
    "icin",
    "ile",
    "mi",
    "mu",
    "musunuz",
    "midir",
    "nedir",
    "ne",
    "var",
    "yok",
}

_PRODUCT_DETAIL_TERMS = (
    "ezine",
    "kasar",
    "peynir",
    "portakal suyu",
    "taze portakal",
    "kirmizi tursu biber",
    "tursu biber",
    "minibar",
    "mini bar",
    "marka urun",
    "hangi urun",
    "urun detayi",
)
_PRODUCT_DETAIL_CUES = (
    "hangi",
    "neler",
    "ne var",
    "var mi",
    "cesit",
    "cesitleri",
    "icerik",
    "marka",
    "urun",
)
_BEACH_TERMS = ("plaj", "sahil", "deniz", "belcekiz")
_BEACH_DISTANCE_TERMS = ("mesafe", "uzak", "kac metre", "kac dakika", "yurume", "yakın", "yakin")


@dataclass(frozen=True)
class HotelInformationMatch:
    """Matched hotel information entry and its confidence score."""

    entry: HotelInformationEntry
    score: float
    match_type: str
    matched_trigger: str | None = None


def match_hotel_information(
    dataset: HotelInformationDataset,
    query: str,
) -> HotelInformationMatch | None:
    """Return the best structured hotel-information match for a guest query."""
    normalized_query = normalize_text(query)
    if not normalized_query:
        return None

    special_match = _match_special_rules(dataset, normalized_query)
    if special_match is not None:
        return special_match

    query_tokens = _tokens(normalized_query)
    best_entry: HotelInformationEntry | None = None
    best_score = 0.0
    best_trigger: str | None = None

    for entry in dataset.hotel_information:
        score, trigger = _score_entry(entry, normalized_query, query_tokens)
        if score > best_score:
            best_entry = entry
            best_score = score
            best_trigger = trigger

    if best_entry is None or best_score < _TRIGGER_MATCH_THRESHOLD:
        return None

    return HotelInformationMatch(
        entry=best_entry,
        score=round(best_score, 3),
        match_type="trigger",
        matched_trigger=best_trigger,
    )


def normalize_text(value: str) -> str:
    """Normalize Turkish text for deterministic matching."""
    folded = str(value or "").casefold().translate(_CHAR_NORMALIZATION_TABLE)
    decomposed = unicodedata.normalize("NFKD", folded)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    stripped = re.sub(r"[^a-z0-9]+", " ", stripped)
    return " ".join(stripped.split())


def _match_special_rules(
    dataset: HotelInformationDataset,
    normalized_query: str,
) -> HotelInformationMatch | None:
    """Apply high-priority deterministic business rules before fuzzy scoring."""
    if _is_product_detail_query(normalized_query):
        return _match_entry_id(dataset, "product_detail_handoff_rule", "product_detail_rule")

    if _mentions_kumburnu_gate_distance(normalized_query):
        return _match_entry_id(dataset, "kumburnu_gate_distance", "kumburnu_gate_rule")

    if _mentions_room_door_system(normalized_query):
        return _match_entry_id(dataset, "room_door_lock_system", "room_door_rule")

    if _mentions_room_electricity_card(normalized_query):
        return _match_entry_id(dataset, "room_electricity_card_system", "room_electricity_rule")

    if _mentions_breakfast_service(normalized_query):
        return _match_entry_id(dataset, "breakfast_service_type", "breakfast_service_rule")

    if _mentions_general_beach_distance(normalized_query):
        return _match_entry_id(dataset, "belcekiz_beach_distance", "general_beach_rule")

    return None


def _match_entry_id(
    dataset: HotelInformationDataset,
    entry_id: str,
    match_type: str,
) -> HotelInformationMatch | None:
    entry = dataset.entry_by_id(entry_id)
    if entry is None:
        return None
    return HotelInformationMatch(entry=entry, score=1.0, match_type=match_type)


def _is_product_detail_query(normalized_query: str) -> bool:
    if any(term in normalized_query for term in _PRODUCT_DETAIL_TERMS):
        return True

    has_detail_cue = any(cue in normalized_query for cue in _PRODUCT_DETAIL_CUES)
    if not has_detail_cue:
        return False

    asks_breakfast_item = "kahvalti" in normalized_query and any(
        cue in normalized_query for cue in ("hangi", "ne var", "var mi", "cesit", "urun")
    )
    asks_minibar_item = ("minibar" in normalized_query or "mini bar" in normalized_query) and has_detail_cue
    asks_room_product = "oda" in normalized_query and "urun" in normalized_query
    asks_brand_detail = "marka" in normalized_query
    return asks_breakfast_item or asks_minibar_item or asks_room_product or asks_brand_detail


def _mentions_kumburnu_gate_distance(normalized_query: str) -> bool:
    return "kumburnu" in normalized_query and any(
        token in normalized_query
        for token in ("gise", "gisesi", "kac dakika", "ne kadar", "uzak", "ulasim")
    )


def _mentions_general_beach_distance(normalized_query: str) -> bool:
    return any(term in normalized_query for term in _BEACH_TERMS) and any(
        term in normalized_query for term in _BEACH_DISTANCE_TERMS
    )


def _mentions_room_door_system(normalized_query: str) -> bool:
    return any(term in normalized_query for term in ("kapi", "kilit", "anahtar")) and any(
        term in normalized_query for term in ("kart", "kartli", "anahtar", "kilit")
    )


def _mentions_room_electricity_card(normalized_query: str) -> bool:
    return any(term in normalized_query for term in ("elektrik", "enerji", "cihaz", "klima")) and any(
        term in normalized_query for term in ("kart", "karti", "cikarinca", "kesiliyor")
    )


def _mentions_breakfast_service(normalized_query: str) -> bool:
    if "kahvalti" not in normalized_query:
        return False
    return any(
        term in normalized_query
        for term in ("acik bufe", "servis", "nasil", "dahil", "var mi")
    )


def _score_entry(
    entry: HotelInformationEntry,
    normalized_query: str,
    query_tokens: set[str],
) -> tuple[float, str | None]:
    candidates = [
        entry.id.replace("_", " "),
        entry.category,
        entry.title_tr,
        *entry.trigger_examples,
    ]
    best_score = 0.0
    best_trigger: str | None = None

    for candidate in candidates:
        normalized_candidate = normalize_text(candidate)
        if not normalized_candidate:
            continue

        score = _score_candidate(normalized_query, query_tokens, normalized_candidate)
        if score > best_score:
            best_score = score
            best_trigger = candidate

    return best_score, best_trigger


def _score_candidate(
    normalized_query: str,
    query_tokens: set[str],
    normalized_candidate: str,
) -> float:
    if normalized_query == normalized_candidate:
        return 1.0
    if normalized_candidate in normalized_query or normalized_query in normalized_candidate:
        return 0.92

    candidate_tokens = _tokens(normalized_candidate)
    if not candidate_tokens:
        return 0.0

    overlap = query_tokens.intersection(candidate_tokens)
    if not overlap:
        sequence_ratio = SequenceMatcher(a=normalized_query, b=normalized_candidate).ratio()
        return sequence_ratio * 0.8 if sequence_ratio >= 0.75 else 0.0

    overlap_ratio = len(overlap) / len(candidate_tokens)
    query_coverage = len(overlap) / max(len(query_tokens), 1)
    sequence_ratio = SequenceMatcher(a=normalized_query, b=normalized_candidate).ratio()
    return max((overlap_ratio * 0.7) + (query_coverage * 0.3), sequence_ratio * 0.8)


def _tokens(normalized_value: str) -> set[str]:
    return {
        match.group(0)
        for match in _WORD_PATTERN.finditer(normalized_value)
        if len(match.group(0)) > 1 and match.group(0) not in _STOPWORDS
    }
