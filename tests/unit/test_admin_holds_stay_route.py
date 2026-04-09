"""Regression tests for admin stay-holds listing route."""

from __future__ import annotations

from typing import Any

import pytest

from velox.api.middleware.auth import TokenData
from velox.api.routes import admin_holds
from velox.config.constants import Role


def _admin_user() -> TokenData:
    return TokenData(
        user_id=1,
        hotel_id=21966,
        username="admin",
        role=Role.ADMIN,
        display_name="Admin",
    )


@pytest.mark.asyncio
async def test_list_stay_holds_count_query_uses_stay_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    """Count query must keep the `sh` alias because archived clause references it."""
    observed: dict[str, Any] = {}

    async def _fake_fetch(_query: str, *_args: object) -> list[dict[str, Any]]:
        return []

    async def _fake_fetchval(query: str, *_args: object) -> int:
        observed["query"] = query
        return 0

    monkeypatch.setattr(admin_holds, "fetch", _fake_fetch)
    monkeypatch.setattr(admin_holds, "fetchval", _fake_fetchval)

    result = await admin_holds.list_stay_holds(
        user=_admin_user(),
        hotel_id=21966,
        status=None,
        reservation_no=None,
        archived=False,
        page=1,
        per_page=30,
    )

    assert result["total"] == 0
    assert "FROM stay_holds sh" in str(observed.get("query", ""))

