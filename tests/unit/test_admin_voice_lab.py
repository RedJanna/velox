"""Unit tests for admin Voice Lab API helpers."""

from datetime import UTC, datetime

import httpx
import pytest
from fastapi import HTTPException

from velox.api.middleware.auth import TokenData
from velox.api.routes.admin_voice_lab import (
    OPENAI_REALTIME_CLIENT_SECRETS_URL,
    VoiceLabMatrixRunRequest,
    VoiceLabRunAdminRequest,
    build_voice_lab_realtime_session_config,
    build_voice_lab_run_id,
    evaluate_voice_lab_release_gate,
    extract_openai_error_summary,
    normalize_voice_lab_realtime_voice,
    request_openai_realtime_client_secret,
    request_openai_realtime_sdp_answer,
    run_voice_lab_matrix,
    run_voice_lab_transcript,
    summarize_voice_lab_matrix,
)
from velox.config.constants import Role
from velox.models.hotel_profile import HotelProfile
from velox.voice_lab import (
    VoiceLabAction,
    VoiceLabResult,
    VoiceLabRunResult,
    VoiceLabSource,
)


def _admin_user(hotel_id: int) -> TokenData:
    """Build a minimal admin token for direct route tests."""
    return TokenData(
        user_id=1,
        hotel_id=hotel_id,
        username="admin",
        role=Role.ADMIN,
        permissions={"conversations:read"},
    )


def test_admin_voice_lab_realtime_config_uses_openai_model_and_voice(
    hotel_profile: HotelProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Realtime Voice Lab sessions should be grounded and audio-only."""
    monkeypatch.setattr("velox.api.routes.admin_voice_lab.settings.openai_realtime_model", "gpt-realtime-1.5")

    config = build_voice_lab_realtime_session_config(
        profile=hotel_profile,
        language="tr",
        voice="marin",
    )

    assert config["type"] == "realtime"
    assert config["model"] == "gpt-realtime-1.5"
    assert config["output_modalities"] == ["audio"]
    assert config["audio"]["output"]["voice"] == "marin"
    assert "Do not ask for or process card numbers" in str(config["instructions"])
    assert "never invent" in str(config["instructions"])


def test_admin_voice_lab_realtime_voice_falls_back_to_marin() -> None:
    """Unsupported Realtime voices should never pass through to OpenAI."""
    assert normalize_voice_lab_realtime_voice("unknown_voice") == "marin"

    supported_voices = (
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "sage",
        "shimmer",
        "verse",
        "marin",
        "cedar",
    )
    for voice in supported_voices:
        assert normalize_voice_lab_realtime_voice(voice) == voice
        assert normalize_voice_lab_realtime_voice(voice.upper()) == voice


@pytest.mark.asyncio
async def test_admin_voice_lab_realtime_requires_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Realtime SDP proxy must fail closed when the server key is missing."""
    monkeypatch.setattr("velox.api.routes.admin_voice_lab.settings.openai_api_key", "")

    with pytest.raises(HTTPException) as exc_info:
        await request_openai_realtime_sdp_answer(
            offer_sdp="v=0\r\n",
            session_config={"type": "realtime"},
            hotel_id=1,
        )

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_admin_voice_lab_realtime_client_secret_requires_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Realtime client-secret minting must fail closed when the server key is missing."""
    monkeypatch.setattr("velox.api.routes.admin_voice_lab.settings.openai_api_key", "")

    with pytest.raises(HTTPException) as exc_info:
        await request_openai_realtime_client_secret(
            session_config={"type": "realtime"},
            hotel_id=1,
        )

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_admin_voice_lab_realtime_client_secret_uses_server_key_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The backend should mint only an ephemeral browser secret, never expose the server key."""
    captured: dict[str, object] = {}

    class _FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = (args, kwargs)

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            _ = (exc_type, exc, tb)

        async def post(self, url: str, **kwargs: object) -> httpx.Response:
            captured["url"] = url
            captured["headers"] = kwargs.get("headers")
            captured["json"] = kwargs.get("json")
            return httpx.Response(
                200,
                json={"value": "ek_test_ephemeral", "expires_at": 1777753268},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr("velox.api.routes.admin_voice_lab.settings.openai_api_key", "test-server-key")
    monkeypatch.setattr("velox.api.routes.admin_voice_lab.httpx.AsyncClient", _FakeAsyncClient)

    response = await request_openai_realtime_client_secret(
        session_config={"type": "realtime", "model": "gpt-realtime-1.5"},
        hotel_id=1,
    )

    assert captured["url"] == OPENAI_REALTIME_CLIENT_SECRETS_URL
    assert captured["headers"] == {
        "Authorization": "Bearer test-server-key",
        "Content-Type": "application/json",
    }
    assert captured["json"] == {"session": {"type": "realtime", "model": "gpt-realtime-1.5"}}
    assert response.value == "ek_test_ephemeral"
    assert response.expires_at == 1777753268
    assert "test-server-key" not in response.model_dump_json()


def test_extract_openai_error_summary_handles_json_error() -> None:
    """OpenAI error logging should keep only a short safe summary."""
    response = httpx.Response(
        400,
        json={"error": {"type": "invalid_request_error", "code": "bad_sdp", "message": "Invalid SDP"}},
    )

    assert extract_openai_error_summary(response) == {
        "type": "invalid_request_error",
        "code": "bad_sdp",
        "message": "Invalid SDP",
    }


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
    assert response.summary.critical_failed == 0
    assert response.run_id.startswith("voice-lab-")
    assert response.mode == "quick"
    assert response.languages == ["tr"]
    assert response.release_gate == "PASS"
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


def test_voice_lab_run_id_uses_compact_timestamp() -> None:
    """Voice Lab reports should have a predictable run ID shape."""
    run_id = build_voice_lab_run_id(datetime(2026, 5, 3, 12, 34, 56, tzinfo=UTC))

    assert run_id == "voice-lab-20260503-123456"


def test_voice_lab_release_gate_blocks_critical_failures(hotel_profile: HotelProfile) -> None:
    """Failed tool/handoff scenarios should block a live release decision."""
    failed_item = VoiceLabRunResult(
        hotel_id=hotel_profile.hotel_id,
        scenario_id="V001",
        input_transcript="fiyat",
        normalized_text="fiyat",
        language_detected="tr",
        intent="stay_quote_request",
        source_type=VoiceLabSource.TOOL,
        source_detail="booking.quote",
        action=VoiceLabAction.TOOL_REQUIRED,
        tool_required=True,
        tool_called=False,
        tool_name="booking.quote",
        handoff_required=False,
        risk_flags=[],
        response_text="",
        result=VoiceLabResult.FAIL,
    )

    summary = summarize_voice_lab_matrix([failed_item])
    release_gate, reason = evaluate_voice_lab_release_gate(summary)

    assert summary.critical_failed == 1
    assert release_gate == "BLOCKED"
    assert "Kritik" in reason
