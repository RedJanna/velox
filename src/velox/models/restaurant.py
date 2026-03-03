"""Restaurant booking data models."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, Field

from velox.config.constants import HoldStatus


class RestaurantAvailabilityRequest(BaseModel):
    hotel_id: int
    date: date
    time: time
    party_size: int
    area: str | None = None  # indoor/outdoor
    notes: str | None = None


class RestaurantSlot(BaseModel):
    slot_id: str
    time: time
    capacity_left: int


class RestaurantSlotCreate(BaseModel):
    date_from: date
    date_to: date
    time: time
    total_capacity: int = Field(ge=1)
    area: str = "outdoor"
    is_active: bool = True


class RestaurantSlotUpdate(BaseModel):
    total_capacity: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class RestaurantSlotView(BaseModel):
    slot_id: int
    hotel_id: int
    date: date
    time: time
    area: str
    total_capacity: int
    booked_count: int
    capacity_left: int
    is_active: bool


class RestaurantHold(BaseModel):
    id: UUID | None = None
    hold_id: str
    hotel_id: int
    conversation_id: UUID | None = None
    slot_id: str | None = None
    date: date
    time: time
    party_size: int
    guest_name: str | None = None
    phone: str | None = None
    area: str | None = None
    notes: str | None = None
    status: HoldStatus = HoldStatus.PENDING_APPROVAL
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
