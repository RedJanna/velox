"""Models for Operations Desk response review and reporting."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ResponseReviewStatus(StrEnum):
    """Lifecycle status for one reported response."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    FINALIZED = "finalized"
    CLOSED = "closed"


class ResponseReviewClassification(StrEnum):
    """Human review decision for the reported response."""

    NEEDS_REVIEW = "needs_review"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    NEEDS_REVISION = "needs_revision"


class ResponseReviewErrorType(StrEnum):
    """Structured error classes used for reporting and feedback routing."""

    NOT_CLASSIFIED = "not_classified"
    WRONG_INFO = "wrong_info"
    MISSING_INFO = "missing_info"
    WRONG_INTENT = "wrong_intent"
    SOURCE_MISMATCH = "source_mismatch"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    POLICY_RISK = "policy_risk"
    PII_RISK = "pii_risk"
    TONE_OR_LENGTH = "tone_or_length"
    LANGUAGE_ISSUE = "language_issue"
    TOOL_MISMATCH = "tool_mismatch"
    HANDOFF_REQUIRED = "handoff_required"
    DELIVERY_STATUS_ISSUE = "delivery_status_issue"
    OTHER = "other"


class ResponseReviewCreateRequest(BaseModel):
    """Request to report one Operations Desk message for review."""

    hotel_id: int | None = Field(default=None, ge=1)
    conversation_id: str = Field(min_length=1, max_length=128)
    message_id: str = Field(min_length=1, max_length=128)
    reason: str | None = Field(default=None, max_length=1000)
    error_type: ResponseReviewErrorType = ResponseReviewErrorType.NOT_CLASSIFIED


class ResponseReviewClassifyRequest(BaseModel):
    """Request to classify and optionally export one reported response."""

    classification: ResponseReviewClassification
    error_type: ResponseReviewErrorType = ResponseReviewErrorType.NOT_CLASSIFIED
    notes: str | None = Field(default=None, max_length=2048)
    gold_standard: str | None = Field(default=None, max_length=4096)
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=8)
    included_in_report: bool = False
    finalize: bool = True

    @model_validator(mode="after")
    def validate_classification_payload(self) -> ResponseReviewClassifyRequest:
        """Require correction context when the response is not accepted as correct."""
        if self.classification == ResponseReviewClassification.CORRECT:
            self.rating = 5
            self.gold_standard = None
            return self

        if not self.gold_standard or not self.gold_standard.strip():
            raise ValueError("Yanlış veya düzeltilmeli yanıtlarda referans yanıt zorunludur.")
        if self.error_type == ResponseReviewErrorType.NOT_CLASSIFIED:
            raise ValueError("Yanlış veya düzeltilmeli yanıtlarda hata tipi seçilmelidir.")
        if self.rating is None:
            self.rating = 2 if self.classification == ResponseReviewClassification.INCORRECT else 3
        self.gold_standard = self.gold_standard.strip()
        if self.notes and not self.notes.strip():
            self.notes = None
        return self


class ResponseReviewActionItem(BaseModel):
    """Audit action displayed in the review detail."""

    action_type: str
    actor_username: str
    from_status: str | None = None
    to_status: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ResponseReviewListItem(BaseModel):
    """Compact response review item for the vertical queue."""

    id: str
    hotel_id: int
    conversation_id: str
    message_id: str
    message_role: str
    message_content: str
    report_reason: str
    error_type: ResponseReviewErrorType
    status: ResponseReviewStatus
    classification: ResponseReviewClassification
    reported_by_username: str
    reported_by_display_name: str | None = None
    reported_at: str
    reviewed_at: str | None = None
    rating: int | None = None
    included_in_report: bool = False
    feedback_id: str | None = None


class ResponseReviewDetail(ResponseReviewListItem):
    """Full response review detail including snapshot and action trail."""

    message_created_at: str
    conversation_snapshot: dict[str, Any] = Field(default_factory=dict)
    context_messages: list[dict[str, Any]] = Field(default_factory=list)
    reviewed_by_username: str | None = None
    notes: str | None = None
    gold_standard: str | None = None
    feedback_storage_group: str | None = None
    feedback_storage_path: str | None = None
    actions: list[ResponseReviewActionItem] = Field(default_factory=list)


class ResponseReviewListResponse(BaseModel):
    """Paginated response review list."""

    items: list[ResponseReviewListItem] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
