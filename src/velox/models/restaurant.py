"""Restaurant booking data models."""

from __future__ import annotations

import datetime as _dt
from datetime import date, datetime, time
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from velox.config.constants import HoldStatus, RestaurantReservationStatus


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
    status: str = RestaurantReservationStatus.BEKLEMEDE
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    table_id: str | None = None
    table_type: str | None = None
    arrived_at: datetime | None = None
    no_show_at: datetime | None = None
    extended_minutes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Floor plan models
# ---------------------------------------------------------------------------


class FloorPlanTableItem(BaseModel):
    """Single table element within a floor plan layout."""
    table_id: str
    type: str  # TABLE_2, TABLE_4, etc.
    capacity: int
    x: float
    y: float
    rotation: float = 0
    label: str = ""


class FloorPlanShapeItem(BaseModel):
    """Decorative shape (divider / wall / decor) within a floor plan layout."""
    shape_id: str
    type: str  # HORIZONTAL_DIVIDER, VERTICAL_DIVIDER, WALL, CURVED_WALL, TREE, BUSH
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0


class FloorPlanLayout(BaseModel):
    """Full layout stored in restaurant_floor_plans.layout_data."""
    canvas_width: int = 1200
    canvas_height: int = 800
    floor_theme: str = "CREAM_MARBLE_CLASSIC"
    tables: list[FloorPlanTableItem] = Field(default_factory=list)
    shapes: list[FloorPlanShapeItem] = Field(default_factory=list)


class FloorPlan(BaseModel):
    id: UUID | None = None
    hotel_id: int
    name: str = "Ana Plan"
    layout_data: FloorPlanLayout = Field(default_factory=FloorPlanLayout)
    is_active: bool = True
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FloorPlanCreate(BaseModel):
    name: str = "Ana Plan"
    layout_data: FloorPlanLayout


class FloorPlanUpdate(BaseModel):
    name: str | None = None
    layout_data: FloorPlanLayout | None = None


# ---------------------------------------------------------------------------
# Restaurant table model
# ---------------------------------------------------------------------------


class RestaurantTable(BaseModel):
    id: int | None = None
    hotel_id: int
    floor_plan_id: UUID
    table_id: str
    table_type: str
    capacity: int
    is_active: bool = True
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Restaurant settings model
# ---------------------------------------------------------------------------


class RestaurantSettings(BaseModel):
    hotel_id: int
    daily_max_reservations_enabled: bool = False
    daily_max_reservations_count: int = Field(default=50, ge=1)
    updated_at: datetime | None = None


class RestaurantSettingsUpdate(BaseModel):
    daily_max_reservations_enabled: bool | None = None
    daily_max_reservations_count: int | None = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Daily view response models
# ---------------------------------------------------------------------------


class DailyTableView(BaseModel):
    """Table with its assigned reservation (if any) for a specific day."""
    table_id: str
    table_type: str
    capacity: int
    x: float
    y: float
    rotation: float = 0
    hold_id: str | None = None
    guest_name: str | None = None
    party_size: int | None = None
    reservation_time: time | None = None
    status: str | None = None


# ---------------------------------------------------------------------------
# Hold update / status change request models
# ---------------------------------------------------------------------------


class RestaurantHoldUpdateRequest(BaseModel):
    """Fields editable from the table detail modal."""
    guest_name: str | None = None
    party_size: int | None = Field(default=None, ge=1)
    time: Optional[_dt.time] = None
    area: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class RestaurantHoldStatusChange(BaseModel):
    """Status transition request."""
    status: str
    reason: str | None = None
