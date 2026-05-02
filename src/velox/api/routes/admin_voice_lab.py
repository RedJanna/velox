"""Admin Voice Lab routes for pre-live AI telesekreter checks."""

from __future__ import annotations

import json
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import (
    TokenData,
    check_permission,
    get_current_user,
    resolve_hotel_scope,
)
from velox.config.settings import settings
from velox.core.hotel_profile_loader import get_profile
from velox.models.hotel_profile import HotelProfile
from velox.voice_lab import (
    VoiceLabRunner,
    VoiceLabRunRequest,
    VoiceLabRunResult,
    VoiceLabScenario,
)
from velox.voice_lab.models import VoiceLabResult
from velox.voice_lab.scenarios import get_voice_lab_scenarios

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin/voice-lab", tags=["admin-voice-lab"])

VOICE_LAB_PERMISSION = "conversations:read"
MAX_VOICE_LAB_TRANSCRIPT_CHARS = 4000
MAX_REALTIME_SDP_CHARS = 200_000
OPENAI_REALTIME_CALLS_URL = "https://api.openai.com/v1/realtime/calls"
OPENAI_REALTIME_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"
OPENAI_REALTIME_TIMEOUT_SECONDS = 12.0
VOICE_LAB_REALTIME_LANGUAGES = {"tr", "en", "ru"}
VOICE_LAB_REALTIME_VOICES = {
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
}


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


class VoiceLabRealtimeClientSecretResponse(BaseModel):
    """Short-lived OpenAI Realtime credential for browser WebRTC setup."""

    value: str
    expires_at: int
    realtime_calls_url: str = OPENAI_REALTIME_CALLS_URL


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


@router.post("/realtime/session", response_class=PlainTextResponse)
async def create_voice_lab_realtime_session(
    request: Request,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: Annotated[int | None, Query(ge=1)] = None,
    language: Annotated[str, Query(max_length=8)] = "tr",
    voice: Annotated[str | None, Query(max_length=32)] = None,
) -> PlainTextResponse:
    """Proxy a browser WebRTC SDP offer to OpenAI Realtime without exposing the API key."""
    check_permission(current_user, VOICE_LAB_PERMISSION)
    scoped_hotel_id = resolve_hotel_scope(current_user, hotel_id)
    profile = _profile_for_hotel(scoped_hotel_id)
    offer_sdp = await _read_realtime_offer_sdp(request)
    session_config = build_voice_lab_realtime_session_config(
        profile=profile,
        language=normalize_voice_lab_realtime_language(language),
        voice=normalize_voice_lab_realtime_voice(voice),
    )
    answer_sdp = await request_openai_realtime_sdp_answer(
        offer_sdp=offer_sdp,
        session_config=session_config,
        hotel_id=scoped_hotel_id,
    )
    return PlainTextResponse(answer_sdp, media_type="application/sdp")


@router.post("/realtime/client-secret", response_model=VoiceLabRealtimeClientSecretResponse)
async def create_voice_lab_realtime_client_secret(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: Annotated[int | None, Query(ge=1)] = None,
    language: Annotated[str, Query(max_length=8)] = "tr",
    voice: Annotated[str | None, Query(max_length=32)] = None,
) -> VoiceLabRealtimeClientSecretResponse:
    """Create a short-lived OpenAI Realtime secret for browser-side SDP exchange."""
    check_permission(current_user, VOICE_LAB_PERMISSION)
    scoped_hotel_id = resolve_hotel_scope(current_user, hotel_id)
    profile = _profile_for_hotel(scoped_hotel_id)
    session_config = build_voice_lab_realtime_session_config(
        profile=profile,
        language=normalize_voice_lab_realtime_language(language),
        voice=normalize_voice_lab_realtime_voice(voice),
    )
    return await request_openai_realtime_client_secret(
        session_config=session_config,
        hotel_id=scoped_hotel_id,
    )


def _runner_for_hotel(hotel_id: int) -> VoiceLabRunner:
    """Build a Voice Lab runner for one loaded HOTEL_PROFILE."""
    return VoiceLabRunner(_profile_for_hotel(hotel_id))


def _profile_for_hotel(hotel_id: int) -> HotelProfile:
    """Load one HOTEL_PROFILE or raise a scoped admin error."""
    profile = get_profile(hotel_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seçili otel profili bulunamadı.",
        )
    return profile


async def _read_realtime_offer_sdp(request: Request) -> str:
    """Read and validate the browser WebRTC SDP offer body."""
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type != "application/sdp":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Realtime bağlantısı için application/sdp gövdesi gerekir.",
        )
    body = await request.body()
    if len(body) > MAX_REALTIME_SDP_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Realtime SDP teklifi izin verilen boyutu aşıyor.",
        )
    offer_sdp = body.decode("utf-8", errors="replace").strip()
    if not offer_sdp or not offer_sdp.startswith("v=0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçerli bir WebRTC SDP teklifi alınamadı.",
        )
    return offer_sdp


def normalize_voice_lab_realtime_language(value: str) -> str:
    """Normalize the first Voice Lab Realtime language set."""
    normalized = str(value or "tr").strip().lower()
    if normalized in VOICE_LAB_REALTIME_LANGUAGES:
        return normalized
    return "tr"


def normalize_voice_lab_realtime_voice(value: str | None) -> str:
    """Normalize OpenAI Realtime voice choice to a supported value."""
    normalized = str(value or settings.openai_realtime_voice or "marin").strip().lower()
    if normalized in VOICE_LAB_REALTIME_VOICES:
        return normalized
    fallback = settings.openai_realtime_voice.strip().lower()
    if fallback in VOICE_LAB_REALTIME_VOICES:
        return fallback
    return "marin"


def build_voice_lab_realtime_session_config(
    *,
    profile: HotelProfile,
    language: str,
    voice: str,
) -> dict[str, object]:
    """Build the OpenAI Realtime session config used by Voice Lab."""
    return {
        "type": "realtime",
        "model": settings.openai_realtime_model,
        "instructions": build_voice_lab_realtime_instructions(profile, language),
        "output_modalities": ["audio"],
        "audio": {
            "input": {
                "turn_detection": {
                    "type": "server_vad",
                    "create_response": True,
                    "interrupt_response": True,
                    "idle_timeout_ms": 8000,
                },
                "transcription": {
                    "model": "gpt-4o-mini-transcribe",
                    "language": language,
                },
            },
            "output": {"voice": voice},
        },
    }


def build_voice_lab_realtime_instructions(profile: HotelProfile, language: str) -> str:
    """Create grounded voice-agent instructions for Realtime Voice Lab sessions."""
    hotel_name = _localized_text(profile.hotel_name, language) or "Kassandra Oludeniz"
    language_label = {"tr": "Turkish", "en": "English", "ru": "Russian"}.get(language, "Turkish")
    return "\n".join(
        [
            f"You are the AI phone receptionist for {hotel_name}.",
            f"Speak {language_label} unless the caller clearly switches language.",
            "Use a calm, natural, professional hotel receptionist voice. Keep answers brief.",
            "This is an admin Voice Lab test session before live phone deployment.",
            "Do not claim to be human. If asked, be transparent that you are an AI assistant.",
            "Do not ask for or process card numbers, CVV, OTP, banking passwords, or identity numbers.",
            (
                "Prices, availability, reservation status, discounts, and currency guarantees require a "
                "verified tool or human handoff; never invent them."
            ),
            (
                "If you are unsure, ask one short clarifying question or say that you will transfer "
                "the request to the team."
            ),
            (
                "No database, PMS, WhatsApp message, ticket, or real booking is created from this "
                "Realtime lab session."
            ),
            "Opening disclosure: calls may be recorded for service quality and request handling.",
        ]
    )


def _localized_text(value: object, language: str) -> str:
    """Return a localized string from HOTEL_PROFILE multilingual fields."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        selected = value.get(language) or value.get("tr") or value.get("en")
        return str(selected or "").strip()
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        data = model_dump()
        selected = data.get(language) or data.get("tr") or data.get("en")
        return str(selected or "").strip()
    return str(value or "").strip()


async def request_openai_realtime_client_secret(
    *,
    session_config: dict[str, object],
    hotel_id: int,
) -> VoiceLabRealtimeClientSecretResponse:
    """Create an ephemeral OpenAI Realtime credential for direct browser WebRTC calls."""
    if not settings.openai_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime için OPENAI_API_KEY yapılandırılmalı.",
        )
    try:
        async with httpx.AsyncClient(timeout=OPENAI_REALTIME_TIMEOUT_SECONDS) as client:
            response = await client.post(
                OPENAI_REALTIME_CLIENT_SECRETS_URL,
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"session": session_config},
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        logger.warning("voice_lab_realtime_client_secret_timeout", hotel_id=hotel_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime client secret isteği zaman aşımına uğradı.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        error_summary = extract_openai_error_summary(exc.response)
        logger.warning(
            "voice_lab_realtime_client_secret_http_error",
            hotel_id=hotel_id,
            status_code=exc.response.status_code,
            openai_error_type=error_summary.get("type"),
            openai_error_code=error_summary.get("code"),
            openai_error_message=error_summary.get("message"),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime client secret oluşturulamadı.",
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("voice_lab_realtime_client_secret_transport_error", hotel_id=hotel_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime servisine ulaşılamadı.",
        ) from exc

    payload = response.json()
    value = str(payload.get("value") or "").strip()
    expires_at = payload.get("expires_at")
    if not value or not isinstance(expires_at, int):
        logger.warning(
            "voice_lab_realtime_client_secret_invalid_payload",
            hotel_id=hotel_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime client secret yanıtı geçersiz.",
        )
    logger.info(
        "voice_lab_realtime_client_secret_created",
        hotel_id=hotel_id,
        model=session_config.get("model"),
    )
    return VoiceLabRealtimeClientSecretResponse(value=value, expires_at=expires_at)


async def request_openai_realtime_sdp_answer(
    *,
    offer_sdp: str,
    session_config: dict[str, object],
    hotel_id: int,
) -> str:
    """Create an OpenAI Realtime WebRTC call and return the SDP answer."""
    if not settings.openai_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime için OPENAI_API_KEY yapılandırılmalı.",
        )
    files = {
        "sdp": (None, offer_sdp),
        "session": (None, json.dumps(session_config, ensure_ascii=False)),
    }
    try:
        async with httpx.AsyncClient(timeout=OPENAI_REALTIME_TIMEOUT_SECONDS) as client:
            response = await client.post(
                OPENAI_REALTIME_CALLS_URL,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                files=files,
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        logger.warning("voice_lab_realtime_timeout", hotel_id=hotel_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime bağlantısı zaman aşımına uğradı.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        error_summary = extract_openai_error_summary(exc.response)
        logger.warning(
            "voice_lab_realtime_http_error",
            hotel_id=hotel_id,
            status_code=exc.response.status_code,
            openai_error_type=error_summary.get("type"),
            openai_error_code=error_summary.get("code"),
            openai_error_message=error_summary.get("message"),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime oturumu başlatılamadı.",
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("voice_lab_realtime_transport_error", hotel_id=hotel_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime servisine ulaşılamadı.",
        ) from exc

    answer_sdp = response.text.strip()
    if not answer_sdp.startswith("v=0"):
        logger.warning("voice_lab_realtime_invalid_sdp_answer", hotel_id=hotel_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI Realtime geçerli SDP cevabı döndürmedi.",
        )
    audio_config = session_config.get("audio")
    voice = None
    if isinstance(audio_config, dict):
        output_config = audio_config.get("output")
        if isinstance(output_config, dict):
            voice = output_config.get("voice")
    logger.info(
        "voice_lab_realtime_session_created",
        hotel_id=hotel_id,
        model=session_config.get("model"),
        voice=voice,
    )
    return answer_sdp


def extract_openai_error_summary(response: httpx.Response) -> dict[str, str | None]:
    """Return a safe, truncated OpenAI error summary for logs."""
    summary: dict[str, str | None] = {"type": None, "code": None, "message": None}
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        summary["message"] = text[:300] if text else None
        return summary

    if not isinstance(payload, dict):
        summary["message"] = str(payload)[:300]
        return summary

    error = payload.get("error")
    if isinstance(error, dict):
        for key in ("type", "code", "message"):
            value = error.get(key)
            if value is not None:
                summary[key] = str(value)[:300]
        return summary

    message = payload.get("message")
    if message is not None:
        summary["message"] = str(message)[:300]
    return summary
