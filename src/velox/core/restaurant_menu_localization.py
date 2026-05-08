"""Customer-facing localization helpers for restaurant menu content."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import orjson

PUBLIC_ORDER_LANGUAGE_CODES = ("tr", "en", "de", "ru", "ar", "fr", "nl", "es")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _translation_key(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


@lru_cache(maxsize=32)
def load_ingredient_translations(hotel_id: int) -> dict[str, dict[str, str]]:
    """Load optional ingredient translations for one hotel catalog."""
    path = _repo_root() / "data" / "restaurant_ai" / f"hotel_{hotel_id}" / "ingredient_translations.json"
    if not path.exists():
        return {}
    raw = orjson.loads(path.read_bytes())
    translations = raw.get("translations") if isinstance(raw, dict) else None
    if not isinstance(translations, dict):
        return {}
    normalized: dict[str, dict[str, str]] = {}
    for ingredient, values in translations.items():
        if not isinstance(values, dict):
            continue
        localized = {str(lang): str(text).strip() for lang, text in values.items() if str(text).strip()}
        if localized:
            normalized[_translation_key(ingredient)] = localized
    return normalized


def localize_ingredients(
    hotel_id: int,
    ingredients: list[Any],
    *,
    language_codes: tuple[str, ...] = PUBLIC_ORDER_LANGUAGE_CODES,
) -> dict[str, list[str]]:
    """Return customer-facing ingredient labels for each public order language."""
    cleaned = [str(item).strip() for item in ingredients if str(item).strip()]
    translations = load_ingredient_translations(hotel_id)
    localized_by_language: dict[str, list[str]] = {}
    for language_code in language_codes:
        rows: list[str] = []
        for ingredient in cleaned:
            key = _translation_key(ingredient)
            rows.append(
                ingredient
                if language_code == "en"
                else translations.get(key, {}).get(language_code, ingredient)
            )
        localized_by_language[language_code] = rows
    return localized_by_language
