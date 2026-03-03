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
    board_type_id: int
    rate_type_id: int
    rate_code_id: int
    price_agency_id: int | None = None
    currency_code: str = "EUR"
    price: Decimal
    discounted_price: Decimal
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


def parse_availability(raw: dict) -> AvailabilityResponse:
    """Parse raw availability response."""
    normalized = normalize_keys(raw)
    return AvailabilityResponse(**normalized)


def parse_quote(raw: dict) -> QuoteResponse:
    """Parse raw quote response."""
    normalized = normalize_keys(raw)
    return QuoteResponse(**normalized)


def parse_reservation_create(raw: dict) -> ReservationResponse:
    """Parse raw reservation creation response."""
    normalized = normalize_keys(raw)
    return ReservationResponse(**normalized)


def parse_reservation_detail(raw: dict) -> ReservationDetailResponse:
    """Parse raw reservation detail response."""
    normalized = normalize_keys(raw)
    return ReservationDetailResponse(**normalized, raw_data=raw)
