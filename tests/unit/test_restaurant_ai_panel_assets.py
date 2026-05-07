"""Unit tests for Restaurant AI admin panel assets."""

from velox.api.routes.admin_panel_restaurant_ai_assets import ADMIN_RESTAURANT_AI_SCRIPT, ADMIN_RESTAURANT_AI_STYLE
from velox.api.routes.admin_panel_ui import render_admin_panel_html


def test_restaurant_ai_panel_is_rendered_in_admin_ui() -> None:
    html = render_admin_panel_html()

    assert 'data-view="restaurantai"' in html
    assert "Restaurant AI / Menü Asistanı" in html
    assert "restaurantAiCatalogToggle" in html
    assert "restaurantAiQrForm" in html
    assert 'id="restaurantAiCatalogContent" hidden' in html
    assert "restaurantAiCatalogTableBody" in html
    assert "restaurantAiTestForm" in html
    assert "Menü dışı öneri engeli: HER ZAMAN AÇIK" in html


def test_restaurant_ai_assets_call_expected_admin_endpoints() -> None:
    assert "/restaurant-ai/catalog" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/waiters" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/orders" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/off-menu-requests" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/test-console" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/table-order-link" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/catalog/items" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "/restaurant-ai/catalog/items/${encodeURIComponent(menuItemId)}/content" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "setRestaurantAiCatalogExpanded" in ADMIN_RESTAURANT_AI_SCRIPT


def test_restaurant_ai_panel_can_manage_product_contents() -> None:
    html = render_admin_panel_html()

    assert "İçindekiler" in html
    assert "restaurantAiIngredients" in ADMIN_RESTAURANT_AI_SCRIPT
    assert "data-restaurant-ai-item-content" in ADMIN_RESTAURANT_AI_SCRIPT
    assert ".restaurant-ai-summary" in ADMIN_RESTAURANT_AI_STYLE
