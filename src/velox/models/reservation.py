"""Stay reservation data models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

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
    notes: str = ""

    @field_validator("guest_name")
    @classmethod
    def normalize_guest_name(cls, value: str) -> str:
        """Normalize guest name spacing and enforce minimum length."""
        normalized = " ".join(value.strip().split())
        if len(normalized) < 2:
            raise ValueError("guest_name must contain at least 2 characters")
        return normalized

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        """Normalize phone to a safe E.164-like shape without spaces."""
        cleaned = "".join(char for char in value.strip() if char.isdigit() or char == "+")
        if cleaned.startswith("00"):
            cleaned = f"+{cleaned[2:]}"
        if cleaned and not cleaned.startswith("+"):
            cleaned = f"+{cleaned}"
        digit_count = len(cleaned.replace("+", ""))
        if digit_count < 10 or digit_count > 15:
            raise ValueError("phone must contain 10-15 digits")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalize optional email casing/spacing."""
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized

    @field_validator("chd_ages")
    @classmethod
    def validate_child_ages(cls, value: list[int]) -> list[int]:
        """Validate child ages with strict bounds."""
        for age in value:
            if age < 0 or age > 17:
                raise ValueError("child ages must be between 0 and 17")
        return value

    @model_validator(mode="after")
    def validate_stay_dates_and_amount(self) -> StayDraft:
        """Validate date ordering and minimum totals."""
        if self.checkout_date <= self.checkin_date:
            raise ValueError("checkout_date must be later than checkin_date")
        if self.adults < 1:
            raise ValueError("adults must be at least 1")
        if self.total_price_eur <= 0:
            raise ValueError("total_price_eur must be greater than 0")
        return self


class StayHold(BaseModel):
    """Stay hold record."""
    id: UUID | None = None
    hold_id: str
    hotel_id: int
    conversation_id: UUID | None = None
    draft_json: dict[str, Any]
    status: HoldStatus = HoldStatus.PENDING_APPROVAL
    pms_reservation_id: str | None = None
    voucher_no: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    workflow_state: str | None = None
    expires_at: datetime | None = None
    pms_create_started_at: datetime | None = None
    pms_create_completed_at: datetime | None = None
    manual_review_reason: str | None = None
    approval_idempotency_key: str | None = None
    create_idempotency_key: str | None = None
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
    def sync_child_fields(self) -> BookingAvailabilityRequest:
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
    def sync_child_fields(self) -> BookingQuoteRequest:
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
    cancellation_penalty: dict[str, Any] = Field(default_factory=dict)
