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
            "room-to-sell": 3,
            "rate-rules": {"stop-sell": False},
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
    assert result.offers[0].room_to_sell == 3
    assert result.offers[0].stop_sell is False
    assert result.offers[0].pax_adult_count == 1
    assert result.offers[0].pax_child_count == 1
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
async def test_availability_normalizes_teen_children_into_adults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Availability should mirror quote occupancy normalization for teen children."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "available": True,
        "rows": [{"date": "2026-08-20", "room-type-id": 66, "room-to-sell": 2}],
    }
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)

    result = await endpoints.availability(
        hotel_id=21966,
        checkin=date(2026, 8, 20),
        checkout=date(2026, 8, 22),
        adults=2,
        chd_ages=[12, 11],
        currency="EUR",
    )

    assert result.available is True
    _, kwargs = mock_client.get.await_args
    params = kwargs["params"]
    assert params["adult"] == 3
    assert params["chdCount"] == 1
    assert params["childage"] == "11"


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
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

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
async def test_create_reservation_child_payload_includes_child_guest_and_bucket_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Child occupancy should include child guest row and child bucket aliases."""
    mock_client = AsyncMock()
    mock_client.post.return_value = {"reservation-id": "RSV-CHD-1", "voucher-no": "V-CHD-1"}
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

    draft = {
        "guest_name": "Test User",
        "phone": "+905301112233",
        "checkin_date": "2026-10-01",
        "checkout_date": "2026-10-03",
        "adults": 2,
        "chd_ages": [7],
        "room_type_id": 396097,
        "board_type_id": 2,
        "rate_type_id": 11,
        "rate_code_id": 102,
        "price_agency_id": 777,
        "total_price_eur": "140.0",
        "currency_display": "EUR",
    }

    result = await endpoints.create_reservation(21966, draft)

    assert result.reservation_id == "RSV-CHD-1"
    path = mock_client.post.await_args.kwargs["json_body"]
    assert path["adult-count"] == 2
    assert path["child-count"] == 1
    assert len(path["guest-list"]) == 3
    assert path["guest-list"][1]["name"] == ""
    assert path["guest-list"][1]["surname"] == ""
    assert path["guest-list"][2]["title-id"] == 2
    assert path["guest-list"][2]["name"] == ""
    assert path["guest-list"][2]["surname"] == ""
    assert path["guest-list"][2]["birthday"] == "2019-10-01"
    assert path["childage"] == "7"
    assert path["child-age"] == "7"
    assert path["chdAges"] == "7"
    assert path["chdCount"] == 1
    assert path["child"] == 1
    assert path["elder-child-count"] == 1
    assert path["younger-child-count"] == 0
    assert path["baby-count"] == 0


@pytest.mark.asyncio
async def test_create_reservation_uses_pms_pax_override_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Create payload should honor pax override from refreshed quote response."""
    mock_client = AsyncMock()
    mock_client.post.return_value = {"reservation-id": "RSV-PAX-1", "voucher-no": "V-PAX-1"}
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

    draft = {
        "guest_name": "Test User",
        "phone": "+905301112233",
        "checkin_date": "2026-10-01",
        "checkout_date": "2026-10-03",
        "adults": 2,
        "chd_ages": [12, 11],
        "pms_adult_count": 3,
        "pms_child_count": 1,
        "room_type_id": 396097,
        "board_type_id": 2,
        "rate_type_id": 11,
        "rate_code_id": 102,
        "price_agency_id": 777,
        "total_price_eur": "140.0",
        "currency_display": "EUR",
    }

    _ = await endpoints.create_reservation(21966, draft)
    path = mock_client.post.await_args.kwargs["json_body"]
    assert path["adult-count"] == 3
    assert path["child-count"] == 1
    assert len(path["guest-list"]) == 4
    assert path["guest-list"][1]["name"] == ""
    assert path["guest-list"][2]["name"] == ""
    assert path["guest-list"][3]["title-id"] == 2
    assert path["guest-list"][3]["birthday"] == "2015-10-01"
    assert path["child-ages"] == [11]
    assert path["chdAges"] == "11"


@pytest.mark.asyncio
async def test_create_reservation_uses_explicit_extra_guest_names_when_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Additional guest names should only be populated when explicitly provided."""
    mock_client = AsyncMock()
    mock_client.post.return_value = {"reservation-id": "RSV-NAMES-1", "voucher-no": "V-NAMES-1"}
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

    draft = {
        "guest_name": "Primary Guest",
        "phone": "+905301112233",
        "checkin_date": "2026-10-01",
        "checkout_date": "2026-10-03",
        "adults": 2,
        "chd_ages": [7],
        "extra_adult_names": ["Second Adult"],
        "extra_child_names": ["Kid Guest"],
        "room_type_id": 396097,
        "board_type_id": 2,
        "rate_type_id": 11,
        "rate_code_id": 102,
        "price_agency_id": 777,
        "total_price_eur": "140.0",
        "currency_display": "EUR",
    }

    _ = await endpoints.create_reservation(21966, draft)
    path = mock_client.post.await_args.kwargs["json_body"]
    assert path["guest-list"][1]["name"] == "Second"
    assert path["guest-list"][1]["surname"] == "Adult"
    assert path["guest-list"][2]["name"] == "Kid"
    assert path["guest-list"][2]["surname"] == "Guest"


@pytest.mark.asyncio
async def test_create_reservation_syncs_notes_via_update_reservation(monkeypatch: pytest.MonkeyPatch) -> None:
    """When draft contains notes, adapter should write them to reservation notes after create."""
    mock_client = AsyncMock()
    mock_client.post.side_effect = [
        {"reservation-id": "RSV-1", "voucher-no": "V-1"},
        {"success": True},
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

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
        "notes": "Misafirimiz şu notu iletti: Üst kat sakin oda rica ediyor.",
    }

    result = await endpoints.create_reservation(21966, draft)

    assert result.reservation_id == "RSV-1"
    assert mock_client.post.await_count == 2
    create_call = mock_client.post.await_args_list[0]
    notes_call = mock_client.post.await_args_list[1]
    assert create_call.kwargs["json_body"]["notes"] == draft["notes"]
    assert notes_call.args[0] == "/hotel/21966/updateReservation"
    assert notes_call.kwargs["json_body"]["reservationId"] == "RSV-1"
    assert notes_call.kwargs["json_body"]["voucherNo"] == "V-1"
    assert notes_call.kwargs["json_body"]["notes"] == draft["notes"]


@pytest.mark.asyncio
async def test_create_reservation_notes_fallbacks_to_hoteladvisor_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If booking update endpoint fails, notes sync should fallback to HOTEL_RES update."""
    mock_client = AsyncMock()
    mock_client.post.side_effect = [
        {"reservation-id": "RSV-1", "voucher-no": "V-1"},
        RuntimeError("updateReservation failed"),
        {"success": True},
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

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
        "notes": "Misafirimiz şu notu iletti: Bebek arabası için geniş alan rica ediyor.",
    }

    _ = await endpoints.create_reservation(21966, draft)

    assert mock_client.post.await_count == 3
    fallback_call = mock_client.post.await_args_list[2]
    assert fallback_call.args[0] == "/Update/HOTEL_RES"
    payload = fallback_call.kwargs["json_body"]
    assert payload["Action"] == "Update"
    assert payload["Object"] == "HOTEL_RES"
    assert payload["Row"]["HOTELID"] == "21966"
    assert payload["Row"]["ID"] == "RSV-1"
    assert payload["Row"]["NOTES"] == draft["notes"]


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


@pytest.mark.asyncio
async def test_create_reservation_retry_success_also_syncs_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Notes must still be synced when booking create succeeds only after refreshed retry."""
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
    mock_client.post.side_effect = [agency_error, {"reservation-id": "RSV-2", "voucher-no": "V-2"}, {"success": True}]
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
                "notes": "Misafirimiz şu notu iletti: Geç check-in yapacaktır.",
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
            "notes": "Misafirimiz şu notu iletti: Geç check-in yapacaktır.",
        },
    )

    assert result.reservation_id == "RSV-2"
    assert mock_client.post.await_count == 3
    notes_call = mock_client.post.await_args_list[2]
    assert notes_call.args[0] == "/hotel/21966/updateReservation"
    assert notes_call.kwargs["json_body"]["reservationId"] == "RSV-2"
    assert notes_call.kwargs["json_body"]["voucherNo"] == "V-2"
    assert notes_call.kwargs["json_body"]["notes"] == "Misafirimiz şu notu iletti: Geç check-in yapacaktır."


def test_create_reservation_refresh_detector_accepts_price_mismatch_errors() -> None:
    """400 price mismatch responses should trigger quote refresh retry path."""
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    error = httpx.HTTPStatusError(
        "price-mismatch",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "You price quote 504 EUR is wrong, it must be 357 EUR"},
            request=request,
        ),
    )

    assert endpoints._needs_offer_refresh(error) is True
    assert endpoints._is_price_mismatch_error(error) is True


def test_create_reservation_refresh_detector_accepts_no_price_found_errors() -> None:
    """400 'no price found' responses should trigger quote refresh retry path."""
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    error = httpx.HTTPStatusError(
        "no-price-found",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "no price where found to match with the body parameters"},
            request=request,
        ),
    )

    assert endpoints._needs_offer_refresh(error) is True
    assert endpoints._is_price_mismatch_error(error) is False


@pytest.mark.asyncio
async def test_create_reservation_agency_error_without_refresh_falls_back_to_hoteladvisor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When agency refresh cannot recover, create should continue to HotelAdvisor fallback."""
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

    async def _post(path: str, _json_body: dict[str, object]) -> dict[str, object]:
        if path in {
            "/hotel/21966/createReservation",
            "/hotel/21966/reservation/create",
            "/hotel/21966/reservations/create",
        }:
            raise agency_error
        if path == "/Insert/HOTEL_RES":
            return {"primary-key": "991122"}
        if path == "/Execute/SP_HOTELRESGUEST_SAVE":
            return {"success": True}
        raise AssertionError(f"unexpected path {path}")

    mock_client.post.side_effect = _post
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(endpoints, "_refresh_offer_identifiers", AsyncMock(return_value=None))

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

    assert result.reservation_id == "991122"
    called_paths = [call.args[0] for call in mock_client.post.await_args_list]
    assert "/Insert/HOTEL_RES" in called_paths


@pytest.mark.asyncio
async def test_create_reservation_uses_second_refresh_after_price_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If first refreshed retry still mismatches price, second refresh should be attempted."""
    mock_client = AsyncMock()
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    agency_error = httpx.HTTPStatusError(
        "agency-not-found",
        request=request,
        response=httpx.Response(400, json={"success": False, "message": "Agency Not Found"}, request=request),
    )
    price_error = httpx.HTTPStatusError(
        "price-mismatch",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "You price quote 504 EUR is wrong, it must be 357 EUR"},
            request=request,
        ),
    )
    mock_client.post.side_effect = [agency_error, price_error, {"reservation-id": "RSV-SECOND"}]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(
        endpoints,
        "_refresh_offer_identifiers",
        AsyncMock(
            side_effect=[
                # Proactive refresh (corrects stale IDs before first attempt)
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 396095,
                    "board_type_id": 44512,
                    "rate_type_id": 24170,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "504.0",
                    "currency_display": "EUR",
                    "cancel_policy_type": "FREE_CANCEL",
                },
                # First error recovery refresh (after agency error)
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 396095,
                    "board_type_id": 44512,
                    "rate_type_id": 24170,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "504.0",
                    "currency_display": "EUR",
                    "cancel_policy_type": "FREE_CANCEL",
                },
                # Second error recovery refresh (after price mismatch)
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 396095,
                    "board_type_id": 44512,
                    "rate_type_id": 24178,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "999.0",
                    "currency_display": "EUR",
                    "cancel_policy_type": "FREE_CANCEL",
                    "pms_adult_count": 3,
                    "pms_child_count": 1,
                },
            ]
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
            "chd_ages": [12, 11],
            "room_type_id": 396095,
            "board_type_id": 2,
            "rate_type_id": 10,
            "rate_code_id": 101,
            "price_agency_id": 777,
            "total_price_eur": "1501.5",
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
        },
    )

    assert result.reservation_id == "RSV-SECOND"
    assert mock_client.post.await_count == 3
    second_refresh_payload = mock_client.post.await_args_list[2].kwargs["json_body"]
    assert second_refresh_payload["total-price"] == 357.0


@pytest.mark.asyncio
async def test_create_reservation_second_refresh_success_also_syncs_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Second-refresh success path must also write customer-visible notes to Elektra."""
    mock_client = AsyncMock()
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    agency_error = httpx.HTTPStatusError(
        "agency-not-found",
        request=request,
        response=httpx.Response(400, json={"success": False, "message": "Agency Not Found"}, request=request),
    )
    price_error = httpx.HTTPStatusError(
        "price-mismatch",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "You price quote 504 EUR is wrong, it must be 357 EUR"},
            request=request,
        ),
    )
    mock_client.post.side_effect = [
        agency_error,
        price_error,
        {"reservation-id": "RSV-SECOND", "voucher-no": "V-SECOND"},
        {"success": True},
    ]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(
        endpoints,
        "_refresh_offer_identifiers",
        AsyncMock(
            side_effect=[
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 396095,
                    "board_type_id": 44512,
                    "rate_type_id": 24170,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "504.0",
                    "currency_display": "EUR",
                    "cancel_policy_type": "FREE_CANCEL",
                    "notes": "Misafirimiz şu notu iletti: Sessiz oda rica ediyor.",
                },
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 396095,
                    "board_type_id": 44512,
                    "rate_type_id": 24170,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "504.0",
                    "currency_display": "EUR",
                    "cancel_policy_type": "FREE_CANCEL",
                    "notes": "Misafirimiz şu notu iletti: Sessiz oda rica ediyor.",
                },
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 396095,
                    "board_type_id": 44512,
                    "rate_type_id": 24178,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "999.0",
                    "currency_display": "EUR",
                    "cancel_policy_type": "FREE_CANCEL",
                    "pms_adult_count": 3,
                    "pms_child_count": 1,
                    "notes": "Misafirimiz şu notu iletti: Sessiz oda rica ediyor.",
                },
            ]
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
            "chd_ages": [12, 11],
            "room_type_id": 396095,
            "board_type_id": 2,
            "rate_type_id": 10,
            "rate_code_id": 101,
            "price_agency_id": 777,
            "total_price_eur": "1501.5",
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
            "notes": "Misafirimiz şu notu iletti: Sessiz oda rica ediyor.",
        },
    )

    assert result.reservation_id == "RSV-SECOND"
    assert mock_client.post.await_count == 4
    notes_call = mock_client.post.await_args_list[3]
    assert notes_call.args[0] == "/hotel/21966/updateReservation"
    assert notes_call.kwargs["json_body"]["reservationId"] == "RSV-SECOND"
    assert notes_call.kwargs["json_body"]["voucherNo"] == "V-SECOND"
    assert notes_call.kwargs["json_body"]["notes"] == "Misafirimiz şu notu iletti: Sessiz oda rica ediyor."


@pytest.mark.asyncio
async def test_create_reservation_uses_final_price_override_after_second_refresh_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second mismatch should trigger one final retry using provider-required total."""
    mock_client = AsyncMock()
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    agency_error = httpx.HTTPStatusError(
        "agency-not-found",
        request=request,
        response=httpx.Response(400, json={"success": False, "message": "Agency Not Found"}, request=request),
    )
    price_error_1 = httpx.HTTPStatusError(
        "price-mismatch-1",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "You price quote 1501.5 EUR is wrong, it must be 1232 EUR"},
            request=request,
        ),
    )
    price_error_2 = httpx.HTTPStatusError(
        "price-mismatch-2",
        request=request,
        response=httpx.Response(
            400,
            json={"success": False, "message": "You price quote 1232 EUR is wrong, it must be 1120 EUR"},
            request=request,
        ),
    )
    mock_client.post.side_effect = [agency_error, price_error_1, price_error_2, {"reservation-id": "RSV-FINAL"}]
    monkeypatch.setattr(endpoints, "get_elektraweb_client", lambda: mock_client)
    monkeypatch.setattr(
        endpoints,
        "_refresh_offer_identifiers",
        AsyncMock(
            side_effect=[
                # Proactive refresh (corrects stale IDs before first attempt)
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 438550,
                    "board_type_id": 44512,
                    "rate_type_id": 24178,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "1501.5",
                    "currency_display": "EUR",
                },
                # First error recovery refresh (after agency error)
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 438550,
                    "board_type_id": 44512,
                    "rate_type_id": 24178,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "1501.5",
                    "currency_display": "EUR",
                },
                # Second error recovery refresh (after price mismatch)
                {
                    "guest_name": "Test User",
                    "phone": "+905301112233",
                    "checkin_date": "2026-10-01",
                    "checkout_date": "2026-10-03",
                    "adults": 2,
                    "chd_ages": [12, 11],
                    "room_type_id": 438550,
                    "board_type_id": 44512,
                    "rate_type_id": 24170,
                    "rate_code_id": 183666,
                    "price_agency_id": 247664,
                    "total_price_eur": "1232.0",
                    "currency_display": "EUR",
                    "pms_adult_count": 3,
                    "pms_child_count": 1,
                },
            ]
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
            "chd_ages": [12, 11],
            "room_type_id": 438550,
            "board_type_id": 2,
            "rate_type_id": 10,
            "rate_code_id": 101,
            "price_agency_id": 777,
            "total_price_eur": "1501.5",
            "currency_display": "EUR",
            "cancel_policy_type": "FREE_CANCEL",
        },
    )

    assert result.reservation_id == "RSV-FINAL"
    assert mock_client.post.await_count == 4
    final_payload = mock_client.post.await_args_list[3].kwargs["json_body"]
    assert final_payload["total-price"] == 1120.0


@pytest.mark.asyncio
async def test_refresh_offer_identifiers_allows_price_drift_with_room_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Identifier refresh should recover by room/cancel policy even when total price drifted."""
    monkeypatch.setattr(
        endpoints,
        "quote",
        AsyncMock(
            return_value=endpoints.QuoteResponse(
                offers=[
                    endpoints.BookingOffer(
                        id="of1",
                        room_type_id=396097,
                        room_type="DELUXE",
                        board_type_id=44512,
                        board_type="BB",
                        rate_type_id=24171,
                        rate_type="Ucretsiz Iptal",
                        rate_code_id=183666,
                        price_agency_id=247664,
                        currency_code="EUR",
                        price=160.0,
                        discounted_price=150.0,
                        cancellation_penalty={"is_refundable": True},
                    )
                ]
            )
        ),
    )

    refreshed = await endpoints._refresh_offer_identifiers(
        21966,
        {
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-03",
            "adults": 2,
            "chd_ages": [],
            "currency_display": "EUR",
            "nationality": "TR",
            "cancel_policy_type": "FREE_CANCEL",
            "room_type_id": 396097,
            "total_price_eur": "999.0",
        },
    )

    assert refreshed is not None
    assert refreshed["price_agency_id"] == 247664
    assert refreshed["rate_code_id"] == 183666


@pytest.mark.asyncio
async def test_refresh_offer_identifiers_returns_none_when_resolved_room_type_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh must return None when resolved room type is not in live quote — never silently substitute."""
    monkeypatch.setattr(
        endpoints,
        "quote",
        AsyncMock(
            return_value=endpoints.QuoteResponse(
                offers=[
                    endpoints.BookingOffer(
                        id="of_blocked",
                        room_type_id=396094,
                        room_type="DELUXE",
                        board_type_id=44512,
                        board_type="BB",
                        rate_type_id=24171,
                        rate_type="Ucretsiz Iptal",
                        rate_code_id=183666,
                        price_agency_id=247664,
                        currency_code="EUR",
                        price=160.0,
                        discounted_price=150.0,
                        room_to_sell=0,
                        stop_sell=False,
                        cancellation_penalty={"is_refundable": True},
                    ),
                    endpoints.BookingOffer(
                        id="of_sellable",
                        room_type_id=396095,
                        room_type="EXCLUSIVE POOL",
                        board_type_id=44512,
                        board_type="BB",
                        rate_type_id=24170,
                        rate_type="Ucretsiz Iptal",
                        rate_code_id=183666,
                        price_agency_id=247664,
                        currency_code="EUR",
                        price=180.0,
                        discounted_price=170.0,
                        room_to_sell=2,
                        stop_sell=False,
                        cancellation_penalty={"is_refundable": True},
                    ),
                ]
            )
        ),
    )

    refreshed = await endpoints._refresh_offer_identifiers(
        21966,
        {
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-03",
            "adults": 2,
            "chd_ages": [],
            "currency_display": "EUR",
            "nationality": "TR",
            "cancel_policy_type": "FREE_CANCEL",
            "room_type_id": 4,  # profile-local id (Penthouse Land / pms 486991), not in quote
            "total_price_eur": "999.0",
        },
        prefer_money_match=False,
    )

    # Must return None instead of silently substituting to a different room type
    assert refreshed is None


@pytest.mark.asyncio
async def test_create_reservation_aborts_when_refresh_changes_room_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reservation creation must abort if offer refresh would change the room type."""
    mock_client = AsyncMock()
    request = httpx.Request("POST", "https://bookingapi.elektraweb.com/hotel/21966/createReservation")
    agency_error = httpx.HTTPStatusError(
        "agency-not-found",
        request=request,
        response=httpx.Response(400, json={"success": False, "message": "Agency Not Found"}, request=request),
    )
    mock_client.post.side_effect = [agency_error]
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
                "room_type_id": 396095,  # Exclusive Pool — different from draft
                "board_type_id": 44512,
                "rate_type_id": 24178,
                "rate_code_id": 183666,
                "price_agency_id": 247664,
                "total_price_eur": "500.0",
                "currency_display": "EUR",
                "cancel_policy_type": "FREE_CANCEL",
            }
        ),
    )

    with pytest.raises(RuntimeError, match="Room type changed during offer refresh"):
        await endpoints.create_reservation(
            21966,
            {
                "guest_name": "Test User",
                "phone": "+905301112233",
                "checkin_date": "2026-10-01",
                "checkout_date": "2026-10-03",
                "adults": 2,
                "chd_ages": [],
                "room_type_id": 396096,  # Penthouse
                "board_type_id": 2,
                "rate_type_id": 10,
                "rate_code_id": 101,
                "price_agency_id": 777,
                "total_price_eur": "500.0",
                "currency_display": "EUR",
                "cancel_policy_type": "FREE_CANCEL",
            },
        )


def test_select_offer_for_cancel_policy_avoids_contract_for_non_refundable() -> None:
    """Non-refundable selection should prefer explicit non-refundable rate over contract."""
    contract = endpoints.BookingOffer(
        id="contract",
        room_type_id=396097,
        room_type="SUPERIOR",
        board_type_id=44512,
        board_type="BB",
        rate_type_id=24169,
        rate_type="Kontrat",
        rate_code_id=183666,
        price_agency_id=247664,
        currency_code="EUR",
        price=420.0,
        discounted_price=378.0,
        room_to_sell=3,
        cancellation_penalty={"is_refundable": False},
    )
    nonref = endpoints.BookingOffer(
        id="nrf",
        room_type_id=396097,
        room_type="SUPERIOR",
        board_type_id=44512,
        board_type="BB",
        rate_type_id=24170,
        rate_type="Iptal Edilemez",
        rate_code_id=183666,
        price_agency_id=247664,
        currency_code="EUR",
        price=420.0,
        discounted_price=378.0,
        room_to_sell=3,
        cancellation_penalty={"is_refundable": False},
    )

    selected = endpoints._select_offer_for_cancel_policy(
        {"cancel_policy_type": "NON_REFUNDABLE"},
        [contract, nonref],
    )
    assert selected.rate_type_id == 24170


def test_select_offer_for_cancel_policy_prefers_refundable_for_free_cancel() -> None:
    """Free-cancel selection should pick refundable/free-cancel rate labels."""
    contract = endpoints.BookingOffer(
        id="contract",
        room_type_id=396097,
        room_type="SUPERIOR",
        board_type_id=44512,
        board_type="BB",
        rate_type_id=24169,
        rate_type="Kontrat",
        rate_code_id=183666,
        price_agency_id=247664,
        currency_code="EUR",
        price=420.0,
        discounted_price=378.0,
        room_to_sell=3,
        cancellation_penalty={"is_refundable": False},
    )
    free_cancel = endpoints.BookingOffer(
        id="free",
        room_type_id=396097,
        room_type="SUPERIOR",
        board_type_id=44512,
        board_type="BB",
        rate_type_id=24178,
        rate_type="Ucretsiz Iptal",
        rate_code_id=183666,
        price_agency_id=247664,
        currency_code="EUR",
        price=462.0,
        discounted_price=415.8,
        room_to_sell=3,
        cancellation_penalty={"is_refundable": True},
    )

    selected = endpoints._select_offer_for_cancel_policy(
        {"cancel_policy_type": "FREE_CANCEL"},
        [contract, free_cancel],
    )
    assert selected.rate_type_id == 24178
