"""Pydantic models for Chat Lab feedback, imports, and reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

ChatLabSourceType = Literal["live_test_chat", "imported_real", "imported_test"]
ChatLabImportRole = Literal["user", "assistant", "system", "other"]


class FeedbackScaleItem(BaseModel):
    """Admin-facing metadata for one feedback score."""

    rating: int = Field(ge=1, le=5)
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    tooltip: str = Field(min_length=1)
    correction_required: bool = False


class FeedbackOptionItem(BaseModel):
    """Definition item for categories or tags shown in Chat Lab."""

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tooltip: str = Field(min_length=1)


class ChatLabCatalogResponse(BaseModel):
    """Chat Lab catalog payload for feedback forms and report defaults."""

    scales: list[FeedbackScaleItem]
    categories: list[FeedbackOptionItem]
    tags: list[FeedbackOptionItem]
    default_report_start: str | None = None
    default_report_end: str


class ChatLabMessageView(BaseModel):
    """Normalized chat message shown in the Chat Lab UI."""

    id: str
    role: str
    content: str
    created_at: str
    phone: str | None = None
    internal_json: dict[str, Any] | None = None
    model: str | None = None


class ChatLabParticipantOption(BaseModel):
    """Participant candidate for role mapping during transcript import."""

    phone: str
    label: str
    suggested_role: ChatLabImportRole = "other"


class ChatLabImportFileItem(BaseModel):
    """One available transcript import file."""

    filename: str
    label: str | None = None
    modified_at: str
    size_bytes: int = Field(ge=0)


class ChatLabImportListResponse(BaseModel):
    """List of transcript import files in the admin-only folder."""

    items: list[ChatLabImportFileItem]


class ChatLabImportRequest(BaseModel):
    """Load one transcript import file, with optional role mapping."""

    filename: str = Field(min_length=1, max_length=255)
    role_mapping: dict[str, ChatLabImportRole] = Field(default_factory=dict)


class ChatLabImportResponse(BaseModel):
    """Transcript import result or role-mapping requirement."""

    status: Literal["ready", "role_mapping_required"]
    source_type: ChatLabSourceType = "imported_real"
    file_name: str
    conversation_id: str | None = None
    source_label: str | None = None
    messages: list[ChatLabMessageView] = Field(default_factory=list)
    participants: list[ChatLabParticipantOption] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatLabFeedbackRequest(BaseModel):
    """Payload for rating one assistant reply in Chat Lab."""

    source_type: ChatLabSourceType = "live_test_chat"
    phone: str = Field(default="test_user_123", min_length=1, max_length=128)
    assistant_message_id: str = Field(min_length=1, max_length=128)
    rating: int = Field(ge=1, le=5)
    category: str | None = Field(default=None, max_length=100)
    custom_category: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    custom_tags: list[str] = Field(default_factory=list)
    gold_standard: str | None = Field(default=None, max_length=4096)
    notes: str | None = Field(default=None, max_length=2048)
    approved_example: bool | None = None
    import_file: str | None = Field(default=None, max_length=255)
    role_mapping: dict[str, ChatLabImportRole] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_feedback_request(self) -> ChatLabFeedbackRequest:
        """Enforce required fields based on the selected rating and source."""
        needs_gold_standard = self.rating in {1, 2, 3, 4}
        has_gold_standard = bool(self.gold_standard and self.gold_standard.strip())
        if needs_gold_standard and not has_gold_standard:
            raise ValueError("Gold standard text is required for ratings 1-4.")

        has_category = bool(self.category and self.category.strip())
        has_custom_category = bool(self.custom_category and self.custom_category.strip())
        if needs_gold_standard and not (has_category or has_custom_category):
            raise ValueError("A category or custom category is required for ratings 1-4.")

        if self.source_type in {"imported_real", "imported_test"} and not self.import_file:
            raise ValueError("Import file is required for imported transcripts.")

        if has_gold_standard:
            self.gold_standard = self.gold_standard.strip()
        else:
            self.gold_standard = None

        if self.notes and not self.notes.strip():
            self.notes = None

        return self


class ChatLabFeedbackResponse(BaseModel):
    """API response after feedback submission."""

    status: Literal["saved"]
    feedback_id: str
    rating: int = Field(ge=1, le=5)
    rating_label: str
    storage_group: Literal["bad_feedback", "good_feedback"]
    category: str
    tags: list[str] = Field(default_factory=list)
    storage_path: str
    source_type: ChatLabSourceType
    approved_example: bool = False


class ChatLabReportRequest(BaseModel):
    """Payload for generating one aggregate bad-feedback report."""

    date_from: datetime
    date_to: datetime

    @model_validator(mode="after")
    def validate_period(self) -> ChatLabReportRequest:
        """Ensure the report period is chronologically valid."""
        if self.date_to < self.date_from:
            raise ValueError("date_to must be greater than or equal to date_from.")
        return self


class ChatLabRecommendation(BaseModel):
    """Recommendation entry stored inside aggregate reports."""

    target_file: str
    reason: str
    risk: str
    conflict_check: str
    test_suggestion: str
    root_cause_type: str
    confidence: Literal["high", "medium", "low"]
    kassandra_profile_change_required: bool = False
    scenario_creation_recommended: bool = False
    duplicate_count: int = Field(default=1, ge=1)


class ChatLabReportResponse(BaseModel):
    """Aggregate report response for the UI."""

    status: Literal["generated", "no_feedback"]
    report_id: str | None = None
    report_path: str | None = None
    selected_model: str | None = None
    summary: str
    recommendation_count: int = 0
    date_from: str
    date_to: str
    recommendations: list[ChatLabRecommendation] = Field(default_factory=list)
