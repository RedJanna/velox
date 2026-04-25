"""Smoke tests for WhatsApp admin panel assets."""

from velox.api.routes.admin_panel_ui import render_admin_panel_html
from velox.api.routes.admin_panel_whatsapp_assets import ADMIN_WHATSAPP_SCRIPT


def test_admin_panel_contains_whatsapp_api_view() -> None:
    html = render_admin_panel_html()

    assert 'data-nav="whatsappapi"' in html
    assert 'data-view="whatsappapi"' in html
    assert "whatsappConnectDialog" in html


def test_whatsapp_asset_normalizes_dotless_hash_alias() -> None:
    assert "whatsappapı" in ADMIN_WHATSAPP_SCRIPT
    assert "velox:whatsapp-oauth" in ADMIN_WHATSAPP_SCRIPT


def test_whatsapp_asset_picker_completes_authorized_session() -> None:
    html = render_admin_panel_html()

    assert "whatsappAssets" in html
    assert "/whatsapp/connect-sessions/' + encodeURIComponent(state.whatsappConnectSessionId) + '/complete" in (
        ADMIN_WHATSAPP_SCRIPT
    )
