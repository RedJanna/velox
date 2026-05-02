"""Admin Voice Lab routes for pre-live AI telesekreter checks."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import (
    TokenData,
    check_permission,
    get_current_user,
    resolve_hotel_scope,
)
from velox.core.hotel_profile_loader import get_profile
from velox.voice_lab import (
    VoiceLabRunner,
    VoiceLabRunRequest,
    VoiceLabRunResult,
    VoiceLabScenario,
)
from velox.voice_lab.models import VoiceLabResult
from velox.voice_lab.scenarios import get_voice_lab_scenarios

router = APIRouter(prefix="/admin/voice-lab", tags=["admin-voice-lab"])

VOICE_LAB_PERMISSION = "conversations:read"
MAX_VOICE_LAB_TRANSCRIPT_CHARS = 4000


class VoiceLabScenarioListResponse(BaseModel):
    """Available Voice Lab scenario catalog."""

    items: list[VoiceLabScenario]


class VoiceLabRunAdminRequest(BaseModel):
    """Admin request for one Voice Lab transcript run."""

    hotel_id: int | None = Field(default=None, ge=1)
    transcript: str = Field(min_length=1, max_length=MAX_VOICE_LAB_TRANSCRIPT_CHARS)
    language: str = Field(default="tr", max_length=8)
    scenario_id: str | None = Field(default=None, max_length=16)

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, value: str) -> str:
        """Reject whitespace-only transcripts before running the lab."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Transcript is required")
        return cleaned

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        """Normalize the first Voice Lab language set."""
        normalized = str(value or "tr").strip().lower()
        if normalized in {"tr", "en", "ru"}:
            return normalized
        return "tr"

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, value: str | None) -> str | None:
        """Normalize empty scenario IDs to automatic matching."""
        cleaned = str(value or "").strip()
        return cleaned or None


class VoiceLabMatrixRunRequest(BaseModel):
    """Admin request for running the baseline scenario matrix."""

    hotel_id: int | None = Field(default=None, ge=1)
    language: str = Field(default="tr", max_length=8)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        """Normalize the first Voice Lab language set."""
        normalized = str(value or "tr").strip().lower()
        if normalized in {"tr", "en", "ru"}:
            return normalized
        return "tr"


class VoiceLabMatrixSummary(BaseModel):
    """Aggregate status for a Voice Lab matrix run."""

    total: int
    passed: int
    failed: int
    blocked: int


class VoiceLabMatrixRunResponse(BaseModel):
    """Result set for the baseline Voice Lab matrix."""

    summary: VoiceLabMatrixSummary
    items: list[VoiceLabRunResult]


@router.get("/scenarios", response_model=VoiceLabScenarioListResponse)
async def list_voice_lab_scenarios(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> VoiceLabScenarioListResponse:
    """Return the current read-only Voice Lab scenario matrix."""
    check_permission(current_user, VOICE_LAB_PERMISSION)
    return VoiceLabScenarioListResponse(items=list(get_voice_lab_scenarios()))


@router.post("/run", response_model=VoiceLabRunResult)
async def run_voice_lab_transcript(
    payload: VoiceLabRunAdminRequest,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> VoiceLabRunResult:
    """Run one transcript through the deterministic Voice Lab pipeline."""
    check_permission(current_user, VOICE_LAB_PERMISSION)
    hotel_id = resolve_hotel_scope(current_user, payload.hotel_id)
    runner = _runner_for_hotel(hotel_id)
    return runner.run(
        VoiceLabRunRequest(
            hotel_id=hotel_id,
            transcript=payload.transcript,
            language=payload.language,
            scenario_id=payload.scenario_id,
        )
    )


@router.post("/run-matrix", response_model=VoiceLabMatrixRunResponse)
async def run_voice_lab_matrix(
    payload: VoiceLabMatrixRunRequest,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> VoiceLabMatrixRunResponse:
    """Run the full V001-V018 scenario matrix for the selected hotel."""
    check_permission(current_user, VOICE_LAB_PERMISSION)
    hotel_id = resolve_hotel_scope(current_user, payload.hotel_id)
    runner = _runner_for_hotel(hotel_id)
    items = runner.run_matrix(language=payload.language)
    summary = VoiceLabMatrixSummary(
        total=len(items),
        passed=sum(1 for item in items if item.result == VoiceLabResult.PASS),
        failed=sum(1 for item in items if item.result == VoiceLabResult.FAIL),
        blocked=sum(1 for item in items if item.result == VoiceLabResult.BLOCKED),
    )
    return VoiceLabMatrixRunResponse(summary=summary, items=items)


def _runner_for_hotel(hotel_id: int) -> VoiceLabRunner:
    """Build a Voice Lab runner for one loaded HOTEL_PROFILE."""
    profile = get_profile(hotel_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seçili otel profili bulunamadı.",
        )
    return VoiceLabRunner(profile)
