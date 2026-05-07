"""Unit tests for public restaurant ordering helpers and assets."""

from velox.api.routes.public_restaurant_order_assets import (
    PUBLIC_RESTAURANT_ORDER_SCRIPT,
    PUBLIC_RESTAURANT_ORDER_STYLE,
)
from velox.core.restaurant_order_tokens import create_table_order_token, verify_table_order_token
from velox.core.restaurant_public_order_config import public_order_payload


def test_table_order_token_round_trip() -> None:
    token = create_table_order_token(hotel_id=21966, venue="Kassandra Restaurant", table_no="12")

    payload = verify_table_order_token(token)

    assert payload is not None
    assert payload.hotel_id == 21966
    assert payload.venue == "Kassandra Restaurant"
    assert payload.table_no == "12"


def test_table_order_token_rejects_tampering() -> None:
    token = create_table_order_token(hotel_id=21966, venue="Kassandra Restaurant", table_no="12")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    assert verify_table_order_token(tampered) is None


def test_public_order_config_uses_customer_pdf_urls() -> None:
    payload = public_order_payload(21966)

    assert payload["currency"] == "TRY"
    assert payload["pdf_menus"]["alacarte"]["url"].startswith("https://kassandrarestaurant.com/")
    assert payload["pdf_menus"]["snack"]["url"].startswith("https://kassandrarestaurant.com/")
    assert payload["pdf_menus"]["wine"]["url"].startswith("https://kassandrarestaurant.com/")
    assert len(payload["breakfast_items"]) == 2


def test_public_order_script_has_no_ai_recommendation_entrypoint() -> None:
    lowered = PUBLIC_RESTAURANT_ORDER_SCRIPT.lower()

    assert "ai ile yemek önerisi" not in lowered
    assert "recommendation" not in lowered
    assert "/api/v1/public/restaurant-order/orders" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "customer_confirmation_count:2" in PUBLIC_RESTAURANT_ORDER_SCRIPT


def test_public_order_script_has_copy_for_supported_languages() -> None:
    payload = public_order_payload(21966)

    for language in payload["supported_languages"]:
        assert f"{language['code']}:{{" in PUBLIC_RESTAURANT_ORDER_SCRIPT


def test_public_order_script_has_tokenless_entry_screen() -> None:
    assert "state.step='entry'" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "renderEntry()" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "Siparişe başlamak için masa QR kodunu okutun" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "Siparişe devam et" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "QR kodu veya size gönderilen kod" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "Sipariş bağlantısını aç" not in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "Sipariş bağlantısı oluştur" not in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "linkLabel:'Sipariş bağlantısı'" not in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "Geçerli bir QR kodu, bağlantı veya imzalı token girin." in PUBLIC_RESTAURANT_ORDER_SCRIPT


def test_public_order_script_renders_error_before_loading_state() -> None:
    render_start = PUBLIC_RESTAURANT_ORDER_SCRIPT.index("function render(){")
    render_end = PUBLIC_RESTAURANT_ORDER_SCRIPT.index("function renderLanguage()")
    render_source = PUBLIC_RESTAURANT_ORDER_SCRIPT[render_start:render_end]

    assert render_source.index("if(state.error)") < render_source.index("if(state.step==='loading')")


def test_public_order_redesign_assets_include_customer_browsing_ui() -> None:
    assert "#192f9a" in PUBLIC_RESTAURANT_ORDER_STYLE
    assert "brand-logo" in PUBLIC_RESTAURANT_ORDER_STYLE
    assert "order-category-rail" in PUBLIC_RESTAURANT_ORDER_STYLE
    assert "sticky-cart" in PUBLIC_RESTAURANT_ORDER_STYLE
    assert "id=\"menuSearch\"" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "data-cat" in PUBLIC_RESTAURANT_ORDER_SCRIPT
    assert "brandLogoConfig" in PUBLIC_RESTAURANT_ORDER_SCRIPT
