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
async def test_quote_parses_wrapped_list_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quote parser should accept client-wrapped list payload under 'data'."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "data": [
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
async def test_availability_parses_wrapped_list_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Availability parser should accept client-wrapped list payload under 'data'."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "data": [
            {"date": "2026-08-10", "room-type-id": 66, "room-to-sell": 3},
            {"date": "2026-08-11", "room-type-id": 66, "room-to-sell": 2},
        ]
    }
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    result = await endpoints.availability(
        hotel_id=21966,
        checkin=date(2026, 8, 10),
        checkout=date(2026, 8, 12),
        adults=2,
    )
    assert result.available is True
    assert len(result.rows) == 2


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
async def test_quote_allows_when_child_total_matches_but_buckets_differ(monkeypatch: pytest.MonkeyPatch) -> None:
    """Child quote should continue when PMS total child occupancy matches."""
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
    result = await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 7, 1),
        checkout=date(2026, 7, 5),
        adults=2,
        chd_ages=[10, 3],
    )
    assert len(result.offers) == 1


@pytest.mark.asyncio
async def test_quote_accepts_child_count_without_bucket_breakdown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Child quote should accept pax_count child_count even when bucket fields are absent."""
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
                "child-count": 2,
            },
            "cancellation-penalty": {},
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    result = await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 7, 1),
        checkout=date(2026, 7, 5),
        adults=2,
        chd_ages=[10, 3],
    )
    assert len(result.offers) == 1


@pytest.mark.asyncio
async def test_quote_accepts_child_age_reclassification_when_total_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Child quote should continue when PMS shifts one child into adult bucket but total pax matches."""
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
                "adult": 3,
                "elder-child-count": 1,
                "younger-child-count": 0,
                "baby-count": 0,
            },
            "cancellation-penalty": {},
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    result = await endpoints.quote(
        hotel_id=21966,
        checkin=date(2026, 10, 1),
        checkout=date(2026, 10, 6),
        adults=2,
        chd_ages=[12, 11],
    )
    assert len(result.offers) == 1


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


@pytest.mark.asyncio
async def test_create_reservation_uses_booking_api_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Create reservation should send mapped booking API fields instead of raw snake_case draft."""
    mock_client = AsyncMock()
    mock_client.post.return_value = {"reservation-id": "RSV-1", "voucher-no": "V-1"}
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    draft = {
        "guest_name": "Test User",
        "phone": "+905301112233",
        "checkin_date": "2026-10-01",
        "checkout_date": "2026-10-03",
        "adults": 2,
        "chd_ages": [],
        "room_type_id": 396097,
        "board_type_id": 2,
        "rate_type_id": 11,
        "rate_code_id": 102,
        "price_agency_id": 777,
        "total_price_eur": "140.0",
        "currency_display": "EUR",
    }

    result = await endpoints.create_reservation(21966, draft)

    assert result.reservation_id == "RSV-1"
    assert result.voucher_no == "V-1"
    path = mock_client.post.await_args.kwargs["json_body"]
    assert path["hotel-id"] == 21966
    assert path["room-type-id"] == 396097
    assert path["adult-count"] == 2
    assert path["check-in"] == "2026-10-01"
    assert len(path["guest-list"]) == 2


@pytest.mark.asyncio
async def test_get_reservation_uses_reservation_list_window_and_filters_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reservation lookup should use reservation-list with bounded window and id filter."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {
            "reservation-id": "RSV-88",
            "voucher-no": "V-88",
            "price": "140.0",
            "status": "CONFIRMED",
        }
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    result = await endpoints.get_reservation(hotel_id=21966, reservation_id="RSV-88")

    assert result.success is True
    assert result.reservation_id == "RSV-88"
    assert result.voucher_no == "V-88"
    _, kwargs = mock_client.get.await_args
    assert kwargs["params"]["reservation-id"] == "RSV-88"
    assert "from-check-in" in kwargs["params"]
    assert "to-check-in" in kwargs["params"]


@pytest.mark.asyncio
async def test_get_reservation_falls_back_when_reservation_list_has_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lookup should continue to secondary paths when reservation-list misses the reservation."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = [[], {"success": True, "reservation_id": "RSV-99", "voucher_no": "V-99"}]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    result = await endpoints.get_reservation(hotel_id=21966, reservation_id="RSV-99")

    assert result.reservation_id == "RSV-99"
    assert mock_client.get.await_count == 2


@pytest.mark.asyncio
async def test_request_does_not_failover_to_secondary_base_on_400(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation 400 responses should surface directly instead of trying another host."""
    client = ElektrawebClient()
    client._base_urls = ["https://primary.example", "https://secondary.example"]
    http = AsyncMock()
    http.request.side_effect = [_response(400, {"detail": "bad-request"})]
    monkeypatch.setattr(client, "_get_client", AsyncMock(return_value=http))
    monkeypatch.setattr(client, "_get_token", AsyncMock(return_value="tok"))
    monkeypatch.setattr(client, "_switch_base_url", AsyncMock())

    with pytest.raises(httpx.HTTPStatusError):
        await client.request("POST", "/hotel/21966/createReservation", json_body={"hotel-id": 21966})

    assert http.request.await_count == 1


@pytest.mark.asyncio
async def test_create_reservation_retries_with_refreshed_offer_on_agency_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Agency drift should trigger a fresh quote-based retry before surfacing the error."""
    mock_client = AsyncMock()
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    agency_error = httpx.HTTPStatusError(
        "agency-not-found",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "Agency Not Found"},
            request=request,
        ),
    )
    mock_client.post.side_effect = [agency_error, {"reservation-id": "RSV-2"}]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(
        endpoints,
        "_refresh_offer_identifiers",
        AsyncMock(
            return_value={
                "guest_name": "Test User",
                "phone": "+905301112233",
                "checkin_date": "2026-10-01",
                "checkout_date": "2026-10-03",
                "adults": 2,
                "chd_ages": [],
                "room_type_id": 396097,
                "board_type_id": 44512,
                "rate_type_id": 24171,
                "rate_code_id": 183666,
                "price_agency_id": 247664,
                "total_price_eur": "140.0",
                "currency_display": "EUR",
                "cancel_policy_type": "NON_REFUNDABLE",
            }
        ),
    )

    result = await endpoints.create_reservation(
        21966,
        {
            "guest_name": "Test User",
            "phone": "+905301112233",
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-03",
            "adults": 2,
            "chd_ages": [],
            "room_type_id": 396097,
            "board_type_id": 2,
            "rate_type_id": 11,
            "rate_code_id": 102,
            "price_agency_id": 777,
            "total_price_eur": "140.0",
            "currency_display": "EUR",
            "cancel_policy_type": "NON_REFUNDABLE",
        },
    )

    assert result.reservation_id == "RSV-2"
    refreshed_payload = mock_client.post.await_args_list[1].kwargs["json_body"]
    assert refreshed_payload["price-agency-id"] == 247664
    assert refreshed_payload["board-type-id"] == 44512
