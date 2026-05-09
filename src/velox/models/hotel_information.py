"""Structured hotel information dataset models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HotelInformationModel(BaseModel):
    """Base model that preserves future hotel-information fields."""

    model_config = ConfigDict(extra="allow")


class HotelInformationEntry(HotelInformationModel):
    """One source-backed hotel information entry."""

    id: str
    category: str
    title_tr: str
    answer_tr: str
    data_type: str
    value: Any = None
    unit: Any = None
    confidence: str
    human_handoff_required: bool
    missing_information: bool = False
    notes: str = ""
    trigger_examples: list[str] = Field(default_factory=list)


class GlobalResponseRule(HotelInformationModel):
    """Global response rule attached to the hotel information dataset."""

    id: str
    rule_tr: str
    human_handoff_required: bool


class HotelInformationDataset(HotelInformationModel):
    """Versioned hotel information dataset loaded from JSON."""

    hotel_data_version: str
    language: str
    status: str
    hotel_information: list[HotelInformationEntry] = Field(default_factory=list)
    global_response_rules: list[GlobalResponseRule] = Field(default_factory=list)

    def entry_by_id(self, entry_id: str) -> HotelInformationEntry | None:
        """Return a dataset entry by stable id."""
        for entry in self.hotel_information:
            if entry.id == entry_id:
                return entry
        return None
