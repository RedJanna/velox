"""Elektraweb API endpoint methods — typed wrappers around the HTTP client."""

from datetime import date

import structlog

from velox.adapters.elektraweb.client import get_elektraweb_client
from velox.adapters.elektraweb.mapper import (
    AvailabilityResponse,
    QuoteResponse,
    ReservationDetailResponse,
    ReservationResponse,
    normalize_keys,
    parse_availability,
    parse_quote,
    parse_reservation_create,
    parse_reservation_detail,
)

logger = structlog.get_logger(__name__)
CHILD_OCCUPANCY_UNVERIFIED = "CHILD_OCCUPANCY_UNVERIFIED"
PMS_ADULT_AGE_MIN = 13


def _requested_child_ages(chd_count: int, chd_ages: list[int] | None) -> list[int]:
    """Return normalized child ages for request construction."""
    if chd_ages:
        return list(chd_ages)
    return [0] * chd_count


def _child_bucket_counts(chd_ages: list[int]) -> dict[str, int]:
    """Map child ages to Elektra's younger/elder/baby buckets."""
    counts = {
        "elder_child_count": 0,
        "younger_child_count": 0,
        "baby_count": 0,
    }
    for age in chd_ages:
        if age <= 0:
            counts["baby_count"] += 1
        elif age <= 5:
            counts["younger_child_count"] += 1
        else:
            counts["elder_child_count"] += 1
    return counts


def _requested_child_count(chd_count: int, chd_ages: list[int] | None) -> int:
    """Return the requested child count using ages when present."""
    return len(_requested_child_ages(chd_count, chd_ages))


def _normalize_children_for_pms(chd_count: int, chd_ages: list[int] | None) -> tuple[int, list[int]]:
    """Treat teen ages as adults for PMS occupancy parity when ages are provided."""
    ages = _requested_child_ages(chd_count, chd_ages)
    if not chd_ages:
        return chd_count, ages

    normalized_child_ages = [age for age in ages if age < PMS_ADULT_AGE_MIN]
    return len(normalized_child_ages), normalized_child_ages


def _apply_child_quote_params(params: dict[str, str | int | bool], chd_count: int, chd_ages: list[int] | None) -> None:
    """Populate Elektra quote params for child occupancy using supported aliases."""
    ages = _requested_child_ages(chd_count, chd_ages)
    if not ages:
        return

    requested_children = len(ages)
    age_csv = ",".join(str(age) for age in ages)
    bucket_counts = _child_bucket_counts(ages)

    params["chdCount"] = requested_children
    params["chdAges"] = age_csv
    params["childage"] = age_csv
    params["child-age"] = age_csv
    params["child-ages"] = age_csv
    params["child"] = requested_children
    params["child-count"] = requested_children
    params["children-count"] = requested_children
    params["elder-child-count"] = bucket_counts["elder_child_count"]
    params["younger-child-count"] = bucket_counts["younger_child_count"]
    params["baby-count"] = bucket_counts["baby_count"]


def _quote_response_matches_requested_occupancy(
    raw: dict | list,
    *,
    adults: int,
    requested_buckets: dict[str, int],
) -> bool:
    """Return True when at least one offer reflects the requested occupancy."""
    requested_children = sum(requested_buckets.values())
    if requested_children <= 0:
        return True

    normalized = normalize_keys(raw)
    if not isinstance(normalized, list) or not normalized:
        return False

    for item in normalized:
        pax_count = item.get("pax_count")
        if not isinstance(pax_count, dict):
            continue
        actual_adults = int(pax_count.get("adult", 0) or 0)
        actual_buckets = {
            "elder_child_count": int(pax_count.get("elder_child_count", 0) or 0),
            "younger_child_count": int(pax_count.get("younger_child_count", 0) or 0),
            "baby_count": int(pax_count.get("baby_count", 0) or 0),
        }
        actual_children = sum(actual_buckets.values())
        if (
            actual_adults == adults
            and actual_children == requested_children
            and actual_buckets == requested_buckets
        ):
            return True
    return False


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
    normalized_chd_count, normalized_chd_ages = _normalize_children_for_pms(chd_count, chd_ages)
    params: dict[str, str | int] = {
        "fromdate": checkin.isoformat(),
        "todate": checkout.isoformat(),
        "adult": adults,
        "currency": currency,
    }
    _apply_child_quote_params(params, normalized_chd_count, normalized_chd_ages)

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
    normalized_chd_count, normalized_chd_ages = _normalize_children_for_pms(chd_count, chd_ages)
    requested_children = _requested_child_count(chd_count, chd_ages)
    adult_equivalent_children = max(requested_children - normalized_chd_count, 0)
    normalized_adults = adults + adult_equivalent_children
    requested_ages = _requested_child_ages(normalized_chd_count, normalized_chd_ages)
    requested_children = len(requested_ages)
    requested_buckets = _child_bucket_counts(requested_ages)
    params: dict[str, str | int | bool] = {
        "fromdate": checkin.isoformat(),
        "todate": checkout.isoformat(),
        "adult": normalized_adults,
        "currency": currency,
        "language": language,
        "nationality": nationality,
        "onlyBestOffer": only_best_offer,
    }
    _apply_child_quote_params(params, normalized_chd_count, normalized_chd_ages)
    if cancel_policy_type:
        params["cancelPolicyType"] = cancel_policy_type

    logger.info("elektraweb_quote_request", hotel_id=hotel_id, checkin=str(checkin), checkout=str(checkout))
    raw = await client.get(f"/hotel/{hotel_id}/price/", params=params)
    if not _quote_response_matches_requested_occupancy(
        raw,
        adults=normalized_adults,
        requested_buckets=requested_buckets,
    ):
        logger.warning(
            "elektraweb_quote_child_occupancy_mismatch",
            hotel_id=hotel_id,
            adults=normalized_adults,
            requested_children=requested_children,
            requested_buckets=requested_buckets,
        )
        raise RuntimeError(
            f"{CHILD_OCCUPANCY_UNVERIFIED}: PMS quote did not reflect requested child occupancy."
        )
    return parse_quote(raw)


def _safe_int(value: object, default: int = 0) -> int:
    """Convert arbitrary value to int with default fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_iso_date(value: object) -> str:
    """Normalize a date-like value to YYYY-MM-DD."""
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "T" in raw:
        return raw.split("T", maxsplit=1)[0]
    if " " in raw:
        return raw.split(" ", maxsplit=1)[0]
    return raw


def _split_guest_name(full_name: str) -> tuple[str, str]:
    """Split full name into first and last name with safe fallback."""
    normalized = " ".join(full_name.strip().split())
    if not normalized:
        return "Guest", "Guest"
    tokens = normalized.split(" ")
    if len(tokens) == 1:
        return tokens[0], tokens[0]
    return tokens[0], " ".join(tokens[1:])


def _build_hoteladvisor_insert_payload(hotel_id: int, draft: dict) -> dict:
    """Build `/Insert/HOTEL_RES` payload for HotelAdvisor integration."""
    checkin_date = _normalize_iso_date(draft.get("checkin_date"))
    checkout_date = _normalize_iso_date(draft.get("checkout_date"))
    try:
        los = (date.fromisoformat(checkout_date) - date.fromisoformat(checkin_date)).days
    except ValueError:
        los = _safe_int(draft.get("los"), 1)
    los = max(los, 1)

    ages = draft.get("chd_ages")
    chd_ages = [max(0, _safe_int(age, 0)) for age in ages] if isinstance(ages, list) else []
    younger_children = len([age for age in chd_ages if 0 < age <= 5])
    elder_children = len([age for age in chd_ages if age > 5])
    babies = len([age for age in chd_ages if age <= 0])

    row: dict[str, object] = {
        "HOTELID": str(hotel_id),
        "CHECKIN": f"{checkin_date} 14:00:00.000" if checkin_date else None,
        "CHECKOUT": f"{checkout_date} 12:00:00.000" if checkout_date else None,
        "LOS": str(los),
        "ADULT": str(max(_safe_int(draft.get("adults"), 1), 1)),
        "CHD1": str(younger_children),
        "CHD2": str(elder_children),
        "BABY": str(babies),
        "ROOMCOUNT": str(max(_safe_int(draft.get("room_count"), 1), 1)),
        "ROOMTYPEID": str(_safe_int(draft.get("room_type_id"), 0)),
        "GIVENROOMTYPEID": str(_safe_int(draft.get("given_room_type_id", draft.get("room_type_id")), 0)),
        "BOARDTYPEID": str(_safe_int(draft.get("board_type_id"), 0)),
        "RATETYPEID": str(_safe_int(draft.get("rate_type_id"), 0)),
        "RATECODEID": str(_safe_int(draft.get("rate_code_id"), 0)),
        "CURRENCYID_CURCODE": str(draft.get("currency_display", draft.get("currency", "EUR"))),
        "TOTALPRICE": str(draft.get("total_price_eur", draft.get("total_price", ""))),
        "GUESTNAMES": draft.get("guest_name"),
        "CONTACTPERSON": draft.get("guest_name"),
        "CONTACTPHONE": draft.get("phone"),
        "CONTACTEMAIL": draft.get("email"),
        "NOTES": draft.get("notes"),
        "RESSTATEID": str(_safe_int(draft.get("res_state_id"), 2)),
        "RESSUBSTATE": str(draft.get("res_sub_state", "Definite")),
        "ISAGENCY": bool(draft.get("is_agency", False)),
    }

    if chd_ages:
        row["CHD1AGE"] = str(chd_ages[0])
    if len(chd_ages) > 1:
        row["CHD2AGE"] = str(chd_ages[1])
    if len(chd_ages) > 2:
        row["CHD3AGE"] = str(chd_ages[2])
    if len(chd_ages) > 3:
        row["CHD4AGE"] = str(chd_ages[3])

    normalized_row = {key: value for key, value in row.items() if value not in (None, "", "0")}
    normalized_row["HOTELID"] = str(hotel_id)
    normalized_row["LOS"] = str(los)
    normalized_row["ADULT"] = str(max(_safe_int(draft.get("adults"), 1), 1))
    return {
        "Action": "Insert",
        "Object": "HOTEL_RES",
        "Row": normalized_row,
        "SelectAfterInsert": ["ID"],
    }


def _build_hoteladvisor_guest_payload(hotel_id: int, reservation_id: str, draft: dict) -> dict | None:
    """Build `/Execute/SP_HOTELRESGUEST_SAVE` payload when guest fields exist."""
    guest_name = str(draft.get("guest_name") or "").strip()
    if not guest_name:
        return None
    first_name, last_name = _split_guest_name(guest_name)
    phone = str(draft.get("phone") or "").strip().replace("+", "")
    email = str(draft.get("email") or "").strip() or None

    parameters: dict[str, object] = {
        "HOTELID": hotel_id,
        "RESID": _safe_int(reservation_id, 0) or reservation_id,
        "RES_GUEST_ID": draft.get("res_guest_id"),
        "GUESTID": draft.get("guest_id"),
        "NAME": first_name,
        "LNAME": last_name,
        "PHONE": phone or None,
        "EMAIL": email,
        "NATIONALITYID": _safe_int(draft.get("nationality_id"), 0) or None,
    }
    normalized = {key: value for key, value in parameters.items() if value not in (None, "")}
    if "RESID" not in normalized:
        return None
    return {
        "Action": "Execute",
        "Object": "SP_HOTELRESGUEST_SAVE",
        "BaseObject": "RES_NAME",
        "Parameters": normalized,
    }


async def create_reservation(hotel_id: int, draft: dict) -> ReservationResponse:
    """Create reservation in Elektraweb with HotelAdvisor-first failover strategy."""
    client = get_elektraweb_client()
    last_error: Exception | None = None

    try:
        logger.info("elektraweb_create_reservation_attempt", hotel_id=hotel_id, path="/Insert/HOTEL_RES")
        insert_payload = _build_hoteladvisor_insert_payload(hotel_id, draft)
        raw = await client.post("/Insert/HOTEL_RES", json_body=insert_payload)
        parsed = parse_reservation_create(raw)
        if parsed.reservation_id:
            guest_payload = _build_hoteladvisor_guest_payload(hotel_id, parsed.reservation_id, draft)
            if guest_payload is not None:
                try:
                    await client.post("/Execute/SP_HOTELRESGUEST_SAVE", json_body=guest_payload)
                except Exception as guest_error:
                    logger.warning("elektraweb_guest_save_failed", hotel_id=hotel_id, error=str(guest_error))
            return parsed
    except Exception as error:
        logger.warning("elektraweb_create_reservation_path_failed", path="/Insert/HOTEL_RES", error=str(error))
        last_error = error

    paths = [
        f"/hotel/{hotel_id}/createReservation",
        f"/hotel/{hotel_id}/reservation/create",
        f"/hotel/{hotel_id}/reservations/create",
    ]

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
    logger.info("elektraweb_modify_reservation_request", hotel_id=hotel_id, reservation_id=reservation_id)

    update_row: dict[str, object] = {"ID": reservation_id, "HOTELID": str(hotel_id)}
    update_row.update({key: value for key, value in updates.items() if value is not None})
    hoteladvisor_payload = {"Action": "Update", "Object": "HOTEL_RES", "Row": update_row}
    try:
        return await client.post("/Update/HOTEL_RES", json_body=hoteladvisor_payload)
    except Exception as error:
        logger.warning("elektraweb_modify_reservation_hoteladvisor_failed", error=str(error))

    body = {"reservationId": reservation_id, **updates}
    return await client.post(f"/hotel/{hotel_id}/updateReservation", json_body=body)


async def cancel_reservation(hotel_id: int, reservation_id: str, reason: str) -> dict:
    """Cancel an existing reservation."""
    client = get_elektraweb_client()
    body = {"reservationId": reservation_id, "reason": reason}
    logger.info("elektraweb_cancel_reservation_request", hotel_id=hotel_id, reservation_id=reservation_id)
    return await client.post(f"/hotel/{hotel_id}/cancelReservation", json_body=body)
