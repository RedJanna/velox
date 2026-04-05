"""Unit tests for menu PDF import helpers."""

from velox.core.menu_pdf_importer import _default_menu_scope_prompt, _extract_items_from_lines


def test_extract_items_from_lines_reads_priced_rows() -> None:
    lines = [
        "Soup of the day 8 EUR",
        "Grilled Salmon 22.50 EUR",
        "House Wine Glass 7 EUR",
    ]

    items = _extract_items_from_lines(lines, source_label="alacarte")

    assert len(items) == 3
    assert items[0]["name"] == "Soup of the day"
    assert items[0]["price_text"] == "8 EUR"
    assert items[1]["name"] == "Grilled Salmon"


def test_extract_items_from_lines_falls_back_when_price_missing() -> None:
    lines = [
        "Fresh Garden Salad",
        "Vegetarian Bowl",
    ]

    items = _extract_items_from_lines(lines, source_label="snack")

    assert len(items) == 2
    assert items[0]["name"] == "Fresh Garden Salad"
    assert items[0]["price_text"] == ""


def test_default_menu_scope_prompt_lists_sources() -> None:
    prompt = _default_menu_scope_prompt(
        [
            "data/menus/hotel_21966/alacarte.pdf",
            "data/menus/hotel_21966/wines.pdf",
        ]
    )
    assert "RESTAURANT_MENU_STRICT_MODE" in prompt
    assert "alacarte.pdf" in prompt
    assert "wines.pdf" in prompt

