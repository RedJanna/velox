"""FAQ lookup tool based on HOTEL_PROFILE FAQ data."""

from difflib import SequenceMatcher
from typing import Any

from velox.core.hotel_profile_loader import get_profile
from velox.tools.base import BaseTool


def _similarity(left: str, right: str) -> float:
    """Return similarity ratio in [0, 1]."""
    return SequenceMatcher(a=left.lower(), b=right.lower()).ratio()


class FAQLookupTool(BaseTool):
    """Find FAQ entry by topic/query with fuzzy fallback."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "query", "language"])
        hotel_id = int(kwargs["hotel_id"])
        query = str(kwargs["query"]).strip()
        language = str(kwargs["language"]).upper()

        profile = get_profile(hotel_id)
        if profile is None:
            return {"found": False}

        faq_data = profile.faq_data
        if not faq_data:
            return {"found": False}

        best_item: dict[str, Any] | None = None
        best_score = 0.0
        for entry in faq_data:
            topic = str(entry.get("topic", ""))
            answer_tr = str(entry.get("answer_tr", ""))
            answer_en = str(entry.get("answer_en", ""))

            score = max(
                _similarity(query, topic),
                _similarity(query, answer_tr[:120]),
                _similarity(query, answer_en[:120]),
            )
            if score > best_score:
                best_score = score
                best_item = entry

            if topic.lower() == query.lower():
                best_item = entry
                best_score = 1.0
                break

        if best_item is None or best_score < 0.35:
            return {"found": False}

        return {
            "found": True,
            "topic": str(best_item.get("topic", "")),
            "answer_tr": str(best_item.get("answer_tr", "")),
            "answer_en": str(best_item.get("answer_en", "")),
            "answer": str(best_item.get("answer_tr", ""))
            if language == "TR"
            else str(best_item.get("answer_en", "")),
            "source": "HOTEL_PROFILE.faq_data",
            "match_score": round(best_score, 3),
        }
