"""Unit tests for admin debug scan registry selection."""

from velox.core.admin_debug_scan_registry import build_scan_targets
from velox.models.admin_debug import DebugRunScope


def test_build_scan_targets_respects_current_view() -> None:
    scope = DebugRunScope(target="current_view", target_view="chatlab")

    targets = build_scan_targets(scope, hotel_id=21966)

    assert targets
    assert all(target.view_key == "chatlab" for target in targets)
    assert {target.key for target in targets} >= {"chatlab_shell", "chatlab_live_feed", "chatlab_templates"}


def test_build_scan_targets_skips_chatlab_when_disabled() -> None:
    scope = DebugRunScope(target="all_panel", include_chatlab_iframe=False)

    targets = build_scan_targets(scope, hotel_id=21966)

    assert not any(target.view_key == "chatlab" for target in targets)
