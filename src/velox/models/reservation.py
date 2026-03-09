"""Stay reservation data models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from velox.config.constants import CancelPolicyType, HoldStatus


class StayDraft(BaseModel):
    """Draft data for creating a stay hold."""
    checkin_date: date
    checkout_date: date
    room_type_id: int
    board_type_id: int
    rate_type_id: int
    rate_code_id: int
    price_agency_id: int | None = None
    currency_display: str = "EUR"
    total_price_eur: Decimal
    adults: int
    chd_ages: list[int] = Field(default_factory=list)
    guest_name: str
    phone: str
    email: str | None = None
    nationality: str = "TR"
    cancel_policy_type: CancelPolicyType = CancelPolicyType.FREE_CANCEL
    notes: str | None = None


class StayHold(BaseModel):
    """Stay hold record."""
    id: UUID | None = None
    hold_id: str
    hotel_id: int
    conversation_id: UUID | None = None
    draft_json: dict
    status: HoldStatus = HoldStatus.PENDING_APPROVAL
    pms_reservation_id: str | None = None
    voucher_no: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class BookingAvailabilityRequest(BaseModel):
    hotel_id: int
    checkin_date: date
    checkout_date: date
    adults: int
    chd_count: int = 0
    chd_ages: list[int] = Field(default_factory=list)
    currency: str = "EUR"

    @model_validator(mode="after")
    def sync_child_fields(self) -> "BookingAvailabilityRequest":
        """Keep child count aligned with provided ages."""
        if self.chd_ages:
            age_count = len(self.chd_ages)
            if self.chd_count not in (0, age_count):
                raise ValueError("chd_count must match number of chd_ages")
            self.chd_count = age_count
        return self


class BookingQuoteRequest(BaseModel):
    hotel_id: int
    checkin_date: date
    checkout_date: date
    adults: int
    chd_count: int = 0
    chd_ages: list[int] = Field(default_factory=list)
    currency: str = "EUR"
    language: str = "TR"
    nationality: str = "TR"
    only_best_offer: bool = False
    cancel_policy_type: CancelPolicyType | None = None

    @model_validator(mode="after")
    def sync_child_fields(self) -> "BookingQuoteRequest":
        """Keep child count aligned with provided ages."""
        if self.chd_ages:
            age_count = len(self.chd_ages)
            if self.chd_count not in (0, age_count):
                raise ValueError("chd_count must match number of chd_ages")
            self.chd_count = age_count
        return self


class BookingOffer(BaseModel):
    id: str
    room_type_id: int
    board_type_id: int
    rate_type_id: int
    rate_code_id: int
    price_agency_id: int | None = None
    currency_code: str
    price: Decimal
    discounted_price: Decimal
    cancellation_penalty: dict = Field(default_factory=dict)
