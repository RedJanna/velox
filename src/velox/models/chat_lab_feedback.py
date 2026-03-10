"""Pydantic models for Chat Lab feedback workflows."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class FeedbackScaleItem(BaseModel):
    """Admin-facing metadata for one feedback score."""

    rating: int = Field(ge=1, le=5)
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    tooltip: str = Field(min_length=1)
    correction_required: bool = False


class ChatLabFeedbackRequest(BaseModel):
    """Payload for rating one assistant reply in Chat Lab."""

    phone: str = Field(default="test_user_123", min_length=1, max_length=128)
    assistant_message_id: UUID
    rating: int = Field(ge=1, le=5)
    correction: str | None = Field(default=None, max_length=4096)

    @model_validator(mode="after")
    def validate_correction_requirement(self) -> "ChatLabFeedbackRequest":
        """Require correction text for ratings that imply a fix."""
        needs_correction = self.rating in {1, 2, 3, 4}
        has_correction = bool(self.correction and self.correction.strip())
        if needs_correction and not has_correction:
            raise ValueError("Correction text is required for ratings 1-4.")
        if not has_correction:
            self.correction = None
        return self


class ChatLabFeedbackResponse(BaseModel):
    """API response after feedback submission."""

    status: Literal["acknowledged", "scenario_created"]
    rating: int = Field(ge=1, le=5)
    rating_label: str
    corrected_reply: str | None = None
    selected_model: str | None = None
    scenario_code: str | None = None
    scenario_path: str | None = None
