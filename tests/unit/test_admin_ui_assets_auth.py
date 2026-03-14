"""Regression checks for admin panel and Chat Lab inline scripts."""

from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT
from velox.api.routes.test_chat_ui_assets import TEST_CHAT_SCRIPT


def test_admin_panel_notifications_use_notify_helper() -> None:
    assert "toast(" not in ADMIN_PANEL_SCRIPT
    assert "notify(" in ADMIN_PANEL_SCRIPT


def test_chat_lab_boot_no_longer_requires_parent_token() -> None:
    assert "window.parent !== window && !adminToken()) return;" not in TEST_CHAT_SCRIPT


def test_chat_lab_does_not_persist_admin_token_in_localstorage() -> None:
    assert "localStorage.setItem" not in TEST_CHAT_SCRIPT
