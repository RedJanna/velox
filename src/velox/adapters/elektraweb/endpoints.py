"""Elektraweb API endpoint methods — typed wrappers around the HTTP client."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import re
from typing import Any

import httpx
import structlog

from velox.adapters.elektraweb.client import get_elektraweb_client
from velox.adapters.elektraweb.mapper import (
    AvailabilityResponse,
    BookingOffer,
    QuoteResponse,
    ReservationDetailResponse,
    ReservationResponse,
    normalize_keys,
    parse_availability,
    parse_quote,
    parse_reservation_create,
    parse_reservation_detail,
)
from velox.core.hotel_profile_loader import get_profile

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
    raw: dict[str, Any] | list[Any],
    *,
    adults: int,
    requested_buckets: dict[str, int],
) -> bool:
    """Return True when at least one offer reflects the requested occupancy."""
    requested_children = sum(requested_buckets.values())
    if requested_children <= 0:
        return True

    normalized = normalize_keys(raw)
    items: list[dict[str, Any]] = []
    if isinstance(normalized, list):
        items = [item for item in normalized if isinstance(item, dict)]
    elif isinstance(normalized, dict):
        offers = normalized.get("offers")
        data = normalized.get("data")
        if isinstance(offers, list):
            items = [item for item in offers if isinstance(item, dict)]
        elif isinstance(data, list):
            items = [item for item in data if isinstance(item, dict)]
    if not items:
        return False

    for item in items:
        pax_count = item.get("pax_count")
        if not isinstance(pax_count, dict):
            continue
        actual_adults = int(pax_count.get("adult", 0) or 0)
        actual_buckets = {
            "elder_child_count": int(pax_count.get("elder_child_count", 0) or 0),
            "younger_child_count": int(pax_count.get("younger_child_count", 0) or 0),
            "baby_count": int(pax_count.get("baby_count", 0) or 0),
        }
        bucket_children = sum(actual_buckets.values())
        count_children = int(
            pax_count.get("child_count")
            or pax_count.get("children_count")
            or pax_count.get("chd_count")
            or pax_count.get("child")
            or 0
        )
        actual_children = bucket_children if bucket_children > 0 else count_children
        if actual_adults == adults and actual_children == requested_children:
            if bucket_children > 0 and actual_buckets != requested_buckets:
                logger.warning(
                    "elektraweb_quote_child_bucket_mismatch_total_matched",
                    adults=adults,
                    requested_buckets=requested_buckets,
                    actual_buckets=actual_buckets,
                )
            return True

        # PMS may reclassify edge ages (for example one child counted as adult)
        # while keeping total occupancy consistent. Accept this as a compatible match.
        requested_total = adults + requested_children
        actual_total = actual_adults + actual_children
        if (
            actual_total == requested_total
            and actual_adults >= adults
            and actual_children <= requested_children
        ):
            logger.warning(
                "elektraweb_quote_child_age_reclassified",
                requested_adults=adults,
                requested_children=requested_children,
                actual_adults=actual_adults,
                actual_children=actual_children,
            )
            return True

        if actual_adults != adults:
            continue
        if actual_children != requested_children:
            continue
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
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, (str, bytes, bytearray)):
            return int(value)
        return default
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert arbitrary value to float with default fallback."""
    try:
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, int | float | Decimal):
            return float(value)
        if isinstance(value, (str, bytes, bytearray)):
            return float(value)
        return default
    except (TypeError, ValueError):
        return default


def _utc_window_days(*, days_back: int, days_forward: int) -> tuple[str, str]:
    """Build reservation list query window in provider-required datetime format."""
    now = datetime.now(UTC)
    from_check_in = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00")
    to_check_in = (now + timedelta(days=days_forward)).strftime("%Y-%m-%dT23:59:59")
    return from_check_in, to_check_in


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


def _reservation_lookup_params(
    *,
    reservation_status: str,
    reservation_id: str | None,
    voucher_no: str | None,
    days_back: int = 365,
    days_forward: int = 730,
) -> dict[str, str]:
    """Build GET params for reservation-list lookup with bounded date window."""
    from_check_in, to_check_in = _utc_window_days(days_back=days_back, days_forward=days_forward)
    params = {
        "from-check-in": from_check_in,
        "to-check-in": to_check_in,
        "reservation-status": reservation_status,
    }
    if reservation_id:
        params["reservation-id"] = reservation_id
    if voucher_no:
        params["voucher-no"] = voucher_no
    return params


def _split_guest_name(full_name: str) -> tuple[str, str]:
    """Split full name into first and last name with safe fallback."""
    normalized = " ".join(full_name.strip().split())
    if not normalized:
        return "Guest", "Guest"
    tokens = normalized.split(" ")
    if len(tokens) == 1:
        return tokens[0], tokens[0]
    return tokens[0], " ".join(tokens[1:])


def _birthday_from_age(age: int, checkin_date: str) -> str:
    """Build yyyy-MM-dd birthday string from age using check-in date as reference."""
    try:
        checkin = date.fromisoformat(_normalize_iso_date(checkin_date))
    except ValueError:
        checkin = datetime.now(UTC).date()
    years = max(age, 0)
    year = max(checkin.year - years, 1900)
    return f"{year:04d}-{checkin.month:02d}-{checkin.day:02d}"


def _valid_email(value: object) -> str | None:
    """Return normalized email only when it looks valid enough for PMS validation."""
    raw = str(value or "").strip().lower()
    if not raw or "@" not in raw:
        return None
    return raw


def _parse_reservation_lookup_response(
    raw: dict[str, Any] | list[Any],
    *,
    reservation_id: str | None,
    voucher_no: str | None,
) -> ReservationDetailResponse:
    """Parse reservation-list response and return the matching reservation row."""
    normalized = normalize_keys(raw)
    items: list[dict[str, Any]] = []
    if isinstance(normalized, list):
        items = [item for item in normalized if isinstance(item, dict)]
    elif isinstance(normalized, dict):
        data = normalized.get("data")
        if isinstance(data, list):
            items = [item for item in data if isinstance(item, dict)]
        else:
            items = [normalized]

    reservation_id_str = str(reservation_id or "").strip()
    voucher_no_str = str(voucher_no or "").strip()
    for item in items:
        item_reservation_id = str(
            item.get("reservation_id")
            or item.get("res_id")
            or item.get("id")
            or item.get("primary_key")
            or ""
        ).strip()
        item_voucher_no = str(
            item.get("voucher_no")
            or item.get("voucher")
            or item.get("voucher_number")
            or ""
        ).strip()
        if reservation_id_str and item_reservation_id != reservation_id_str:
            continue
        if voucher_no_str and item_voucher_no != voucher_no_str:
            continue

        return ReservationDetailResponse(
            success=True,
            reservation_id=item_reservation_id,
            voucher_no=item_voucher_no,
            total_price=(
                item.get("total_price")
                or item.get("discounted_price")
                or item.get("price")
            ),
            state=str(item.get("state") or item.get("status") or item.get("res_state") or ""),
            raw_data=item,
        )
    return ReservationDetailResponse(raw_data=raw)


def _booking_api_guest_list(
    draft: dict[str, Any],
    *,
    child_count: int = 0,
    child_ages: list[int] | None = None,
) -> list[dict[str, object]]:
    """Build booking API guest-list rows with explicit child entries when available."""
    adults = max(_safe_int(draft.get("pms_adult_count", draft.get("adults")), 1), 1)
    first_name, last_name = _split_guest_name(str(draft.get("guest_name") or "Guest"))
    email = _valid_email(draft.get("email"))
    phone = str(draft.get("phone") or "").strip() or None
    checkin_date = str(draft.get("checkin_date") or "")
    safe_child_ages = list(child_ages or [])
    extra_adult_names = [
        str(name).strip()
        for name in draft.get("extra_adult_names", [])
        if isinstance(name, str) and str(name).strip()
    ]
    extra_child_names = [
        str(name).strip()
        for name in draft.get("extra_child_names", [])
        if isinstance(name, str) and str(name).strip()
    ]

    guests: list[dict[str, object]] = []
    for index in range(adults):
        name = first_name
        surname = last_name
        if index > 0:
            if index - 1 < len(extra_adult_names):
                name, surname = _split_guest_name(extra_adult_names[index - 1])
            else:
                # Keep unnamed guests generic unless guest explicitly provided names.
                name, surname = "Guest", "Guest"
        guest: dict[str, object] = {
            "title-id": 1,
            "name": name,
            "surname": surname,
        }
        if index == 0 and email:
            guest["email"] = email
        if index == 0 and phone:
            guest["phone"] = phone
        guests.append(guest)

    for index in range(max(child_count, 0)):
        age = max(_safe_int(safe_child_ages[index], 0), 0) if index < len(safe_child_ages) else 0
        child_name = extra_child_names[index] if index < len(extra_child_names) else "Child"
        child_first, child_last = _split_guest_name(child_name)
        child_guest: dict[str, object] = {
            "title-id": 2,
            "name": child_first,
            "surname": child_last,
            "birthday": _birthday_from_age(age, checkin_date),
        }
        guests.append(child_guest)
    return guests


def _build_booking_api_create_payload(hotel_id: int, draft: dict[str, Any]) -> dict[str, Any]:
    """Build booking API payload for `/hotel/{hotel_id}/createReservation`."""
    chd_ages = [max(0, _safe_int(age, 0)) for age in draft.get("chd_ages", []) if isinstance(age, int | str)]
    adult_count = max(_safe_int(draft.get("pms_adult_count", draft.get("adults")), 1), 1)
    pms_child_count = _safe_int(draft.get("pms_child_count"), -1)
    child_count = max(pms_child_count if pms_child_count >= 0 else len(chd_ages), 0)
    child_ages_for_payload: list[int] = []
    if child_count > 0 and chd_ages:
        # Prefer youngest ages when PMS reduced child-count after occupancy normalization.
        child_ages_for_payload = sorted(chd_ages)[:child_count]
    child_buckets = _child_bucket_counts(child_ages_for_payload) if child_ages_for_payload else {
        "elder_child_count": child_count,
        "younger_child_count": 0,
        "baby_count": 0,
    }
    payload: dict[str, Any] = {
        "hotel-id": hotel_id,
        "room-type-id": _safe_int(draft.get("room_type_id")),
        "board-type-id": _safe_int(draft.get("board_type_id")),
        "rate-type-id": _safe_int(draft.get("rate_type_id")),
        "rate-code-id": _safe_int(draft.get("rate_code_id")),
        "price-agency-id": _safe_int(draft.get("price_agency_id")),
        "currency-code": str(draft.get("currency_display") or draft.get("currency") or "EUR").strip() or "EUR",
        "total-price": _safe_float(draft.get("total_price_eur", draft.get("total_price"))),
        "adult-count": adult_count,
        "child-count": child_count,
        "check-in": _normalize_iso_date(draft.get("checkin_date")),
        "check-out": _normalize_iso_date(draft.get("checkout_date")),
        "guest-list": _booking_api_guest_list(
            draft,
            child_count=child_count if child_ages_for_payload else 0,
            child_ages=child_ages_for_payload,
        ),
    }
    if child_ages_for_payload:
        payload["child-ages"] = child_ages_for_payload
        age_csv = ",".join(str(age) for age in child_ages_for_payload)
        # Some Elektra environments expect child ages/count aliases used by quote endpoint.
        payload["chdCount"] = len(child_ages_for_payload)
        payload["child"] = len(child_ages_for_payload)
        payload["childage"] = age_csv
        payload["child-age"] = age_csv
        payload["chdAges"] = age_csv
        payload["children-count"] = len(child_ages_for_payload)
        payload["elder-child-count"] = child_buckets["elder_child_count"]
        payload["younger-child-count"] = child_buckets["younger_child_count"]
        payload["baby-count"] = child_buckets["baby_count"]
    nationality_code = str(draft.get("nationality") or "").strip()
    if nationality_code:
        payload["nationality-code"] = nationality_code
    notes = str(draft.get("notes") or "").strip()
    if notes:
        payload["notes"] = notes
    return payload


def _matches_cancel_policy(draft: dict[str, Any], offer: BookingOffer) -> bool:
    """Return True when an offer is compatible with the requested cancel policy."""
    return _cancel_policy_rank(draft, offer) < 99


def _normalize_policy_label(value: str) -> str:
    """Normalize Turkish/ASCII label variants for robust policy token matching."""
    normalized = value.casefold().replace("i̇", "i")
    translation = str.maketrans(
        {
            "ü": "u",
            "ı": "i",
            "ş": "s",
            "ç": "c",
            "ö": "o",
            "ğ": "g",
        }
    )
    return normalized.translate(translation)


def _cancel_policy_rank(draft: dict[str, Any], offer: BookingOffer) -> int:
    """Return priority rank for policy-compliant rate-type selection (lower is better)."""
    cancel_policy = str(draft.get("cancel_policy_type") or "").upper()
    label = _normalize_policy_label(offer.rate_type)
    refundable = bool((offer.cancellation_penalty or {}).get("is_refundable")) or offer.cancel_possible
    is_contract = "kontrat" in label
    if cancel_policy == "FREE_CANCEL":
        if refundable and any(token in label for token in ("ucretsiz iptal", "free cancel", "refundable")):
            return 0
        if refundable and not is_contract:
            return 1
        if refundable:
            return 2
        return 99
    if cancel_policy == "NON_REFUNDABLE":
        if any(token in label for token in ("iptal edilemez", "non refundable", "non-refundable", "nrf")):
            return 0
        if not refundable and not is_contract:
            return 1
        if not refundable:
            return 2
        return 99
    return 0


def _select_offer_for_cancel_policy(draft: dict[str, Any], offers: list[BookingOffer]) -> BookingOffer:
    """Select best offer for requested cancel policy while avoiding generic contract rates."""
    ranked = sorted(
        offers,
        key=lambda offer: (
            _cancel_policy_rank(draft, offer),
            float(offer.discounted_price or offer.price),
        ),
    )
    return ranked[0]


def _money_matches_offer(draft: dict[str, Any], offer: BookingOffer) -> bool:
    """Compare total against live offer price using a small tolerance."""
    expected_total = _safe_float(draft.get("total_price_eur", draft.get("total_price")))
    return any(abs(expected_total - candidate) < 0.01 for candidate in (float(offer.discounted_price), float(offer.price)))


def _offer_total_for_create(offer: BookingOffer) -> str:
    """Choose a safe create total from live offer prices."""
    candidates = [float(offer.discounted_price), float(offer.price)]
    positives = [value for value in candidates if value > 0]
    if positives:
        return str(min(positives))
    return str(offer.discounted_price or offer.price)


def _resolve_room_type_id_for_refresh(hotel_id: int, room_type_id: int) -> int:
    """Resolve profile room id into PMS room id when needed."""
    if room_type_id <= 0:
        return room_type_id
    profile = get_profile(hotel_id)
    if profile is None:
        return room_type_id
    for room_type in profile.room_types:
        if room_type.pms_room_type_id == room_type_id:
            return room_type_id
        if room_type.id == room_type_id and room_type.pms_room_type_id > 0:
            return int(room_type.pms_room_type_id)
    return room_type_id


async def _refresh_offer_identifiers(
    hotel_id: int,
    draft: dict[str, Any],
    *,
    prefer_money_match: bool = True,
) -> dict[str, Any] | None:
    """Reload live quote ids for stale holds when provider identifiers drift."""
    quote_response = await quote(
        hotel_id=hotel_id,
        checkin=date.fromisoformat(_normalize_iso_date(draft.get("checkin_date"))),
        checkout=date.fromisoformat(_normalize_iso_date(draft.get("checkout_date"))),
        adults=max(_safe_int(draft.get("adults"), 1), 1),
        chd_ages=[max(0, _safe_int(age, 0)) for age in draft.get("chd_ages", []) if isinstance(age, int | str)],
        currency=str(draft.get("currency_display") or draft.get("currency") or "EUR"),
        nationality=str(draft.get("nationality") or "TR"),
        cancel_policy_type=str(draft.get("cancel_policy_type") or "") or None,
    )
    room_type_id = _resolve_room_type_id_for_refresh(hotel_id, _safe_int(draft.get("room_type_id")))
    room_type_candidates = [
        offer
        for offer in quote_response.offers
        if offer.room_type_id == room_type_id
    ]
    if not room_type_candidates:
        # Fallback for stale profile/internal ids: use any sellable offers from live quote.
        room_type_candidates = [offer for offer in quote_response.offers if offer.room_to_sell > 0 and not offer.stop_sell]
    if not room_type_candidates:
        return None
    sellable_candidates = [offer for offer in room_type_candidates if offer.room_to_sell > 0 and not offer.stop_sell]
    if sellable_candidates:
        room_type_candidates = sellable_candidates
    candidates = (
        [offer for offer in room_type_candidates if _money_matches_offer(draft, offer)]
        if prefer_money_match
        else []
    )
    if not candidates:
        logger.info(
            "elektraweb_offer_identifier_refresh_without_price_match",
            hotel_id=hotel_id,
            room_type_id=room_type_id,
        )
        candidates = room_type_candidates

    preferred = _select_offer_for_cancel_policy(draft, candidates)
    refreshed = dict(draft)
    refreshed.update(
        {
            "room_type_id": preferred.room_type_id,
            "board_type_id": preferred.board_type_id,
            "rate_type_id": preferred.rate_type_id,
            "rate_code_id": preferred.rate_code_id,
            "price_agency_id": preferred.price_agency_id,
            "currency_display": preferred.currency_code,
            "total_price_eur": _offer_total_for_create(preferred),
        }
    )
    if preferred.pax_adult_count is not None and preferred.pax_adult_count > 0:
        refreshed["pms_adult_count"] = preferred.pax_adult_count
    if preferred.pax_child_count is not None and preferred.pax_child_count >= 0:
        refreshed["pms_child_count"] = preferred.pax_child_count
    logger.info(
        "elektraweb_offer_identifiers_refreshed",
        hotel_id=hotel_id,
        room_type_id=preferred.room_type_id,
        rate_type_id=preferred.rate_type_id,
        rate_code_id=preferred.rate_code_id,
        price_agency_id=preferred.price_agency_id,
        pms_adult_count=preferred.pax_adult_count,
        pms_child_count=preferred.pax_child_count,
    )
    return refreshed


def _needs_offer_refresh(error: httpx.HTTPStatusError) -> bool:
    """Return True when createReservation failure can be recovered by refreshing quote identifiers."""
    if error.response.status_code != 400:
        return False
    try:
        payload = error.response.json()
    except ValueError:
        return False
    message = str(payload.get("message") or "").casefold()
    return any(
        token in message
        for token in (
            "agency not found",
            "price quote",
            "must be",
        )
    )


def _is_price_mismatch_error(error: httpx.HTTPStatusError) -> bool:
    """Return True when provider rejects create because total price is stale."""
    if error.response.status_code != 400:
        return False
    try:
        payload = error.response.json()
    except ValueError:
        return False
    message = str(payload.get("message") or "").casefold()
    return "price quote" in message and "must be" in message


def _extract_expected_total_from_price_mismatch(error: httpx.HTTPStatusError) -> str | None:
    """Extract provider-required total from mismatch message, if present."""
    if not _is_price_mismatch_error(error):
        return None
    try:
        payload = error.response.json()
    except ValueError:
        return None
    message = str(payload.get("message") or "")
    match = re.search(r"must\s+be\s+([0-9]+(?:[.,][0-9]+)?)", message, flags=re.IGNORECASE)
    if match is None:
        return None
    return match.group(1).replace(",", ".")


def _with_price_override(draft: dict[str, Any], total_price: str | None) -> dict[str, Any]:
    """Return a draft copy with an overridden total-price when provider hints it explicitly."""
    if total_price is None:
        return draft
    updated = dict(draft)
    updated["total_price_eur"] = total_price
    return updated


def _build_hoteladvisor_insert_payload(hotel_id: int, draft: dict[str, Any]) -> dict[str, Any]:
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


def _build_hoteladvisor_guest_payload(
    hotel_id: int,
    reservation_id: str,
    draft: dict[str, Any],
) -> dict[str, Any] | None:
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


async def create_reservation(hotel_id: int, draft: dict[str, Any]) -> ReservationResponse:
    """Create reservation in Elektraweb with booking API primary and HotelAdvisor fallback."""
    client = get_elektraweb_client()
    last_error: Exception | None = None

    booking_api_payload = _build_booking_api_create_payload(hotel_id, draft)

    paths = [
        f"/hotel/{hotel_id}/createReservation",
        f"/hotel/{hotel_id}/reservation/create",
        f"/hotel/{hotel_id}/reservations/create",
    ]

    for path in paths:
        try:
            logger.info("elektraweb_create_reservation_attempt", hotel_id=hotel_id, path=path)
            raw = await client.post(path, json_body=booking_api_payload)
            return parse_reservation_create(raw)
        except httpx.HTTPStatusError as error:
            logger.warning("elektraweb_create_reservation_path_failed", path=path, error=str(error))
            last_error = error
            if _needs_offer_refresh(error):
                refreshed_draft = await _refresh_offer_identifiers(
                    hotel_id,
                    draft,
                    prefer_money_match=not _is_price_mismatch_error(error),
                )
                if refreshed_draft is not None:
                    logger.info("elektraweb_create_reservation_retry_refreshed_offer", hotel_id=hotel_id, path=path)
                    try:
                        expected_total = None
                        raw = await client.post(
                            path,
                            json_body=_build_booking_api_create_payload(hotel_id, refreshed_draft),
                        )
                        return parse_reservation_create(raw)
                    except Exception as retry_error:  # pragma: no cover - exercised via integration tests
                        if isinstance(retry_error, httpx.HTTPStatusError):
                            expected_total = _extract_expected_total_from_price_mismatch(retry_error)
                        if isinstance(retry_error, httpx.HTTPStatusError) and _is_price_mismatch_error(retry_error):
                            second_refresh = await _refresh_offer_identifiers(
                                hotel_id,
                                refreshed_draft,
                                prefer_money_match=False,
                            )
                            if second_refresh is not None:
                                second_refresh_payload = _with_price_override(second_refresh, expected_total)
                                logger.info(
                                    "elektraweb_create_reservation_retry_second_refresh",
                                    hotel_id=hotel_id,
                                    path=path,
                                    expected_total=expected_total,
                                )
                                try:
                                    raw = await client.post(
                                        path,
                                        json_body=_build_booking_api_create_payload(hotel_id, second_refresh_payload),
                                    )
                                    return parse_reservation_create(raw)
                                except Exception as second_retry_error:
                                    if isinstance(second_retry_error, httpx.HTTPStatusError):
                                        last_expected_total = _extract_expected_total_from_price_mismatch(second_retry_error)
                                        if last_expected_total is not None and last_expected_total != expected_total:
                                            final_price_payload = _with_price_override(
                                                second_refresh_payload,
                                                last_expected_total,
                                            )
                                            logger.info(
                                                "elektraweb_create_reservation_retry_price_override",
                                                hotel_id=hotel_id,
                                                path=path,
                                                expected_total=last_expected_total,
                                            )
                                            try:
                                                raw = await client.post(
                                                    path,
                                                    json_body=_build_booking_api_create_payload(
                                                        hotel_id,
                                                        final_price_payload,
                                                    ),
                                                )
                                                return parse_reservation_create(raw)
                                            except Exception as final_retry_error:
                                                logger.warning(
                                                    "elektraweb_create_reservation_retry_price_override_failed",
                                                    hotel_id=hotel_id,
                                                    path=path,
                                                    error=str(final_retry_error),
                                                )
                                                last_error = final_retry_error
                                    logger.warning(
                                        "elektraweb_create_reservation_retry_second_refresh_failed",
                                        hotel_id=hotel_id,
                                        path=path,
                                        error=str(second_retry_error),
                                    )
                                    last_error = second_retry_error
                        logger.warning(
                            "elektraweb_create_reservation_retry_refreshed_offer_failed",
                            hotel_id=hotel_id,
                            path=path,
                            error=str(retry_error),
                        )
                        last_error = retry_error
            # Continue trying alternative booking paths and HotelAdvisor fallback.
            continue
        except Exception as error:
            logger.warning("elektraweb_create_reservation_path_failed", path=path, error=str(error))
            last_error = error

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

    reservation_list_path = f"/hotel/{hotel_id}/reservation-list"
    reservation_statuses = ("Reservation", "Waiting", "InHouse", "CheckOut", "No Show", "Cancelled")
    paths_and_methods: list[tuple[str, str]] = [
        ("POST", f"/hotel/{hotel_id}/getReservation"),
        ("GET", f"/hotel/{hotel_id}/reservation/{reservation_id or ''}"),
        ("GET", f"/hotel/{hotel_id}/reservation/detail"),
        ("POST", f"/hotel/{hotel_id}/get-reservation"),
        ("POST", f"/hotel/{hotel_id}/reservation/get"),
    ]

    last_error: Exception | None = None
    for reservation_status in reservation_statuses:
        try:
            params = _reservation_lookup_params(
                reservation_status=reservation_status,
                reservation_id=reservation_id,
                voucher_no=voucher_no,
            )
            logger.info(
                "elektraweb_get_reservation_attempt",
                hotel_id=hotel_id,
                path=reservation_list_path,
                method="GET",
                reservation_status=reservation_status,
            )
            raw = await client.get(reservation_list_path, params=params)
            parsed = _parse_reservation_lookup_response(
                raw,
                reservation_id=reservation_id,
                voucher_no=voucher_no,
            )
            if parsed.success:
                return parsed
            raise RuntimeError("reservation_not_found_in_list")
        except Exception as error:
            logger.warning(
                "elektraweb_get_reservation_path_failed",
                path=reservation_list_path,
                error=str(error),
                reservation_status=reservation_status,
            )
            last_error = error

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


async def modify_reservation(
    hotel_id: int,
    reservation_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
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


async def cancel_reservation(hotel_id: int, reservation_id: str, reason: str) -> dict[str, Any]:
    """Cancel an existing reservation."""
    client = get_elektraweb_client()
    body = {"reservationId": reservation_id, "reason": reason}
    logger.info("elektraweb_cancel_reservation_request", hotel_id=hotel_id, reservation_id=reservation_id)
    return await client.post(f"/hotel/{hotel_id}/cancelReservation", json_body=body)
