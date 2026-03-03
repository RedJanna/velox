"""Elektraweb API endpoint methods — typed wrappers around the HTTP client."""

from datetime import date

import structlog

from velox.adapters.elektraweb.client import get_elektraweb_client
from velox.adapters.elektraweb.mapper import (
    AvailabilityResponse,
    QuoteResponse,
    ReservationDetailResponse,
    ReservationResponse,
    parse_availability,
    parse_quote,
    parse_reservation_create,
    parse_reservation_detail,
)

logger = structlog.get_logger(__name__)


async def availability(
    hotel_id: int,
    checkin: date,
    checkout: date,
    adults: int,
    chd_count: int = 0,
    chd_ages: list[int] | None = None,
    currency: str = "EUR",
) -> AvailabilityResponse:
    """Check room availability for given dates."""
    client = get_elektraweb_client()
    params: dict[str, str | int] = {
        "checkin": checkin.isoformat(),
        "checkout": checkout.isoformat(),
        "adults": adults,
        "chdCount": chd_count,
        "currency": currency,
    }
    if chd_ages:
        params["chdAges"] = ",".join(str(age) for age in chd_ages)

    logger.info("elektraweb_availability_request", hotel_id=hotel_id, checkin=str(checkin), checkout=str(checkout))
    raw = await client.get(f"/hotel/{hotel_id}/availability", params=params)
    return parse_availability(raw)


async def quote(
    hotel_id: int,
    checkin: date,
    checkout: date,
    adults: int,
    chd_count: int = 0,
    chd_ages: list[int] | None = None,
    currency: str = "EUR",
    language: str = "TR",
    nationality: str = "TR",
    only_best_offer: bool = False,
    cancel_policy_type: str | None = None,
) -> QuoteResponse:
    """Get price quotes/offers for given dates and room configuration."""
    client = get_elektraweb_client()
    params: dict[str, str | int | bool] = {
        "checkin": checkin.isoformat(),
        "checkout": checkout.isoformat(),
        "adults": adults,
        "chdCount": chd_count,
        "currency": currency,
        "language": language,
        "nationality": nationality,
        "onlyBestOffer": only_best_offer,
    }
    if chd_ages:
        params["chdAges"] = ",".join(str(age) for age in chd_ages)
    if cancel_policy_type:
        params["cancelPolicyType"] = cancel_policy_type

    logger.info("elektraweb_quote_request", hotel_id=hotel_id, checkin=str(checkin), checkout=str(checkout))
    raw = await client.get(f"/hotel/{hotel_id}/price/", params=params)
    return parse_quote(raw)


async def create_reservation(hotel_id: int, draft: dict) -> ReservationResponse:
    """Create reservation in Elektraweb with fallback paths."""
    client = get_elektraweb_client()
    paths = [
        f"/hotel/{hotel_id}/createReservation",
        f"/hotel/{hotel_id}/reservation/create",
        f"/hotel/{hotel_id}/reservations/create",
    ]

    last_error: Exception | None = None
    for path in paths:
        try:
            logger.info("elektraweb_create_reservation_attempt", hotel_id=hotel_id, path=path)
            raw = await client.post(path, json_body=draft)
            return parse_reservation_create(raw)
        except Exception as error:
            logger.warning("elektraweb_create_reservation_path_failed", path=path, error=str(error))
            last_error = error

    logger.error("elektraweb_create_reservation_all_paths_failed", hotel_id=hotel_id)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to create reservation for hotel {hotel_id}")


async def get_reservation(
    hotel_id: int,
    reservation_id: str | None = None,
    voucher_no: str | None = None,
) -> ReservationDetailResponse:
    """Fetch reservation details using path and method fallbacks."""
    client = get_elektraweb_client()
    body: dict[str, int | str] = {"hotelId": hotel_id}
    if reservation_id:
        body["reservationId"] = reservation_id
    if voucher_no:
        body["voucherNo"] = voucher_no

    paths_and_methods: list[tuple[str, str]] = [
        ("POST", f"/hotel/{hotel_id}/getReservation"),
        ("GET", f"/hotel/{hotel_id}/reservation/{reservation_id or ''}"),
        ("POST", f"/hotel/{hotel_id}/reservation/get"),
    ]

    last_error: Exception | None = None
    for method, path in paths_and_methods:
        try:
            logger.info("elektraweb_get_reservation_attempt", hotel_id=hotel_id, path=path, method=method)
            if method == "POST":
                raw = await client.post(path, json_body=body)
            else:
                params: dict[str, str] | None = {"voucherNo": voucher_no} if voucher_no else None
                raw = await client.get(path, params=params)
            return parse_reservation_detail(raw)
        except Exception as error:
            logger.warning("elektraweb_get_reservation_path_failed", path=path, error=str(error))
            last_error = error

    logger.error("elektraweb_get_reservation_all_paths_failed", hotel_id=hotel_id)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to get reservation for hotel {hotel_id}")


async def modify_reservation(hotel_id: int, reservation_id: str, updates: dict) -> dict:
    """Modify an existing reservation."""
    client = get_elektraweb_client()
    body = {"reservationId": reservation_id, **updates}
    logger.info("elektraweb_modify_reservation_request", hotel_id=hotel_id, reservation_id=reservation_id)
    return await client.post(f"/hotel/{hotel_id}/updateReservation", json_body=body)


async def cancel_reservation(hotel_id: int, reservation_id: str, reason: str) -> dict:
    """Cancel an existing reservation."""
    client = get_elektraweb_client()
    body = {"reservationId": reservation_id, "reason": reason}
    logger.info("elektraweb_cancel_reservation_request", hotel_id=hotel_id, reservation_id=reservation_id)
    return await client.post(f"/hotel/{hotel_id}/cancelReservation", json_body=body)
