"""Stay reservation data models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

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
