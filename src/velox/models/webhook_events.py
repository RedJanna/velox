"""Webhook event data models."""

from datetime import datetime

from pydantic import BaseModel


class ApprovalEvent(BaseModel):
    hotel_id: int
    approval_request_id: str
    approved: bool
    approved_by_role: str
    timestamp: datetime


class PaymentEvent(BaseModel):
    hotel_id: int
    payment_request_id: str
    status: str  # PAID, FAILED, EXPIRED
    timestamp: datetime


class TransferEvent(BaseModel):
    hotel_id: int
    transfer_hold_id: str
    status: str  # CONFIRMED, CANCELLED
    timestamp: datetime
