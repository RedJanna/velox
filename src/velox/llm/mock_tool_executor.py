"""Mock tool executor for test/development environment.

Returns realistic stub data so the LLM can complete the full
booking / restaurant / transfer conversation flow without a
real PMS or back-end connection.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Pricing tables (EUR per night per room type)
# Source: Elektraweb PMS — Kassandra Oludeniz (June 2026, %30 early-bird)
#
# Prices are stored as BASE rates for STANDARD occupancy (2 adults).
# Extra adults are charged a per-night supplement on top.
# Elektraweb screenshots were taken for 3 adults, so:
#   base_2pax = elektraweb_3pax_price − EXTRA_ADULT_PER_NIGHT
# ---------------------------------------------------------------------------
_STD_OCCUPANCY = 2
_EXTRA_ADULT_PER_NIGHT = 35.0       # EUR, after 30% discount
_EXTRA_ADULT_RACK_PER_NIGHT = 50.0  # EUR, before discount
_DISCOUNT_PERCENT = 30

# Per-night BASE prices for 2 adults (discounted)
_ROOM_BASE_PRICES: dict[int, dict[str, float]] = {
    # pms_room_type_id -> { cancel_policy -> base_price_per_night_eur }
    60: {"FREE_CANCEL": 196.0, "NON_REFUNDABLE": 175.0},     # Deluxe         (25m²)
    61: {"FREE_CANCEL": 203.7, "NON_REFUNDABLE": 182.0},     # Superior       (30m²)
    62: {"FREE_CANCEL": 211.4, "NON_REFUNDABLE": 189.0},     # Exclusive Land (40m²)
    63: {"FREE_CANCEL": 207.0, "NON_REFUNDABLE": 185.0},     # Penthouse Land (25m², jakuzi)
    64: {"FREE_CANCEL": 219.1, "NON_REFUNDABLE": 196.0},     # Exclusive Pool (40m²)
    65: {"FREE_CANCEL": 230.65, "NON_REFUNDABLE": 206.5},    # Penthouse      (45m², jakuzi, teras)
    66: {"FREE_CANCEL": 242.2, "NON_REFUNDABLE": 217.0},     # Premium        (40m², jakuzi)
}

# Per-night BASE rack rates for 2 adults (before discount)
_ROOM_BASE_RACK_RATES: dict[int, dict[str, float]] = {
    60: {"FREE_CANCEL": 280.0, "NON_REFUNDABLE": 250.0},
    61: {"FREE_CANCEL": 291.0, "NON_REFUNDABLE": 260.0},
    62: {"FREE_CANCEL": 302.0, "NON_REFUNDABLE": 270.0},
    63: {"FREE_CANCEL": 296.0, "NON_REFUNDABLE": 264.0},
    64: {"FREE_CANCEL": 313.0, "NON_REFUNDABLE": 280.0},
    65: {"FREE_CANCEL": 329.5, "NON_REFUNDABLE": 295.0},
    66: {"FREE_CANCEL": 346.0, "NON_REFUNDABLE": 310.0},
}


def _price_for_pax(base: float, adults: int) -> float:
    """Calculate per-night price adjusted for adult count."""
    extra = max(0, adults - _STD_OCCUPANCY)
    return round(base + extra * _EXTRA_ADULT_PER_NIGHT, 2)


def _rack_for_pax(rack_base: float, adults: int) -> float:
    """Calculate per-night rack price adjusted for adult count."""
    extra = max(0, adults - _STD_OCCUPANCY)
    return round(rack_base + extra * _EXTRA_ADULT_RACK_PER_NIGHT, 2)

_ROOM_NAMES: dict[int, str] = {
    60: "Deluxe",
    61: "Superior",
    62: "Exclusive Land",
    63: "Penthouse Land",
    64: "Exclusive Pool",
    65: "Penthouse",
    66: "Premium",
}

_RATE_MAP = {
    "FREE_CANCEL": {"rate_type_id": 10, "rate_code_id": 101},
    "NON_REFUNDABLE": {"rate_type_id": 11, "rate_code_id": 102},
}

_BOARD_TYPE = {"id": 2, "code": "BB", "name": "Oda Kahvalti / Bed & Breakfast"}
_PRICE_AGENCY_ID = 1
_HOTEL_ID = 21966

_SEASON_OPEN = (4, 20)   # April 20
_SEASON_CLOSE = (11, 10)  # November 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _in_season(date_str: str) -> bool:
    """Check if a date string falls within the hotel season."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False
    open_dt = dt.replace(month=_SEASON_OPEN[0], day=_SEASON_OPEN[1])
    close_dt = dt.replace(month=_SEASON_CLOSE[0], day=_SEASON_CLOSE[1])
    return open_dt <= dt <= close_dt


def _nights(checkin: str, checkout: str) -> int:
    try:
        ci = datetime.strptime(checkin, "%Y-%m-%d")
        co = datetime.strptime(checkout, "%Y-%m-%d")
        return max((co - ci).days, 1)
    except ValueError:
        return 1


def _mock_id() -> str:
    return uuid.uuid4().hex[:12].upper()


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _booking_availability(args: dict[str, Any]) -> dict[str, Any]:
    checkin = args.get("checkin_date", "")
    checkout = args.get("checkout_date", "")
    adults = args.get("adults", 2)

    if not _in_season(checkin) or not _in_season(checkout):
        return {
            "available": False,
            "reason": "requested_dates_outside_season",
            "season": {"open": "04-20", "close": "11-10"},
        }

    nights = _nights(checkin, checkout)
    rooms = []
    for pms_id, base_prices in _ROOM_BASE_PRICES.items():
        rack_base = _ROOM_BASE_RACK_RATES[pms_id]
        for policy in ("FREE_CANCEL", "NON_REFUNDABLE"):
            ppn = _price_for_pax(base_prices[policy], adults)
            rack_ppn = _rack_for_pax(rack_base[policy], adults)
            rooms.append({
                "room_type_id": pms_id,
                "room_name": _ROOM_NAMES[pms_id],
                "available": True,
                "remaining_units": 3,
                "adults": adults,
                "cancel_policy": policy,
                "rack_price_per_night_eur": rack_ppn,
                "discount_percent": _DISCOUNT_PERCENT,
                "price_per_night_eur": ppn,
                "total_rack_price_eur": round(rack_ppn * nights, 2),
                "total_price_eur": round(ppn * nights, 2),
                "savings_eur": round((rack_ppn - ppn) * nights, 2),
                "board": _BOARD_TYPE["code"],
            })
    return {
        "available": True,
        "checkin_date": checkin,
        "checkout_date": checkout,
        "nights": nights,
        "adults": adults,
        "discount_campaign": f"%{_DISCOUNT_PERCENT} Early Bird Indirimi",
        "rooms": rooms,
    }


def _booking_quote(args: dict[str, Any]) -> dict[str, Any]:
    checkin = args.get("checkin_date", "")
    checkout = args.get("checkout_date", "")
    adults = args.get("adults", 2)
    nights = _nights(checkin, checkout)

    if not _in_season(checkin):
        return {"error": "dates_outside_season"}

    offers = []
    for pms_id, base_prices in _ROOM_BASE_PRICES.items():
        rack_base = _ROOM_BASE_RACK_RATES[pms_id]
        for policy in ("FREE_CANCEL", "NON_REFUNDABLE"):
            ppn = _price_for_pax(base_prices[policy], adults)
            rack_ppn = _rack_for_pax(rack_base[policy], adults)
            total = round(ppn * nights, 2)
            rack_total = round(rack_ppn * nights, 2)
            rate_info = _RATE_MAP.get(policy, _RATE_MAP["FREE_CANCEL"])
            offers.append({
                "room_type_id": pms_id,
                "room_name": _ROOM_NAMES[pms_id],
                "board_type_id": _BOARD_TYPE["id"],
                "board_code": _BOARD_TYPE["code"],
                "rate_type_id": rate_info["rate_type_id"],
                "rate_code_id": rate_info["rate_code_id"],
                "price_agency_id": _PRICE_AGENCY_ID,
                "adults": adults,
                "rack_price_per_night_eur": rack_ppn,
                "discount_percent": _DISCOUNT_PERCENT,
                "price_per_night_eur": ppn,
                "total_rack_price_eur": rack_total,
                "total_price_eur": total,
                "savings_eur": round(rack_total - total, 2),
                "currency": "EUR",
                "cancel_policy": policy,
                "cancel_deadline": (
                    (datetime.strptime(checkin, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
                    if policy == "FREE_CANCEL" else None
                ),
            })

    return {
        "hotel_id": _HOTEL_ID,
        "checkin_date": checkin,
        "checkout_date": checkout,
        "nights": nights,
        "adults": adults,
        "discount_campaign": f"%{_DISCOUNT_PERCENT} Early Bird Indirimi",
        "offers": offers,
    }


def _stay_create_hold(args: dict[str, Any]) -> dict[str, Any]:
    draft = args.get("draft", {})
    return {
        "status": "HOLD_CREATED",
        "hold_id": f"HOLD-{_mock_id()}",
        "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat() + "Z",
        "summary": {
            "room": _ROOM_NAMES.get(draft.get("room_type_id", 0), "Unknown"),
            "checkin": draft.get("checkin_date"),
            "checkout": draft.get("checkout_date"),
            "total_eur": draft.get("total_price_eur"),
            "guest": draft.get("guest_name"),
        },
        "next_step": "approval_request",
    }


def _booking_create_reservation(args: dict[str, Any]) -> dict[str, Any]:
    draft = args.get("draft", {})
    return {
        "status": "CONFIRMED",
        "reservation_id": f"RES-{_mock_id()}",
        "voucher_no": f"VCH-{_mock_id()}",
        "checkin": draft.get("checkin_date"),
        "checkout": draft.get("checkout_date"),
        "room": _ROOM_NAMES.get(draft.get("room_type_id", 0), "Unknown"),
        "total_eur": draft.get("total_price", 0),
    }


def _booking_get_reservation(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "reservation_id": args.get("reservation_id", f"RES-{_mock_id()}"),
        "status": "CONFIRMED",
        "guest_name": "Test Misafir",
        "checkin": "2026-05-25",
        "checkout": "2026-05-28",
        "room": "Deluxe",
        "total_eur": 255.0,
    }


def _booking_modify(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "MODIFIED", "updates_applied": args.get("updates", {})}


def _booking_cancel(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "CANCELLED", "reason": args.get("reason", "guest_request")}


def _restaurant_availability(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "available": True,
        "slot_id": f"SLOT-{_mock_id()}",
        "date": args.get("date"),
        "time": args.get("time"),
        "party_size": args.get("party_size", 2),
        "area": args.get("area", "outdoor"),
    }


def _restaurant_create_hold(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "HOLD_CREATED",
        "restaurant_hold_id": f"RHOLD-{_mock_id()}",
        "slot_id": args.get("slot_id"),
        "next_step": "approval_request",
    }


def _restaurant_confirm(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "CONFIRMED", "restaurant_hold_id": args.get("restaurant_hold_id")}


def _restaurant_modify(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "MODIFIED", "restaurant_hold_id": args.get("restaurant_hold_id")}


def _restaurant_cancel(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "CANCELLED", "restaurant_hold_id": args.get("restaurant_hold_id")}


_TRANSFER_PRICES = {
    "DALAMAN_AIRPORT_TO_HOTEL": 75,
    "HOTEL_TO_DALAMAN_AIRPORT": 75,
    "ANTALYA_AIRPORT_TO_HOTEL": 220,
    "HOTEL_TO_ANTALYA_AIRPORT": 220,
}

_TRANSFER_DURATIONS = {
    "DALAMAN_AIRPORT_TO_HOTEL": 75,
    "HOTEL_TO_DALAMAN_AIRPORT": 75,
    "ANTALYA_AIRPORT_TO_HOTEL": 240,
    "HOTEL_TO_ANTALYA_AIRPORT": 240,
}


def _transfer_get_info(args: dict[str, Any]) -> dict[str, Any]:
    route = args.get("route", "")
    pax = args.get("pax_count", 2)
    price = _TRANSFER_PRICES.get(route, 0)
    vehicle = "Sprinter" if pax >= 8 else "Vito"
    if pax >= 8 and "DALAMAN" in route:
        price = 100
    return {
        "route": route,
        "price_eur": price,
        "vehicle_type": vehicle,
        "max_pax": 7 if vehicle == "Vito" else 14,
        "duration_min": _TRANSFER_DURATIONS.get(route, 0),
        "baby_seat_available": True,
    }


def _transfer_create_hold(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "HOLD_CREATED",
        "transfer_hold_id": f"THOLD-{_mock_id()}",
        "route": args.get("route"),
        "date": args.get("date"),
        "time": args.get("time"),
        "next_step": "approval_request",
    }


def _transfer_confirm(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "CONFIRMED", "transfer_hold_id": args.get("transfer_hold_id")}


def _transfer_modify(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "MODIFIED", "transfer_hold_id": args.get("transfer_hold_id")}


def _transfer_cancel(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "CANCELLED", "transfer_hold_id": args.get("transfer_hold_id")}


def _approval_request(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PENDING_APPROVAL",
        "approval_id": f"APR-{_mock_id()}",
        "type": args.get("approval_type"),
        "reference_id": args.get("reference_id"),
    }


def _payment_request_prepayment(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PAYMENT_REQUESTED",
        "payment_id": f"PAY-{_mock_id()}",
        "amount_eur": args.get("amount"),
        "methods": args.get("methods", []),
    }


def _notify_send(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "SENT", "to_role": args.get("to_role"), "channel": args.get("channel")}


def _handoff_create_ticket(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "TICKET_CREATED",
        "ticket_id": f"TKT-{_mock_id()}",
        "reason": args.get("reason"),
    }


def _crm_log(args: dict[str, Any]) -> dict[str, Any]:
    return {"status": "LOGGED", "intent": args.get("intent")}


def _faq_lookup(args: dict[str, Any]) -> dict[str, Any]:
    return {"answer": "Bilgi icin otel profilindeki FAQ verilerine bakiniz.", "source": "faq"}


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_HANDLERS: dict[str, Any] = {
    "booking_availability": _booking_availability,
    "booking_quote": _booking_quote,
    "stay_create_hold": _stay_create_hold,
    "booking_create_reservation": _booking_create_reservation,
    "booking_get_reservation": _booking_get_reservation,
    "booking_modify": _booking_modify,
    "booking_cancel": _booking_cancel,
    "restaurant_availability": _restaurant_availability,
    "restaurant_create_hold": _restaurant_create_hold,
    "restaurant_confirm": _restaurant_confirm,
    "restaurant_modify": _restaurant_modify,
    "restaurant_cancel": _restaurant_cancel,
    "transfer_get_info": _transfer_get_info,
    "transfer_create_hold": _transfer_create_hold,
    "transfer_confirm": _transfer_confirm,
    "transfer_modify": _transfer_modify,
    "transfer_cancel": _transfer_cancel,
    "approval_request": _approval_request,
    "payment_request_prepayment": _payment_request_prepayment,
    "notify_send": _notify_send,
    "handoff_create_ticket": _handoff_create_ticket,
    "crm_log": _crm_log,
    "faq_lookup": _faq_lookup,
}


async def mock_tool_executor(tool_name: str, tool_args: str | dict[str, Any]) -> str:
    """Execute a tool call with mock data.

    This function matches the signature expected by
    ``LLMClient.run_tool_call_loop`` (tool_name, tool_args) -> str.
    """
    # Parse arguments if given as JSON string
    if isinstance(tool_args, str):
        try:
            parsed_args: dict[str, Any] = json.loads(tool_args)
        except (json.JSONDecodeError, TypeError):
            parsed_args = {}
    else:
        parsed_args = tool_args or {}

    handler = _HANDLERS.get(tool_name)
    if handler is None:
        logger.warning("mock_tool_unknown", tool=tool_name)
        return json.dumps({"error": f"unknown_tool: {tool_name}"})

    try:
        result = handler(parsed_args)
        logger.info("mock_tool_executed", tool=tool_name, status="ok")
        return json.dumps(result, ensure_ascii=False)
    except Exception:
        logger.exception("mock_tool_execution_error", tool=tool_name)
        return json.dumps({"error": "tool_execution_failed"})
