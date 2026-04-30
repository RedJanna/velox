"""Deterministic stay quote guard that cross-checks price offers with availability."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import orjson
import structlog

from velox.core.hotel_profile_loader import get_profile

logger = structlog.get_logger(__name__)

TR_NO_AVAILABLE_ROOM_FOR_QUOTE = (
    "Belirttiğiniz tarih ve kişi sayısı için canlı müsaitlikte satılabilir oda görünmüyor. "
    "Konuyu ekibimize iletiyorum; en kısa sürede size dönüş yapılacak."
)
EN_NO_AVAILABLE_ROOM_FOR_QUOTE = (
    "I cannot verify a sellable room for those dates and guest count from live availability. "
    "I am forwarding this to our team so they can assist you shortly."
)

_BOOKING_TOOL_NAMES = {"booking_quote", "booking_availability"}
_FREE_CANCEL_HINTS = ("free", "ücretsiz", "ucretsiz", "cancel possible", "cancel_possible")
_NON_REFUNDABLE_HINTS = ("non", "refundable", "iptal edilemez", "iade", "kontrat")


@dataclass(frozen=True)
class GuardedStayQuote:
    """Guarded quote output built from executed quote and availability tools."""

    messages: list[str]
    available_room_type_ids: list[int]
    handoff_reason: str | None = None


def loads_tool_payload(value: Any) -> dict[str, Any]:
    """Return a dict from executed tool payloads stored as dicts or JSON strings."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            loaded = orjson.loads(value)
        except orjson.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}


def executed_booking_tool_names(executed_calls: list[dict[str, Any]]) -> set[str]:
    """Return executed booking tool names that can ground live stay claims."""
    return {
        str(call.get("name") or "").strip()
        for call in executed_calls
        if str(call.get("name") or "").strip() in _BOOKING_TOOL_NAMES
    }


def latest_booking_quote_args(executed_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return latest booking_quote arguments."""
    for call in reversed(executed_calls):
        if str(call.get("name") or "") != "booking_quote":
            continue
        args = loads_tool_payload(call.get("arguments"))
        if args:
            return args
    return {}


async def backfill_availability_for_quote(
    *,
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], Awaitable[str]],
) -> bool:
    """Add a booking_availability call when quote ran without availability grounding."""
    if any(str(call.get("name") or "") == "booking_availability" for call in executed_calls):
        return False
    quote_args = latest_booking_quote_args(executed_calls)
    if not quote_args:
        return False

    checkin_date = str(quote_args.get("checkin_date") or "").strip()
    checkout_date = str(quote_args.get("checkout_date") or "").strip()
    adults = _to_int(quote_args.get("adults"), 0)
    if not checkin_date or not checkout_date or adults <= 0:
        return False

    availability_args: dict[str, Any] = {
        "hotel_id": hotel_id,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults": adults,
        "chd_count": _to_int(quote_args.get("chd_count"), 0),
        "chd_ages": quote_args.get("chd_ages") if isinstance(quote_args.get("chd_ages"), list) else [],
        "currency": str(quote_args.get("currency") or "EUR").upper(),
    }
    result = await tool_executor("booking_availability", availability_args)
    executed_calls.append({"name": "booking_availability", "arguments": availability_args, "result": result})
    return True


def build_guarded_stay_quote(
    *,
    hotel_id: int,
    executed_calls: list[dict[str, Any]],
    language: str,
) -> GuardedStayQuote | None:
    """Build a deterministic stay quote message after availability filtering."""
    payloads = _extract_quote_call_payloads(executed_calls)
    if not payloads:
        offers = _extract_quote_offers(executed_calls)
        if not offers:
            return None
        payloads = [{"arguments": {}, "offers": offers}]

    has_availability_call = _has_booking_availability_call(executed_calls)
    if has_availability_call and _availability_failed(executed_calls):
        return GuardedStayQuote(
            messages=[_no_available_message(language)],
            available_room_type_ids=[],
            handoff_reason="live_availability_unverified",
        )

    available_room_type_ids = _extract_available_room_type_ids(executed_calls)
    if has_availability_call and not available_room_type_ids:
        if _has_nonempty_availability_inventory(executed_calls):
            return GuardedStayQuote(
                messages=[_no_available_message(language)],
                available_room_type_ids=[],
                handoff_reason="no_sellable_room_type",
            )
        fallback_ids = _extract_quote_fallback_room_type_ids(payloads)
        if not fallback_ids:
            return GuardedStayQuote(
                messages=[_no_available_message(language)],
                available_room_type_ids=[],
                handoff_reason="no_sellable_room_type",
            )
        available_room_type_ids = fallback_ids

    filtered_payloads = _filter_quote_payloads_by_available_room_types(payloads, available_room_type_ids)
    if not filtered_payloads and has_availability_call:
        return GuardedStayQuote(
            messages=[_no_available_message(language)],
            available_room_type_ids=[],
            handoff_reason="quote_availability_mismatch",
        )

    messages = _format_quote_messages(hotel_id, filtered_payloads, language)
    if not messages:
        return None
    return GuardedStayQuote(messages=messages, available_room_type_ids=available_room_type_ids)


def _extract_quote_offers(executed_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for call in reversed(executed_calls):
        if str(call.get("name") or "") != "booking_quote":
            continue
        offers = loads_tool_payload(call.get("result")).get("offers")
        if isinstance(offers, list):
            return [item for item in offers if isinstance(item, dict)]
    return []


def _extract_quote_call_payloads(executed_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_quote":
            continue
        offers = loads_tool_payload(call.get("result")).get("offers")
        if not isinstance(offers, list):
            continue
        parsed_offers = [item for item in offers if isinstance(item, dict)]
        if parsed_offers:
            payloads.append({"arguments": loads_tool_payload(call.get("arguments")), "offers": parsed_offers})
    return payloads


def _has_booking_availability_call(executed_calls: list[dict[str, Any]]) -> bool:
    return any(str(call.get("name") or "") == "booking_availability" for call in executed_calls)


def _availability_failed(executed_calls: list[dict[str, Any]]) -> bool:
    availability_results = [
        loads_tool_payload(call.get("result"))
        for call in executed_calls
        if str(call.get("name") or "") == "booking_availability"
    ]
    return bool(availability_results) and all(bool(result.get("error")) for result in availability_results)


def _extract_available_room_type_ids(executed_calls: list[dict[str, Any]]) -> list[int]:
    room_type_ids: list[int] = []
    seen: set[int] = set()
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_availability":
            continue
        result = loads_tool_payload(call.get("result"))
        args = loads_tool_payload(call.get("arguments"))
        required_dates = _required_stay_dates(args)
        rows = result.get("rows")
        rows = rows if isinstance(rows, list) else []

        room_date_coverage: dict[int, set[str]] = {}
        positive_rooms: set[int] = set()
        has_row_dates = False
        for row in rows:
            if not isinstance(row, dict):
                continue
            room_type_id = _to_int(row.get("room_type_id"), 0)
            if room_type_id <= 0 or bool(row.get("stop_sell")) or _to_int(row.get("room_to_sell"), 0) <= 0:
                continue
            positive_rooms.add(room_type_id)
            row_date = str(row.get("date") or "").strip()
            if row_date:
                has_row_dates = True
                room_date_coverage.setdefault(room_type_id, set()).add(row_date)

        eligible_ids = set(positive_rooms)
        if required_dates and has_row_dates:
            eligible_ids = {
                room_type_id
                for room_type_id, covered_dates in room_date_coverage.items()
                if required_dates.issubset(covered_dates)
            }

        for room_type_id in sorted(eligible_ids):
            if room_type_id not in seen:
                seen.add(room_type_id)
                room_type_ids.append(room_type_id)
    return room_type_ids


def _has_nonempty_availability_inventory(executed_calls: list[dict[str, Any]]) -> bool:
    for call in executed_calls:
        if str(call.get("name") or "") != "booking_availability":
            continue
        result = loads_tool_payload(call.get("result"))
        rows = result.get("rows")
        if isinstance(rows, list) and rows:
            return True
        derived = result.get("derived")
        eligible_ids = derived.get("eligible_room_type_ids") if isinstance(derived, dict) else None
        if isinstance(eligible_ids, list) and eligible_ids:
            return True
    return False


def _filter_quote_payloads_by_available_room_types(
    payloads: list[dict[str, Any]],
    available_room_type_ids: list[int],
) -> list[dict[str, Any]]:
    if not available_room_type_ids:
        return payloads
    allowed = set(available_room_type_ids)
    filtered_payloads: list[dict[str, Any]] = []
    for payload in payloads:
        offers = payload.get("offers")
        if not isinstance(offers, list):
            continue
        filtered_offers = [
            offer
            for offer in offers
            if isinstance(offer, dict) and _to_int(offer.get("room_type_id"), 0) in allowed
        ]
        if filtered_offers:
            filtered_payloads.append({"arguments": payload.get("arguments", {}), "offers": filtered_offers})
    return filtered_payloads


def _extract_quote_fallback_room_type_ids(payloads: list[dict[str, Any]]) -> list[int]:
    explicit_sellable_ids: list[int] = []
    implicit_offer_ids: list[int] = []
    seen_explicit: set[int] = set()
    seen_implicit: set[int] = set()
    for payload in payloads:
        offers = payload.get("offers")
        if not isinstance(offers, list):
            continue
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            room_type_id = _to_int(offer.get("room_type_id"), 0)
            if room_type_id <= 0:
                continue
            has_room_to_sell = offer.get("room_to_sell") is not None
            has_stop_sell = offer.get("stop_sell") is not None
            if has_stop_sell and bool(offer.get("stop_sell")):
                continue
            if has_room_to_sell and _to_int(offer.get("room_to_sell"), 0) <= 0:
                continue
            if has_room_to_sell or has_stop_sell:
                if room_type_id not in seen_explicit:
                    seen_explicit.add(room_type_id)
                    explicit_sellable_ids.append(room_type_id)
                continue
            if room_type_id not in seen_implicit:
                seen_implicit.add(room_type_id)
                implicit_offer_ids.append(room_type_id)
    return explicit_sellable_ids or implicit_offer_ids


def _format_quote_messages(hotel_id: int, payloads: list[dict[str, Any]], language: str) -> list[str]:
    messages: list[str] = []
    for payload in payloads:
        offers = payload.get("offers")
        if not isinstance(offers, list) or not offers:
            continue
        args = payload.get("arguments") if isinstance(payload.get("arguments"), dict) else {}
        grouped = _best_offers_by_room(hotel_id, offers)
        if not grouped:
            continue
        messages.append(_format_single_quote_message(hotel_id, grouped, args, language))
    return messages


def _best_offers_by_room(hotel_id: int, offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_room: dict[int, dict[str, Any]] = {}
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        room_type_id = _to_int(offer.get("room_type_id"), 0)
        if room_type_id <= 0:
            continue
        room_bucket = best_by_room.setdefault(room_type_id, {"room_type_id": room_type_id, "offers": []})
        room_bucket["offers"].append(offer)

    profile = get_profile(hotel_id)
    room_order = {}
    if profile is not None:
        room_order = {
            _to_int(getattr(room, "pms_room_type_id", 0), 0): index
            for index, room in enumerate(getattr(profile, "room_types", []))
        }
    return sorted(best_by_room.values(), key=lambda item: room_order.get(_to_int(item["room_type_id"], 0), 9999))


def _format_single_quote_message(
    hotel_id: int,
    grouped_rooms: list[dict[str, Any]],
    args: dict[str, Any],
    language: str,
) -> str:
    is_english = str(language or "").lower() == "en"
    lines = _quote_header(args, is_english)
    for room in grouped_rooms:
        selected = _select_room_policy_offers(room["offers"])
        if not selected:
            continue
        lines.append("")
        lines.append(_room_label(hotel_id, _to_int(room["room_type_id"], 0), selected[0], is_english))
        for offer in selected:
            lines.append(f"{_policy_label(offer, is_english)}: {_format_offer_price(offer)}")
    return "\n".join(lines).strip()


def _quote_header(args: dict[str, Any], is_english: bool) -> list[str]:
    checkin = str(args.get("checkin_date") or "").strip()
    checkout = str(args.get("checkout_date") or "").strip()
    nights = _nights_between(checkin, checkout)
    adults = _to_int(args.get("adults"), 0)
    children = _to_int(args.get("chd_count"), 0)
    occupancy = _occupancy_label(adults, children, is_english)
    if is_english:
        lines = ["Thank you for your interest in our hotel."]
        if checkin and checkout and nights > 0 and adults > 0:
            lines.extend(
                [
                    "",
                    f"For {nights} night(s), {checkin} - {checkout},",
                    f"our breakfast-included rates for {occupancy} are:",
                ]
            )
        return lines
    lines = ["Otelimize göstermiş olduğunuz ilgi için teşekkür ederiz."]
    if checkin and checkout and nights > 0 and adults > 0:
        lines.extend(
            [
                "",
                f"{checkin} - {checkout} tarihleri arasında {nights} gece",
                f"kahvaltı dahil {occupancy} fiyatlarımız aşağıdaki gibidir;",
            ]
        )
    return lines


def _select_room_policy_offers(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for offer in offers:
        policy = _policy_key(offer)
        current = buckets.get(policy)
        if current is None or _price_decimal(offer) < _price_decimal(current):
            buckets[policy] = offer
    ordered: list[dict[str, Any]] = []
    for key in ("non_refundable", "free_cancel", "other"):
        offer = buckets.get(key)
        if offer is not None:
            ordered.append(offer)
    return ordered


def _policy_key(offer: dict[str, Any]) -> str:
    rate_text = " ".join(
        str(offer.get(key) or "").lower()
        for key in ("rate_type", "rate_code", "cancel_policy_type")
    )
    if bool(offer.get("cancel_possible")) or any(hint in rate_text for hint in _FREE_CANCEL_HINTS):
        return "free_cancel"
    if any(hint in rate_text for hint in _NON_REFUNDABLE_HINTS) or offer.get("cancel_possible") is False:
        return "non_refundable"
    return "other"


def _policy_label(offer: dict[str, Any], is_english: bool) -> str:
    policy = _policy_key(offer)
    if is_english:
        return {"free_cancel": "Free cancellation", "non_refundable": "Non-refundable"}.get(policy, "Rate")
    return {"free_cancel": "Ücretsiz İptal", "non_refundable": "İptal edilemez"}.get(policy, "Fiyat")


def _room_label(hotel_id: int, room_type_id: int, offer: dict[str, Any], is_english: bool) -> str:
    profile_room = _find_profile_room(hotel_id, room_type_id)
    if profile_room is not None:
        name_obj = getattr(profile_room, "name", None)
        name = str(getattr(name_obj, "en" if is_english else "tr", "") or getattr(name_obj, "tr", "") or "").strip()
        size_m2 = _to_int(getattr(profile_room, "size_m2", 0), 0)
    else:
        name = str(offer.get("room_type") or f"Room {room_type_id}").replace("_", " ").title()
        size_m2 = _to_int(offer.get("room_area"), 0)
    return f"{name} ({size_m2}m2)" if size_m2 > 0 else name


def _find_profile_room(hotel_id: int, room_type_id: int) -> Any | None:
    profile = get_profile(hotel_id)
    if profile is None:
        return None
    for room in getattr(profile, "room_types", []):
        if _to_int(getattr(room, "pms_room_type_id", 0), 0) == room_type_id:
            return room
    return None


def _format_offer_price(offer: dict[str, Any]) -> str:
    amount = _price_decimal(offer).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    currency = str(offer.get("currency_code") or offer.get("currency") or "EUR").upper()
    symbol = "€" if currency == "EUR" else currency
    return f"{amount} {symbol}"


def _price_decimal(offer: dict[str, Any]) -> Decimal:
    raw = offer.get("discounted_price", offer.get("price", 0))
    try:
        return Decimal(str(raw or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _required_stay_dates(args: dict[str, Any]) -> set[str]:
    checkin_raw = str(args.get("checkin_date") or "").strip()
    checkout_raw = str(args.get("checkout_date") or "").strip()
    try:
        checkin_date = date.fromisoformat(checkin_raw)
        checkout_date = date.fromisoformat(checkout_raw)
    except ValueError:
        return set()
    dates: set[str] = set()
    cursor = checkin_date
    while cursor < checkout_date:
        dates.add(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


def _nights_between(checkin: str, checkout: str) -> int:
    try:
        return (date.fromisoformat(checkout) - date.fromisoformat(checkin)).days
    except ValueError:
        return 0


def _occupancy_label(adults: int, children: int, is_english: bool) -> str:
    if is_english:
        child_part = f" and {children} child(ren)" if children else ""
        return f"{adults} adult(s){child_part}"
    child_part = f", {children} çocuk" if children else ""
    return f"{adults} yetişkin{child_part}"


def _no_available_message(language: str) -> str:
    return EN_NO_AVAILABLE_ROOM_FOR_QUOTE if str(language or "").lower() == "en" else TR_NO_AVAILABLE_ROOM_FOR_QUOTE


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, (str, bytes, bytearray)):
            return int(value)
    except (TypeError, ValueError):
        return default
    return default
