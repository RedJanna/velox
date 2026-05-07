"""Config loader for the public restaurant ordering panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


DEFAULT_SUPPORTED_LANGUAGES = [
    {"code": "tr", "label": "Türkçe"},
    {"code": "en", "label": "English"},
    {"code": "de", "label": "Deutsch"},
    {"code": "ru", "label": "Русский"},
    {"code": "ar", "label": "العربية"},
    {"code": "fr", "label": "Français"},
    {"code": "nl", "label": "Nederlands"},
    {"code": "es", "label": "Español"},
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_public_order_config(hotel_id: int) -> dict[str, Any]:
    """Load public order config from data/restaurant_ai/hotel_{id}."""
    path = _repo_root() / "data" / "restaurant_ai" / f"hotel_{hotel_id}" / "public_order_config.json"
    if path.exists():
        raw = orjson.loads(path.read_bytes())
        return raw if isinstance(raw, dict) else {}
    return {}


def public_order_payload(hotel_id: int) -> dict[str, Any]:
    """Return normalized public order config payload."""
    config = load_public_order_config(hotel_id)
    languages = config.get("supported_languages")
    if not isinstance(languages, list) or not languages:
        languages = DEFAULT_SUPPORTED_LANGUAGES
    pdf_menus = config.get("pdf_menus")
    if not isinstance(pdf_menus, dict):
        pdf_menus = {}
    meal_periods = config.get("meal_periods")
    if not isinstance(meal_periods, dict):
        meal_periods = {
            "breakfast": {"enabled": True, "pdf_keys": []},
            "lunch": {"enabled": True, "pdf_keys": ["snack", "alacarte", "wine"]},
            "dinner": {"enabled": True, "pdf_keys": ["alacarte", "wine"]},
        }
    breakfast_items = config.get("breakfast_items")
    if not isinstance(breakfast_items, list):
        breakfast_items = []
    return {
        "enabled": bool(config.get("enabled", True)),
        "supported_languages": languages,
        "default_language": str(config.get("default_language") or "tr"),
        "currency": "TRY",
        "pdf_menus": pdf_menus,
        "meal_periods": meal_periods,
        "breakfast_items": breakfast_items,
    }
