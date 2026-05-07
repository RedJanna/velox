"""Unit tests for Restaurant AI menu assistant safeguards."""

from __future__ import annotations

from velox.core.restaurant_ai_menu import load_default_menu_catalog, run_test_console


def test_default_menu_catalog_loads_kassandra_items() -> None:
    payload = load_default_menu_catalog(21966)

    assert payload is not None
    assert len(payload.items) > 50
    assert any(item.menu_item_id == "kr_snack_pizza_margherita" for item in payload.items)


def test_margarita_cocktail_is_not_confused_with_margherita_pizza() -> None:
    payload = load_default_menu_catalog(21966)
    assert payload is not None

    result = run_test_console(question="Bana margarita cocktail yapar mısınız?", catalog_items=payload.items)

    assert result["detected_intent"] == "off_menu_request"
    assert result["off_menu_risk"] is True
    matched_ids = {item["menu_item_id"] for item in result["matched_menu_items"]}
    assert "kr_snack_pizza_margherita" not in matched_ids
    assert "Mojito" in result["generated_answer"]
    assert result["validator"]["passed"] is True


def test_sushi_request_gets_catalog_only_seafood_alternatives() -> None:
    payload = load_default_menu_catalog(21966)
    assert payload is not None

    result = run_test_console(question="Sushi var mı?", catalog_items=payload.items)

    assert result["detected_intent"] == "off_menu_request"
    assert result["off_menu_risk"] is True
    assert "Sushi" not in result["generated_answer"]
    assert "Grilled Sea Bass" in result["generated_answer"] or "Izgara Levrek" in result["generated_answer"]
    assert result["validator"]["passed"] is True


def test_mixed_off_menu_request_validates_answer_matches() -> None:
    payload = load_default_menu_catalog(21966)
    assert payload is not None

    result = run_test_console(
        question="Sushi var mı? Margarita cocktail isterim",
        catalog_items=payload.items,
        venue="Kassandra Restaurant",
    )

    matched_names = {item["name_en"] for item in result["matched_menu_items"]}
    assert result["off_menu_risk"] is True
    assert result["validator"]["passed"] is True
    assert "Grilled Sea Bass" in result["generated_answer"] or "Izgara Levrek" in result["generated_answer"]
    assert "Grilled Sea Bass" in matched_names
