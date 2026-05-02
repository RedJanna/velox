"""Unit tests for admin Voice Lab API helpers."""

import pytest
from fastapi import HTTPException

from velox.api.middleware.auth import TokenData
from velox.api.routes.admin_voice_lab import (
    VoiceLabMatrixRunRequest,
    VoiceLabRunAdminRequest,
    run_voice_lab_matrix,
    run_voice_lab_transcript,
)
from velox.config.constants import Role
from velox.models.hotel_profile import HotelProfile


def _admin_user(hotel_id: int) -> TokenData:
    """Build a minimal admin token for direct route tests."""
    return TokenData(
        user_id=1,
        hotel_id=hotel_id,
        username="admin",
        role=Role.ADMIN,
        permissions={"conversations:read"},
    )


@pytest.mark.asyncio
async def test_admin_voice_lab_runs_full_matrix(
    hotel_profile: HotelProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admin Voice Lab API should expose the full deterministic matrix."""
    monkeypatch.setattr("velox.api.routes.admin_voice_lab.get_profile", lambda _hotel_id: hotel_profile)

    response = await run_voice_lab_matrix(
        VoiceLabMatrixRunRequest(hotel_id=hotel_profile.hotel_id, language="tr"),
        _admin_user(hotel_profile.hotel_id),
    )

    assert response.summary.total == 18
    assert response.summary.passed == 18
    assert response.summary.failed == 0
    assert response.summary.blocked == 0
    assert response.items[0].scenario_id == "V001"


@pytest.mark.asyncio
async def test_admin_voice_lab_transcript_redacts_card_like_input(
    hotel_profile: HotelProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Payment-card-like values must not be returned raw from the API result."""
    monkeypatch.setattr("velox.api.routes.admin_voice_lab.get_profile", lambda _hotel_id: hotel_profile)

    response = await run_voice_lab_transcript(
        VoiceLabRunAdminRequest(
            hotel_id=hotel_profile.hotel_id,
            transcript="Kart numaram 4111 1111 1111 1111, odeme alir misiniz?",
        ),
        _admin_user(hotel_profile.hotel_id),
    )

    assert response.result == "BLOCKED"
    assert "[REDACTED_CARD]" in response.input_transcript
    assert "4111 1111 1111 1111" not in response.input_transcript


@pytest.mark.asyncio
async def test_admin_voice_lab_enforces_hotel_scope(hotel_profile: HotelProfile) -> None:
    """Admins cannot run another hotel's Voice Lab scope."""
    with pytest.raises(HTTPException) as exc_info:
        await run_voice_lab_matrix(
            VoiceLabMatrixRunRequest(hotel_id=hotel_profile.hotel_id + 1, language="tr"),
            _admin_user(hotel_profile.hotel_id),
        )

    assert exc_info.value.status_code == 403
