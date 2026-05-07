"""Deterministic helpers for the Restaurant AI menu assistant panel."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any
from unicodedata import combining, normalize

import orjson

from velox.models.restaurant_ai import RestaurantAiMenuItem

DEFAULT_OFF_MENU_RESPONSE = (
    "Bu ürün mevcut menümüzde görünmüyor. Menüdeki alternatiflerden isterseniz size uygun seçenekleri "
    "listeleyebilirim."
)
DEFAULT_ORDER_CONFIRMATION_MESSAGE = (
    "Sipariş özetinizi hazırladım. Onaylıyor musunuz? Onayınızdan sonra sipariş ekibe iletilecektir."
)
DEFAULT_WHATSAPP_NOTIFICATION_TEMPLATE = (
    "Yeni Sipariş - {venue}\n\nMasa/Oda: {table_or_room}\nMisafir: {guest_name}\n"
    "Sipariş:\n{items}\n\nToplam: {total_try} TL\n\nNot: {customer_note}\nAlerji: {allergy_note}"
)
DEFAULT_ALLERGY_WARNING_TEXT = (
    "Alerji veya özel beslenme tercihiniz varsa lütfen ekibimize ayrıca iletin; içerik bilgisi personel "
    "tarafından teyit edilmelidir."
)

OFF_MENU_KEYWORDS = {
    "lahmacun",
    "sushi",
    "margarita",
    "ramen",
    "taco",
    "burrito",
    "künefe",
    "kunefe",
}

INTENT_KEYWORDS: dict[str, set[str]] = {
    "order_request": {"istiyorum", "sipariş", "siparis", "getir", "alabilir miyim", "adet", "order"},
    "price_inquiry": {"kaç tl", "kac tl", "fiyat", "price", "how much", "ücreti", "ucreti"},
    "recommendation_request": {"öner", "oner", "tavsiye", "hafif", "ne yiyebilirim", "recommend"},
    "allergy_inquiry": {"alerji", "allergy", "gluten", "laktoz", "vegan", "vejetaryen"},
    "menu_inquiry": {"menü", "menu", "var mı", "var mi", "içecek", "icecek", "yemek"},
}

RECOMMENDATION_RULES: tuple[tuple[set[str], dict[str, set[str]]], ...] = (
    ({"hafif", "light"}, {"tags": {"light_candidate"}, "categories": {"Salads", "Starters", "Power Bowls"}}),
    ({"deniz", "balık", "balik", "seafood", "fish"}, {"tags": {"seafood"}, "categories": {"Seafood", "Hot Starters"}}),
    ({"çocuk", "cocuk", "kids", "child"}, {"categories": {"Children's Menu"}}),
    ({"vegan"}, {"tags": {"vegan"}}),
    ({"tatlı", "tatli", "dessert"}, {"categories": {"Desserts"}}),
    ({"kokteyl", "cocktail"}, {"categories": {"Cocktails", "Classic Cocktails"}}),
    ({"alkolsüz", "alkolsuz", "non alcoholic"}, {"categories": {"Mocktails", "Soft Drinks"}}),
    ({"şarap", "sarap", "wine"}, {"menu_types": {"Wine List"}}),
)


@dataclass(frozen=True)
class CatalogPayload:
    """Parsed default menu catalog file."""

    source_path: Path
    source_label: str
    checksum: str
    items: list[RestaurantAiMenuItem]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def normalize_text(value: object) -> str:
    """Normalize menu/search text without locale-specific surprises."""
    text = str(value or "").strip().lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = "".join(char for char in normalize("NFKD", text) if not combining(char))
    return " ".join(text.split())


def catalog_checksum(items: Sequence[RestaurantAiMenuItem]) -> str:
    """Return a stable checksum for one catalog item sequence."""
    payload = [item.model_dump(mode="json") for item in sorted(items, key=lambda item: item.menu_item_id)]
    return sha256(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)).hexdigest()


def load_default_menu_catalog(hotel_id: int) -> CatalogPayload | None:
    """Load the repository menu_catalog.json for one hotel if it exists."""
    path = _repo_root() / "data" / "restaurant_ai" / f"hotel_{hotel_id}" / "menu_catalog.json"
    if not path.exists():
        return None
    raw = orjson.loads(path.read_bytes())
    raw_items = raw.get("items") if isinstance(raw, dict) else None
    if not isinstance(raw_items, list):
        raise ValueError("menu_catalog.json items listesi eksik.")
    items = [RestaurantAiMenuItem.model_validate(_normalize_raw_item(item)) for item in raw_items]
    source_label = str(raw.get("source_label") or path.name) if isinstance(raw, dict) else path.name
    checksum = str(raw.get("checksum") or catalog_checksum(items)) if isinstance(raw, dict) else catalog_checksum(items)
    return CatalogPayload(source_path=path, source_label=source_label, checksum=checksum, items=items)


def filter_catalog_items(
    items: Iterable[RestaurantAiMenuItem],
    *,
    search: str | None = None,
    category: str | None = None,
    venue: str | None = None,
    menu_type: str | None = None,
    status: str | None = None,
) -> list[RestaurantAiMenuItem]:
    """Apply panel filters to catalog items."""
    search_key = normalize_text(search)
    category_key = normalize_text(category)
    venue_key = normalize_text(venue)
    menu_type_key = normalize_text(menu_type)
    status_key = normalize_text(status)
    filtered: list[RestaurantAiMenuItem] = []
    for item in items:
        haystack = normalize_text(
            " ".join(
                [
                    item.name_en,
                    item.name_tr or "",
                    item.category,
                    item.venue,
                    item.menu_type,
                    " ".join(item.tags),
                ]
            )
        )
        if search_key and search_key not in haystack:
            continue
        if category_key and normalize_text(item.category) != category_key:
            continue
        if venue_key and normalize_text(item.venue) != venue_key:
            continue
        if menu_type_key and normalize_text(item.menu_type) != menu_type_key:
            continue
        if status_key and normalize_text(item.status) != status_key:
            continue
        filtered.append(item)
    return filtered


def build_price_conflicts(items: Sequence[RestaurantAiMenuItem]) -> list[dict[str, Any]]:
    """Group same-name items with different prices within venue + menu_type."""
    groups: dict[tuple[str, str, str], list[RestaurantAiMenuItem]] = {}
    for item in items:
        key = (normalize_text(item.name_en or item.name_tr), normalize_text(item.venue), normalize_text(item.menu_type))
        groups.setdefault(key, []).append(item)

    conflicts: list[dict[str, Any]] = []
    for (_name_key, _venue_key, _menu_type_key), grouped in groups.items():
        prices = {str(item.price_try) for item in grouped if item.price_try is not None}
        if len(prices) <= 1:
            continue
        first = grouped[0]
        conflicts.append(
            {
                "venue": first.venue,
                "menu_type": first.menu_type,
                "name": first.name_en,
                "prices": sorted(prices),
                "items": [item.model_dump(mode="json") for item in grouped],
            }
        )
    return conflicts


def categories_for_catalog(items: Sequence[RestaurantAiMenuItem]) -> list[str]:
    """Return stable category options."""
    return sorted({item.category for item in items if item.category})


def venues_for_catalog(items: Sequence[RestaurantAiMenuItem]) -> list[str]:
    """Return stable venue options."""
    return sorted({item.venue for item in items if item.venue})


def menu_types_for_catalog(items: Sequence[RestaurantAiMenuItem]) -> list[str]:
    """Return stable menu type options."""
    return sorted({item.menu_type for item in items if item.menu_type})


def run_test_console(
    *,
    question: str,
    catalog_items: Sequence[RestaurantAiMenuItem],
    settings: dict[str, Any] | None = None,
    venue: str | None = None,
    menu_type: str | None = None,
) -> dict[str, Any]:
    """Run a deterministic menu-bound test for the admin panel."""
    scoped_items = [
        item
        for item in catalog_items
        if item.status == "active"
        and (not venue or normalize_text(item.venue) == normalize_text(venue))
        and (not menu_type or normalize_text(item.menu_type) == normalize_text(menu_type))
    ]
    intent = detect_intent(question)
    matches = match_menu_items(question, scoped_items, intent=intent)
    off_menu_risk = detect_off_menu_risk(question, matches, intent)
    answer_matches = list(matches)
    if off_menu_risk:
        answer_matches = safe_alternatives(question, scoped_items) or answer_matches
    generated_answer = build_menu_bound_answer(
        question=question,
        intent=intent,
        matches=answer_matches,
        all_items=scoped_items,
        off_menu_risk=off_menu_risk,
        settings=settings or {},
    )
    validator = validate_menu_bound_answer(generated_answer, answer_matches, scoped_items, off_menu_risk)
    return {
        "detected_intent": intent,
        "matched_menu_items": [item.model_dump(mode="json") for item in answer_matches[:8]],
        "generated_answer": generated_answer,
        "off_menu_risk": off_menu_risk,
        "validator": validator,
    }


def detect_intent(question: str) -> str:
    """Detect a coarse restaurant assistant intent."""
    normalized = normalize_text(question)
    if any(keyword in normalized for keyword in OFF_MENU_KEYWORDS):
        return "off_menu_request"
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return intent
    return "menu_inquiry"


def match_menu_items(
    question: str,
    items: Sequence[RestaurantAiMenuItem],
    *,
    intent: str,
    limit: int = 8,
) -> list[RestaurantAiMenuItem]:
    """Return menu items that can be grounded to the question."""
    normalized = normalize_text(question)
    tokens = {token for token in normalized.split() if len(token) >= 3}
    scored: list[tuple[int, RestaurantAiMenuItem]] = []
    for item in items:
        names = [item.name_en, item.name_tr or ""]
        item_text = normalize_text(" ".join([*names, item.category, item.menu_type, " ".join(item.tags)]))
        name_text = normalize_text(" ".join(names))
        item_tokens = {token for token in item_text.split() if len(token) >= 3}
        score = 0
        if name_text and name_text in normalized:
            score += 8
        if normalize_text(item.name_en) in normalized:
            score += 8
        if item.name_tr and normalize_text(item.name_tr) in normalized:
            score += 8
        score += len(tokens & item_tokens)
        if score:
            scored.append((score, item))

    if scored:
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].price_try or ""), pair[1].name_en))
        return [item for _score, item in scored[:limit]]

    return recommendation_matches(normalized, items, intent=intent, limit=limit)


def recommendation_matches(
    normalized_question: str,
    items: Sequence[RestaurantAiMenuItem],
    *,
    intent: str,
    limit: int,
) -> list[RestaurantAiMenuItem]:
    """Fallback to controlled recommendation categories."""
    if intent not in {"recommendation_request", "menu_inquiry", "price_inquiry"}:
        return []
    for keywords, filters in RECOMMENDATION_RULES:
        if not any(keyword in normalized_question for keyword in keywords):
            continue
        tags = {normalize_text(item) for item in filters.get("tags", set())}
        categories = {normalize_text(item) for item in filters.get("categories", set())}
        menu_types = {normalize_text(item) for item in filters.get("menu_types", set())}
        matches = [
            item
            for item in items
            if (tags and tags.intersection({normalize_text(tag) for tag in item.tags + item.dietary_tags}))
            or (categories and normalize_text(item.category) in categories)
            or (menu_types and normalize_text(item.menu_type) in menu_types)
        ]
        if matches:
            return matches[:limit]
    return []


def detect_off_menu_risk(question: str, matches: Sequence[RestaurantAiMenuItem], intent: str) -> bool:
    """Return whether the test question risks menu-boundary drift."""
    normalized = normalize_text(question)
    if any(keyword in normalized for keyword in OFF_MENU_KEYWORDS):
        return True
    return intent in {"order_request", "price_inquiry", "menu_inquiry"} and not matches


def build_menu_bound_answer(
    *,
    question: str,
    intent: str,
    matches: Sequence[RestaurantAiMenuItem],
    all_items: Sequence[RestaurantAiMenuItem],
    off_menu_risk: bool,
    settings: dict[str, Any],
) -> str:
    """Build a short panel preview answer using only catalog items."""
    if off_menu_risk:
        alternatives = list(matches) or safe_alternatives(question, all_items)
        base = str(settings.get("off_menu_response") or DEFAULT_OFF_MENU_RESPONSE)
        if alternatives:
            return f"{base}\n\nMenüdeki uygun alternatifler:\n{format_item_lines(alternatives[:6])}"
        return base

    if not matches:
        return "Bu soru için katalogda net eşleşme bulamadım. Net ürün veya kategori sorarak ilerlemek gerekir."

    if intent == "order_request":
        confirmation = str(settings.get("order_confirmation_message") or DEFAULT_ORDER_CONFIRMATION_MESSAGE)
        return f"{format_item_lines(matches[:5])}\n\n{confirmation}"

    if intent == "allergy_inquiry":
        allergy = str(settings.get("allergy_warning_text") or DEFAULT_ALLERGY_WARNING_TEXT)
        return f"Menüde buna yakın seçenekler:\n{format_item_lines(matches[:5])}\n\n{allergy}"

    return f"Menümüzde buna uygun seçenekler:\n{format_item_lines(matches[:5])}\n\nSipariş vermek ister misiniz?"


def safe_alternatives(question: str, items: Sequence[RestaurantAiMenuItem]) -> list[RestaurantAiMenuItem]:
    """Return catalog-only alternatives for known off-menu asks."""
    normalized = normalize_text(question)
    if "sushi" in normalized:
        return [
            item
            for item in items
            if "seafood" in {normalize_text(tag) for tag in item.tags} or normalize_text(item.category) == "seafood"
        ][:8]
    if "margarita" in normalized:
        cocktails = [item for item in items if normalize_text(item.category) in {"classic cocktails", "cocktails"}]
        cocktails.sort(key=lambda item: (normalize_text(item.category) != "classic cocktails", item.name_en))
        return cocktails[:8]
    if "lahmacun" in normalized:
        return [item for item in items if normalize_text(item.category) in {"pizzas", "burgers & wraps", "snacks"}][:8]
    return items[:5]


def format_item_lines(items: Sequence[RestaurantAiMenuItem]) -> str:
    """Format catalog items for preview output."""
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        price = format_price_try(item.price_try)
        name = item.name_tr or item.name_en
        suffix = f" - {price}" if price else ""
        description = item.description_tr or item.description_en
        if description:
            lines.append(f"{index}. {name}{suffix}\n{description}")
        else:
            lines.append(f"{index}. {name}{suffix}")
    return "\n".join(lines)


def format_price_try(value: Decimal | None) -> str:
    """Format TRY prices without inventing missing values."""
    if value is None:
        return ""
    if value == value.to_integral_value():
        return f"{int(value)} TL"
    return f"{value} TL"


def validate_menu_bound_answer(
    generated_answer: str,
    matched_items: Sequence[RestaurantAiMenuItem],
    all_items: Sequence[RestaurantAiMenuItem],
    off_menu_risk: bool,
) -> dict[str, Any]:
    """Validate that preview output stays inside the matched catalog rows."""
    catalog_names = {normalize_text(item.name_en) for item in all_items} | {
        normalize_text(item.name_tr) for item in all_items if item.name_tr
    }
    matched_names = {normalize_text(item.name_en) for item in matched_items} | {
        normalize_text(item.name_tr) for item in matched_items if item.name_tr
    }
    answer = normalize_text(generated_answer)
    off_menu_mentions = sorted(
        keyword for keyword in OFF_MENU_KEYWORDS if keyword in answer and keyword not in catalog_names
    )
    if off_menu_mentions and not off_menu_risk:
        return {
            "passed": False,
            "result": "failed",
            "reason": "Yanıtta menü dışı ürün riski var.",
            "off_menu_mentions": off_menu_mentions,
        }
    if matched_items:
        missing = [name for name in matched_names if name and name not in answer]
        if len(missing) == len(matched_names):
            return {
                "passed": False,
                "result": "failed",
                "reason": "Eşleşen katalog ürünleri cevapta görünmüyor.",
                "off_menu_mentions": off_menu_mentions,
            }
    return {
        "passed": True,
        "result": "passed",
        "reason": "Cevap katalog sınırı içinde kaldı.",
        "off_menu_mentions": off_menu_mentions,
    }


def _normalize_raw_item(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Her katalog kalemi JSON nesnesi olmalı.")
    item = dict(raw)
    item["menu_item_id"] = str(item.get("menu_item_id") or item.get("id") or "").strip()
    item["raw_json"] = dict(raw)
    if "tags" not in item:
        item["tags"] = list(item.get("dietary_tags") or [])
    return item
