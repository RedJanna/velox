"""Transfer booking data models."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from velox.config.constants import HoldStatus


class TransferRoute(BaseModel):
    route_code: str
    from_location: str
    to_location: str
    price_eur: Decimal
    vehicle_type: str
    max_pax: int
    duration_min: int
    baby_seat: bool = False
    oversize_vehicle: dict | None = None  # {type, price_eur, min_pax}


class TransferInfoRequest(BaseModel):
    hotel_id: int
    route: str
    pax_count: int


class TransferHold(BaseModel):
    id: UUID | None = None
    hold_id: str
    hotel_id: int
    conversation_id: UUID | None = None
    route: str
    date: date
    time: time
    pax_count: int
    guest_name: str | None = None
    phone: str | None = None
    flight_no: str | None = None
    vehicle_type: str | None = None
    baby_seat: bool = False
    price_eur: Decimal | None = None
    notes: str | None = None
    status: HoldStatus = HoldStatus.PENDING_APPROVAL
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
