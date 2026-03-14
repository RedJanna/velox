"""Elektraweb response field mapper — normalizes kebab-case to snake_case."""

import re
from decimal import Decimal

from pydantic import BaseModel, Field


def kebab_to_snake(name: str) -> str:
    """Convert kebab-case or camelCase into snake_case."""
    normalized = name.replace("-", "_")
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    return normalized.lower()


def normalize_keys(data: dict | list) -> dict | list:
    """Recursively normalize dict/list keys to snake_case."""
    if isinstance(data, dict):
        return {kebab_to_snake(key): normalize_keys(value) for key, value in data.items()}
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    return data


class AvailabilityRow(BaseModel):
    """A single row in the availability response."""

    date: str
    room_type_id: int
    room_type: str = ""
    room_to_sell: int = 0
    stop_sell: bool = False


class AvailabilityResponse(BaseModel):
    """Parsed availability response from Elektraweb."""

    available: bool = False
    rows: list[AvailabilityRow] = Field(default_factory=list)
    derived: dict = Field(default_factory=dict)
    notes: str = ""


class BookingOffer(BaseModel):
    """A single offer from quote endpoint."""

    id: str = ""
    room_type_id: int
    room_type: str = ""
    board_type_id: int
    board_type: str = ""
    rate_type_id: int
    rate_type: str = ""
    rate_code_id: int
    price_agency_id: int | None = None
    currency_code: str = "EUR"
    price: Decimal
    discounted_price: Decimal
    room_area: int | None = None
    cancel_possible: bool = False
    cancellation_penalty: dict = Field(default_factory=dict)


class QuoteResponse(BaseModel):
    """Parsed quote response from Elektraweb."""

    offers: list[BookingOffer] = Field(default_factory=list)


class ReservationResponse(BaseModel):
    """Parsed reservation creation response."""

    reservation_id: str = ""
    voucher_no: str = ""
    confirmation_url: str | None = None
    state: str = ""


class ReservationDetailResponse(BaseModel):
    """Parsed reservation detail response."""

    success: bool = False
    reservation_id: str = ""
    voucher_no: str = ""
    total_price: Decimal | None = None
    state: str = ""
    raw_data: dict = Field(default_factory=dict)


def parse_availability(raw: dict | list) -> AvailabilityResponse:
    """Parse raw availability response."""
    normalized = normalize_keys(raw)
    if isinstance(normalized, list):
        rows = [
            AvailabilityRow(
                date=str(item.get("date", "")),
                room_type_id=int(item.get("room_type_id", 0) or 0),
                room_type=str(item.get("room_type", "")),
                room_to_sell=int(item.get("available_room_count", item.get("room_to_sell", 0)) or 0),
                stop_sell=bool(item.get("stopsell", item.get("stop_sell", False))),
            )
            for item in normalized
        ]
        return AvailabilityResponse(
            available=any((row.room_to_sell > 0) and (not row.stop_sell) for row in rows),
            rows=rows,
            derived={"source": "live_list_response", "row_count": len(rows)},
            notes="",
        )
    return AvailabilityResponse(**normalized)


def parse_quote(raw: dict | list) -> QuoteResponse:
    """Parse raw quote response."""
    normalized = normalize_keys(raw)
    if isinstance(normalized, list):
        offers: list[BookingOffer] = []
        for item in normalized:
            offers.append(
                BookingOffer(
                    id=str(item.get("id", "")),
                    room_type_id=int(item.get("room_type_id", 0) or 0),
                    room_type=str(item.get("room_type", "")),
                    board_type_id=int(item.get("board_type_id", 0) or 0),
                    board_type=str(item.get("board_type", "")),
                    rate_type_id=int(item.get("rate_type_id", 0) or 0),
                    rate_type=str(item.get("rate_type", "")),
                    rate_code_id=int(item.get("rate_code_id", item.get("ratecodeid", 0)) or 0),
                    price_agency_id=item.get("price_agency_id"),
                    currency_code=str(item.get("currency_code", item.get("currency", "EUR"))),
                    price=item.get("price", 0),
                    discounted_price=item.get("discounted_price", item.get("price", 0)),
                    room_area=int(item.get("room_area", 0) or 0) or None,
                    cancel_possible=bool(item.get("cancel_possible", item.get("cancelpossible", False))),
                    cancellation_penalty=item.get("cancellation_penalty") or {},
                )
            )
        return QuoteResponse(offers=offers)
    return QuoteResponse(**normalized)


def parse_reservation_create(raw: dict) -> ReservationResponse:
    """Parse raw reservation creation response."""
    normalized = normalize_keys(raw)
    if isinstance(normalized, dict):
        row_data = normalized.get("row")
        row_id = row_data.get("id") if isinstance(row_data, dict) else None
        reservation_id = str(
            normalized.get("reservation_id")
            or normalized.get("resid")
            or normalized.get("primary_key")
            or row_id
            or ""
        )
        voucher_no = str(
            normalized.get("voucher_no")
            or normalized.get("voucher")
            or normalized.get("voucherno")
            or ""
        )
        state = str(normalized.get("state") or normalized.get("status") or normalized.get("message") or "")
        confirmation_url_raw = normalized.get("confirmation_url")
        confirmation_url = str(confirmation_url_raw) if isinstance(confirmation_url_raw, str) else None
        return ReservationResponse(
            reservation_id=reservation_id,
            voucher_no=voucher_no,
            confirmation_url=confirmation_url,
            state=state,
        )

    if isinstance(normalized, list) and normalized:
        first = normalized[0]
        if isinstance(first, dict):
            return parse_reservation_create(first)
    return ReservationResponse()


def parse_reservation_detail(raw: dict) -> ReservationDetailResponse:
    """Parse raw reservation detail response."""
    normalized = normalize_keys(raw)
    return ReservationDetailResponse(**normalized, raw_data=raw)
