"""FAQ lookup tool based on HOTEL_PROFILE FAQ data."""

import unicodedata
from difflib import SequenceMatcher
from typing import Any

from velox.config.constants import SUPPORTED_LANGUAGES
from velox.core.hotel_profile_loader import get_profile
from velox.models.hotel_profile import FAQEntry, FAQStatus
from velox.tools.base import BaseTool

_CHAR_NORMALIZATION_TABLE = str.maketrans(
    {
        "ı": "i",
        "ß": "ss",
    }
)


def _normalize_text(value: str) -> str:
    """Normalize text for resilient FAQ matching across punctuation and accents."""
    folded = value.casefold().translate(_CHAR_NORMALIZATION_TABLE).strip()
    decomposed = unicodedata.normalize("NFKD", folded)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(stripped.split())


def _similarity(left: str, right: str) -> float:
    """Return similarity ratio in [0, 1]."""
    return SequenceMatcher(a=_normalize_text(left), b=_normalize_text(right)).ratio()


def _deduplicate_preserving_order(items: list[str]) -> list[str]:
    """Return unique strings without changing their original order."""
    unique_items: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = _normalize_text(item)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_items.append(item)
    return unique_items


def _question_candidates(entry: FAQEntry, language: str) -> list[str]:
    """Return ordered question candidates, prioritising the active language."""
    language_code = language.casefold()
    prioritized_languages = [language_code]
    for fallback_language in ("en", "tr"):
        if fallback_language not in prioritized_languages:
            prioritized_languages.append(fallback_language)
    prioritized_languages.extend(
        supported_language
        for supported_language in SUPPORTED_LANGUAGES
        if supported_language not in prioritized_languages
    )

    ordered_candidates: list[str] = []
    for candidate_language in prioritized_languages:
        ordered_candidates.extend(entry.question_candidates_for_language(candidate_language))
    ordered_candidates.append(entry.topic)
    return _deduplicate_preserving_order(ordered_candidates)


class FAQLookupTool(BaseTool):
    """Find FAQ entry by topic/query with fuzzy fallback."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "query", "language"])
        hotel_id = int(kwargs["hotel_id"])
        query = str(kwargs["query"]).strip()
        language = str(kwargs["language"]).strip()

        profile = get_profile(hotel_id)
        if profile is None:
            return {"found": False}

        faq_data = profile.faq_data
        if not faq_data:
            return {"found": False}

        best_item: FAQEntry | None = None
        best_score = 0.0
        for entry in faq_data:
            if entry.status != FAQStatus.ACTIVE:
                continue
            candidates = _question_candidates(entry, language)
            answer_tr = entry.answer_tr
            answer_en = entry.answer_en

            if any(_normalize_text(candidate) == _normalize_text(query) for candidate in candidates):
                best_item = entry
                best_score = 1.0
                break

            score = max(
                *(_similarity(query, candidate) for candidate in candidates),
                _similarity(query, answer_tr[:120]),
                _similarity(query, answer_en[:120]),
            )
            if score > best_score:
                best_score = score
                best_item = entry

        if best_item is None or best_score < 0.35:
            return {"found": False}

        return {
            "found": True,
            "faq_id": best_item.faq_id,
            "topic": best_item.topic,
            "answer_tr": best_item.answer_tr,
            "answer_en": best_item.answer_en,
            "answer": best_item.answer_tr
            if language.casefold() == "tr"
            else best_item.answer_en,
            "source": "HOTEL_PROFILE.faq_data",
            "match_score": round(best_score, 3),
        }
