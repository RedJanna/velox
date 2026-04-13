"""Unit tests for readiness dependency checks."""

from __future__ import annotations

import pytest

from velox.api.routes import health


@pytest.mark.asyncio
async def test_check_elektraweb_generic_sync_accepts_login_token_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health.settings, "elektra_generic_api_base_url", "https://4001.hoteladvisor.net")
    monkeypatch.setattr(health.settings, "elektra_generic_login_token", "token-only")
    monkeypatch.setattr(health.settings, "elektra_generic_tenant", "")
    monkeypatch.setattr(health.settings, "elektra_generic_usercode", "")
    monkeypatch.setattr(health.settings, "elektra_generic_password", "")

    result = await health.check_elektraweb_generic_sync()

    assert result["ok"] is True
    assert result["detail"] == "elektraweb_generic_override_only"
    assert result["mode"] == "override_token"
    assert result["has_login_token_override"] is True
    assert result["missing_fields"] == ["tenant", "usercode", "password"]


@pytest.mark.asyncio
async def test_check_elektraweb_generic_sync_accepts_permanent_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health.settings, "elektra_generic_api_base_url", "https://4001.hoteladvisor.net")
    monkeypatch.setattr(health.settings, "elektra_generic_login_token", "")
    monkeypatch.setattr(health.settings, "elektra_generic_tenant", "21966")
    monkeypatch.setattr(health.settings, "elektra_generic_usercode", "ops-user")
    monkeypatch.setattr(health.settings, "elektra_generic_password", "ops-pass")

    result = await health.check_elektraweb_generic_sync()

    assert result["ok"] is True
    assert result["detail"] == "elektraweb_generic_credentials_configured"
    assert result["has_login_token_override"] is False
