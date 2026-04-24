"""Unit tests for signed admin debug sessions."""

from __future__ import annotations

from uuid import uuid4

import pytest

from velox.config.settings import settings
from velox.utils.admin_debug_security import create_debug_session_token, decode_debug_session_token


def test_debug_session_token_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = uuid4()
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")

    token = create_debug_session_token(
        run_id=run_id,
        hotel_id=21966,
        triggered_by_user_id=42,
    )
    payload = decode_debug_session_token(token)

    assert payload.run_id == run_id
    assert payload.hotel_id == 21966
    assert payload.triggered_by_user_id == 42
    assert payload.report_only is True
    assert payload.role.value == "ADMIN"


def test_debug_session_token_rejects_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")

    with pytest.raises(ValueError):
        decode_debug_session_token("not-a-valid-token")
