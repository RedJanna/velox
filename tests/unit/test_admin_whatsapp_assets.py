"""Smoke tests for WhatsApp admin panel assets."""

from velox.api.routes.admin_panel_ui import render_admin_panel_html
from velox.api.routes.admin_panel_whatsapp_assets import ADMIN_WHATSAPP_SCRIPT


def test_admin_panel_contains_whatsapp_api_view() -> None:
    html = render_admin_panel_html()

    assert 'data-nav="whatsappapi"' in html
    assert 'data-view="whatsappapi"' in html
    assert "whatsappConnectDialog" in html
    assert "whatsappGuideDialog" in html
    assert "WhatsApp Meta Cloud API Kurulum Rehberi" in html
    assert 'id="whatsappGuideButton" class="inline-button primary"' in html
    assert "whatsappMetaResourceSelect" in html
    assert "whatsappMetaResourceToggles" in html


def test_whatsapp_asset_normalizes_dotless_hash_alias() -> None:
    assert "whatsappapı" in ADMIN_WHATSAPP_SCRIPT
    assert "velox:whatsapp-oauth" in ADMIN_WHATSAPP_SCRIPT


def test_whatsapp_asset_picker_completes_authorized_session() -> None:
    html = render_admin_panel_html()

    assert "whatsappAssets" in html
    assert "/whatsapp/connect-sessions/' + encodeURIComponent(state.whatsappConnectSessionId) + '/complete" in (
        ADMIN_WHATSAPP_SCRIPT
    )


def test_whatsapp_guide_explains_beginner_error_prevention() -> None:
    html = render_admin_panel_html()

    assert "Başlamadan önce 5 dakikalık kontrol" in html
    assert "Hangi yolu seçmeliyim?" in html
    assert "Telefon Numarası Kimliği, görünen telefon numarası değildir" in html
    assert "whatsapp_business_management" in html
    assert "24 saatlik pencere" in html
    assert "Webhook URL'sini HTTP veya localhost olarak ayarlamak" in html
    assert "Erişim token'ı, uygulama gizli anahtarı" in html
    assert "WHATSAPP_VERIFY_TOKEN" in html
    assert "Açılır pencere açılmıyor" in html
    assert "Bittiğini nasıl anlarım?" in html
    assert "openGuideDialog" in ADMIN_WHATSAPP_SCRIPT


def test_whatsapp_meta_resource_hub_lists_required_meta_urls() -> None:
    html = render_admin_panel_html()

    assert "Meta Bilgi Merkezi" in html
    assert "renderMetaResourceHub" in ADMIN_WHATSAPP_SCRIPT
    assert "onMetaResourceSelect" in ADMIN_WHATSAPP_SCRIPT
    assert "Başlangıç ve ürün kapsamı" in ADMIN_WHATSAPP_SCRIPT
    assert "Yetki, token ve bağlantı" in ADMIN_WHATSAPP_SCRIPT
    assert "WABA, telefon ve kimlikler" in ADMIN_WHATSAPP_SCRIPT
    assert "Webhook ve mesaj gönderimi" in ADMIN_WHATSAPP_SCRIPT
    assert "Şablon ve 24 saat penceresi" in ADMIN_WHATSAPP_SCRIPT
    assert "https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started" in ADMIN_WHATSAPP_SCRIPT
    assert "https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview" in ADMIN_WHATSAPP_SCRIPT
    assert "https://developers.facebook.com/documentation/business-messaging/whatsapp/access-tokens" in ADMIN_WHATSAPP_SCRIPT
    assert "https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview" in ADMIN_WHATSAPP_SCRIPT
    assert "https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview" in ADMIN_WHATSAPP_SCRIPT
    assert "https://business.facebook.com/wa/manage/message-templates/" in ADMIN_WHATSAPP_SCRIPT
    assert "https://developers.facebook.com/tools/explorer/" in ADMIN_WHATSAPP_SCRIPT
