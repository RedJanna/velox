"""Integration tests for Elektraweb adapter with mocked HTTP responses."""

from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest

from velox.adapters.elektraweb import client as client_module
from velox.adapters.elektraweb import endpoints
from velox.adapters.elektraweb.client import ElektrawebClient


def _response(status_code: int, payload: dict) -> httpx.Response:
    """Build an httpx response with request context for raise_for_status."""
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.Response(status_code=status_code, json=payload, request=request)


@pytest.mark.asyncio
async def test_successful_availability_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Availability endpoint should parse successful adapter response."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "available": True,
        "rows": [{"date": "2026-08-10", "room-type-id": 66, "room-to-sell": 3}],
    }
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    result = await endpoints.availability(
        hotel_id=21966,
        checkin=date(2026, 8, 10),
        checkout=date(2026, 8, 12),
        adults=2,
    )
    assert result.available is True
    assert result.rows[0].room_type_id == 66


@pytest.mark.asyncio
async def test_successful_quote_with_offers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quote endpoint should parse offer list correctly."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "offers": [
            {
                "id": "of1",
                "room-type-id": 66,
                "board-type-id": 2,
                "rate-type-id": 10,
                "rate-code-id": 101,
                "price-agency-id": 1,
                "currency-code": "EUR",
                "price": "120.0",
                "discounted-price": "100.0",
                "cancellation-penalty": {},
            }
        ]
    }
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    result = await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 8, 10),
        checkout=date(2026, 8, 12),
        adults=2,
    )
    assert len(result.offers) == 1
    assert result.offers[0].room_type_id == 66


@pytest.mark.asyncio
async def test_auth_token_refresh_on_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """Client should refresh token when first response is 401."""
    client = ElektrawebClient()
    http = AsyncMock()
    http.request.side_effect = [_response(401, {"detail": "unauthorized"}), _response(200, {"ok": True})]
    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=http))
    token_mock = AsyncMock(side_effect=["tok1", "tok2"])
    monkeypatch.setattr(client, "_get_token", token_mock)
    result = await client.request("GET", "/hotel/21966/availability")
    assert result == {"ok": True}
    assert token_mock.await_count == 2


@pytest.mark.asyncio
async def test_retry_logic_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeout should retry and eventually return successful payload."""
    client = ElektrawebClient()
    http = AsyncMock()
    http.request.side_effect = [httpx.TimeoutException("timeout"), _response(200, {"ok": True})]
    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=http))
    monkeypatch.setattr(client, "_get_token", AsyncMock(return_value="tok"))
    sleep_mock = AsyncMock()
    monkeypatch.setattr(client_module.asyncio, "sleep", sleep_mock)
    result = await client.request("GET", "/hotel/21966/availability")
    assert result == {"ok": True}
    sleep_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_error_handling_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """Server-side 500 responses should retry and then raise."""
    client = ElektrawebClient()
    http = AsyncMock()
    http.request.side_effect = [_response(500, {"detail": "err"})] * 3
    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=http))
    monkeypatch.setattr(client, "_get_token", AsyncMock(return_value="tok"))
    monkeypatch.setattr(client_module.asyncio, "sleep", AsyncMock())
    with pytest.raises(httpx.HTTPStatusError):
        await client.request("GET", "/hotel/21966/availability")
