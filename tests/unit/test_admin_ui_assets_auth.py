"""Regression checks for admin panel and Chat Lab inline scripts."""

from velox.api.routes.admin_panel_ui import render_admin_panel_html
from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT, ADMIN_PANEL_STYLE
from velox.api.routes.test_chat_ui_assets import TEST_CHAT_SCRIPT


def test_admin_panel_notifications_use_notify_helper() -> None:
    assert "toast(" not in ADMIN_PANEL_SCRIPT
    assert "notify(" in ADMIN_PANEL_SCRIPT


def test_chat_lab_boot_no_longer_requires_parent_token() -> None:
    assert "window.parent !== window && !adminToken()) return;" not in TEST_CHAT_SCRIPT


def test_chat_lab_does_not_persist_admin_token_in_localstorage() -> None:
    assert "localStorage.setItem" not in TEST_CHAT_SCRIPT


def test_admin_panel_shared_label_helper_avoids_broken_regex_escape() -> None:
    assert "findExplicitLabel(" in ADMIN_PANEL_SCRIPT
    assert "var safeId =" not in ADMIN_PANEL_SCRIPT
    assert "replace(/\\/g" not in ADMIN_PANEL_SCRIPT


def test_admin_auth_forms_do_not_fallback_to_get_submission() -> None:
    html = render_admin_panel_html()
    assert '<form id="loginForm" class="field-grid" method="post">' in html
    assert '<form id="bootstrapForm" class="field-grid mt-md" method="post">' in html
    assert '<form id="totpRecoveryForm" class="field-grid" method="post">' in html
    assert '<form id="otpVerifyForm" class="field-grid mt-md" method="post" hidden>' in html


def test_hold_rows_are_clickable_without_detail_button() -> None:
    """Hold table rows should be directly clickable for selection."""
    assert '.holds-table tbody tr[data-open-hold]{cursor:pointer}' in ADMIN_PANEL_STYLE
    assert 'data-open-hold="${escapeHtml(item.hold_id)}"' in ADMIN_PANEL_SCRIPT
