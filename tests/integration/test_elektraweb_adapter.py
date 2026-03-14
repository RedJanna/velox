"""Integration tests for Elektraweb adapter with mocked HTTP responses."""

from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest

from velox.adapters.elektraweb import client as client_module
from velox.adapters.elektraweb import endpoints
from velox.adapters.elektraweb.client import ElektrawebClient
from velox.adapters.elektraweb.mapper import parse_reservation_create


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
async def test_quote_sends_child_alias_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quote request should send Elektra's child occupancy aliases and buckets."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {
            "id": "of1",
            "room-type-id": 66,
            "board-type-id": 2,
            "rate-type-id": 10,
            "rate-code-id": 101,
            "price-agency-id": 1,
            "currency": "EUR",
            "price": "120.0",
            "discounted-price": "100.0",
            "pax-count": {
                "adult": 2,
                "elder-child-count": 1,
                "younger-child-count": 1,
                "baby-count": 0,
            },
            "cancellation-penalty": {},
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 7, 1),
        checkout=date(2026, 7, 5),
        adults=2,
        chd_ages=[10, 3],
        currency="EUR",
        nationality="TR",
    )

    _, kwargs = mock_client.get.await_args
    params = kwargs["params"]
    assert params["childage"] == "10,3"
    assert params["child-age"] == "10,3"
    assert params["child-ages"] == "10,3"
    assert params["child"] == 2
    assert params["child-count"] == 2
    assert params["children-count"] == 2
    assert params["elder-child-count"] == 1
    assert params["younger-child-count"] == 1
    assert params["baby-count"] == 0


@pytest.mark.asyncio
async def test_quote_parses_live_room_and_rate_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live Elektra list responses should preserve room/rate labels used by quote formatting."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {
            "room-type-id": 396094,
            "room-type": "DELUXE",
            "board-type-id": 44512,
            "board-type": "Kahvaltı Dahil",
            "rate-type-id": 24178,
            "rate-type": "Ücretsiz İptal",
            "RATECODEID": 183666,
            "currency": "EUR",
            "price": "546.7",
            "room-area": 25,
            "cancel-possible": True,
            "pax-count": {
                "adult": 1,
                "elder-child-count": 1,
                "younger-child-count": 0,
                "baby-count": 0,
            },
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    result = await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 8, 3),
        checkout=date(2026, 8, 5),
        adults=1,
        chd_ages=[8],
    )

    assert result.offers[0].room_type == "DELUXE"
    assert result.offers[0].rate_type == "Ücretsiz İptal"
    assert result.offers[0].rate_code_id == 183666
    assert result.offers[0].room_area == 25
    assert result.offers[0].cancel_possible is True


@pytest.mark.asyncio
async def test_quote_normalizes_teen_children_into_adults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Teen ages should be normalized to adults for PMS quote compatibility."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {
            "id": "of1",
            "room-type-id": 66,
            "board-type-id": 2,
            "rate-type-id": 10,
            "rate-code-id": 101,
            "price-agency-id": 1,
            "currency": "EUR",
            "price": "220.0",
            "discounted-price": "200.0",
            "pax-count": {
                "adult": 4,
                "elder-child-count": 0,
                "younger-child-count": 0,
                "baby-count": 0,
            },
            "cancellation-penalty": {},
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    result = await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 8, 20),
        checkout=date(2026, 8, 22),
        adults=2,
        chd_ages=[15, 13],
        currency="EUR",
        nationality="TR",
    )

    assert len(result.offers) == 1
    _, kwargs = mock_client.get.await_args
    params = kwargs["params"]
    assert params["adult"] == 4
    assert "chdCount" not in params
    assert "childage" not in params


@pytest.mark.asyncio
async def test_quote_raises_when_child_occupancy_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """Child quote requests must fail if PMS returns adult-only occupancy."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {
            "id": "of1",
            "room-type-id": 66,
            "board-type-id": 2,
            "rate-type-id": 10,
            "rate-code-id": 101,
            "price-agency-id": 1,
            "currency": "EUR",
            "price": "120.0",
            "discounted-price": "100.0",
            "pax-count": {
                "adult": 2,
                "elder-child-count": 0,
                "younger-child-count": 0,
                "baby-count": 0,
            },
            "cancellation-penalty": {},
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    with pytest.raises(RuntimeError, match="CHILD_OCCUPANCY_UNVERIFIED"):
        await endpoints.quote(
            hotel_id=21966,
            checkin=date(2026, 8, 10),
            checkout=date(2026, 8, 12),
            adults=2,
            chd_ages=[7],
        )


@pytest.mark.asyncio
async def test_quote_raises_when_child_buckets_do_not_match(monkeypatch: pytest.MonkeyPatch) -> None:
    """Child quote requests must fail when PMS echoes wrong younger/elder buckets."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {
            "id": "of1",
            "room-type-id": 66,
            "board-type-id": 2,
            "rate-type-id": 10,
            "rate-code-id": 101,
            "price-agency-id": 1,
            "currency": "EUR",
            "price": "120.0",
            "discounted-price": "100.0",
            "pax-count": {
                "adult": 2,
                "elder-child-count": 0,
                "younger-child-count": 2,
                "baby-count": 0,
            },
            "cancellation-penalty": {},
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    with pytest.raises(RuntimeError, match="CHILD_OCCUPANCY_UNVERIFIED"):
        await endpoints.quote(
            hotel_id=21966,
            checkin=date(2026, 7, 1),
            checkout=date(2026, 7, 5),
            adults=2,
            chd_ages=[10, 3],
        )


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
    http.request.side_effect = [_response(500, {"detail": "err"})] * 6
    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=http))
    monkeypatch.setattr(client, "_get_token", AsyncMock(return_value="tok"))
    monkeypatch.setattr(client_module.asyncio, "sleep", AsyncMock())
    with pytest.raises(httpx.HTTPStatusError):
        await client.request("GET", "/hotel/21966/availability")


def test_parse_reservation_create_supports_hoteladvisor_primary_key() -> None:
    """HOTEL_RES insert response should map PrimaryKey to reservation_id."""
    parsed = parse_reservation_create(
        {
            "Success": True,
            "PrimaryKey": 89985306,
            "Row": {"ID": 89985306},
            "Message": "OK",
        }
    )
    assert parsed.reservation_id == "89985306"
    assert parsed.state == "OK"
