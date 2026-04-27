"""Admin WhatsApp Cloud API integration management routes."""

from __future__ import annotations

import secrets
import json
from datetime import UTC, datetime
from html import escape
from typing import Annotated, Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from velox.api.middleware.auth import TokenData, ensure_hotel_access, require_role
from velox.config.constants import Role
from velox.config.settings import settings
from velox.db.repositories.whatsapp_integration import WhatsAppIntegrationRepository
from velox.utils.token_cipher import (
    SecretCipher,
    SecretCipherNotConfiguredError,
    mask_secret,
    secret_last4,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin-whatsapp"])

GRAPH_TIMEOUT_SECONDS = 15.0
SUBSCRIBED_FIELDS = (
    "messages",
    "message_template_status_update",
    "phone_number_quality_update",
    "account_update",
)


class ManualIntegrationRequest(BaseModel):
    """Manual/admin-provided WhatsApp integration payload."""

    business_id: str | None = Field(default=None, max_length=64)
    waba_id: str | None = Field(default=None, max_length=64)
    phone_number_id: str = Field(min_length=3, max_length=64)
    display_phone_number: str | None = Field(default=None, max_length=32)
    verified_name: str | None = Field(default=None, max_length=255)
    quality_rating: str | None = Field(default=None, max_length=32)
    messaging_limit: str | None = Field(default=None, max_length=64)
    access_token: str | None = Field(default=None, max_length=8192)
    token_expires_at: datetime | None = None
    token_scopes: list[str] = Field(default_factory=list, max_length=20)
    webhook_verify_token: str | None = Field(default=None, max_length=256)

    @field_validator(
        "business_id",
        "waba_id",
        "phone_number_id",
        "display_phone_number",
        "verified_name",
        "quality_rating",
        "messaging_limit",
        "access_token",
        "webhook_verify_token",
        mode="before",
    )
    @classmethod
    def normalize_optional_string(cls, value: object) -> object:
        """Trim string fields and convert blanks to None except required phone_number_id."""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class TemplateCreateRequest(BaseModel):
    """Minimal local template draft payload.

    The first phase stores template metadata locally and syncs approved
    templates from Meta. Meta create/submit is intentionally separated so raw
    template text can be reviewed before calling Graph API.
    """

    name: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=2, max_length=32)
    category: str | None = Field(default=None, max_length=64)
    components: list[dict[str, Any]] = Field(default_factory=list)


class CompleteConnectSessionRequest(BaseModel):
    """Selected WhatsApp asset after Meta OAuth authorization."""

    phone_number_id: str = Field(min_length=3, max_length=64)
    waba_id: str | None = Field(default=None, max_length=64)


def _cipher() -> SecretCipher:
    return SecretCipher(settings.whatsapp_token_encryption_key)


def _require_encryption() -> SecretCipher:
    cipher = _cipher()
    if not cipher.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "WHATSAPP_TOKEN_ENCRYPTION_KEY tanımlı değil. "
                "Token saklamadan önce secret yönetimini yapılandırın."
            ),
        )
    return cipher


def _ensure_hotel_scope(user: TokenData, hotel_id: int) -> None:
    """Allow only admins to manage WhatsApp integration for the selected hotel."""
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu ekran sadece ADMIN rolüne açıktır.")
    ensure_hotel_access(user, hotel_id)


def _integration_public_payload(integration: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a UI-safe integration payload without encrypted values."""
    if integration is None:
        return None
    return {
        "id": integration.get("id"),
        "hotel_id": integration.get("hotel_id"),
        "business_id": integration.get("business_id"),
        "waba_id": integration.get("waba_id"),
        "phone_number_id": integration.get("phone_number_id"),
        "display_phone_number": integration.get("display_phone_number"),
        "verified_name": integration.get("verified_name"),
        "quality_rating": integration.get("quality_rating"),
        "messaging_limit": integration.get("messaging_limit"),
        "token_mask": mask_secret(integration.get("token_last4")),
        "token_expires_at": integration.get("token_expires_at"),
        "token_scopes": integration.get("token_scopes_json") or [],
        "webhook_token_stored": bool(integration.get("webhook_verify_token_ciphertext")),
        "webhook_status": integration.get("webhook_status"),
        "connection_status": integration.get("connection_status"),
        "last_health_check_at": integration.get("last_health_check_at"),
        "last_error_code": integration.get("last_error_code"),
        "last_error_message": integration.get("last_error_message"),
        "is_active": integration.get("is_active"),
        "created_at": integration.get("created_at"),
        "updated_at": integration.get("updated_at"),
    }


def _config_status() -> dict[str, Any]:
    """Return safe Meta/WhatsApp configuration readiness."""
    return {
        "meta_app_configured": bool(settings.meta_app_id and settings.meta_app_secret),
        "embedded_signup_configured": bool(settings.meta_embedded_signup_config_id),
        "token_encryption_configured": _cipher().is_configured,
        "webhook_url": settings.whatsapp_webhook_url,
        "oauth_redirect_url": settings.meta_oauth_redirect_url,
        "verify_token_configured": bool(settings.whatsapp_verify_token),
        "app_secret_configured": bool(settings.whatsapp_app_secret),
        "api_version": settings.whatsapp_api_version,
        "oauth_scopes": settings.meta_whatsapp_oauth_scope_list,
    }


def _build_signup_url(state_token: str) -> str:
    """Build the Meta popup URL used by the modal-driven connection flow."""
    query = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.meta_oauth_redirect_url,
        "state": state_token,
        "response_type": "code",
        "scope": ",".join(settings.meta_whatsapp_oauth_scope_list),
    }
    if settings.meta_embedded_signup_config_id:
        query["config_id"] = settings.meta_embedded_signup_config_id
    return f"https://www.facebook.com/{settings.whatsapp_api_version}/dialog/oauth?{urlencode(query)}"


async def _graph_get(path: str, access_token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call Meta Graph GET with bearer auth and return JSON."""
    async with httpx.AsyncClient(
        base_url=f"{settings.whatsapp_api_base_url.rstrip('/')}/{settings.whatsapp_api_version}",
        timeout=GRAPH_TIMEOUT_SECONDS,
        headers={"Authorization": f"Bearer {access_token}"},
    ) as client:
        response = await client.get(path, params=params or {})
    response.raise_for_status()
    return dict(response.json())


async def _graph_post(path: str, access_token: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call Meta Graph POST with bearer auth and return JSON."""
    async with httpx.AsyncClient(
        base_url=f"{settings.whatsapp_api_base_url.rstrip('/')}/{settings.whatsapp_api_version}",
        timeout=GRAPH_TIMEOUT_SECONDS,
        headers={"Authorization": f"Bearer {access_token}"},
    ) as client:
        response = await client.post(path, data=data or {})
    response.raise_for_status()
    return dict(response.json())


async def _exchange_oauth_code(code: str) -> str:
    """Exchange a Meta OAuth code for an access token."""
    async with httpx.AsyncClient(
        base_url=settings.whatsapp_api_base_url.rstrip("/"),
        timeout=GRAPH_TIMEOUT_SECONDS,
    ) as client:
        response = await client.get(
            f"/{settings.whatsapp_api_version}/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": settings.meta_oauth_redirect_url,
                "code": code,
            },
        )
    response.raise_for_status()
    payload = dict(response.json())
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Meta OAuth response did not include an access token.")
    return token


def _decrypt_token(record: dict[str, Any]) -> str:
    token_ciphertext = str(record.get("token_ciphertext") or "").strip()
    if not token_ciphertext:
        raise HTTPException(status_code=409, detail="Bu bağlantıda saklı access token yok.")
    try:
        return _require_encryption().decrypt(token_ciphertext)
    except SecretCipherNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail="Token şifreleme anahtarı yapılandırılmamış.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="Saklı access token çözülemedi. Yeniden bağlanın.") from exc


@router.get("/hotels/{hotel_id}/whatsapp/integration")
async def get_whatsapp_integration(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Return safe WhatsApp integration status for the selected hotel."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    integration = await repository.get_latest_for_hotel(hotel_id)
    events = await repository.list_events(hotel_id, limit=12)
    templates = await repository.list_templates(hotel_id)
    return {
        "config": _config_status(),
        "integration": _integration_public_payload(integration),
        "template_summary": {
            "total": len(templates),
            "approved": sum(1 for item in templates if str(item.get("status") or "").upper() == "APPROVED"),
            "pending": sum(1 for item in templates if str(item.get("status") or "").upper() == "PENDING"),
            "rejected": sum(1 for item in templates if str(item.get("status") or "").upper() == "REJECTED"),
        },
        "events": events,
    }


@router.post("/hotels/{hotel_id}/whatsapp/integration/manual")
async def save_manual_whatsapp_integration(
    hotel_id: int,
    body: ManualIntegrationRequest,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Save a manually provided integration without exposing secrets to the UI."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    existing = await repository.get_active_for_hotel(hotel_id)

    token_ciphertext = existing.get("token_ciphertext") if existing else None
    token_last4 = existing.get("token_last4") if existing else None
    token_expires_at = body.token_expires_at or (existing.get("token_expires_at") if existing else None)
    if body.access_token:
        cipher = _require_encryption()
        token_ciphertext = cipher.encrypt(body.access_token)
        token_last4 = secret_last4(body.access_token)

    verify_token_ciphertext = existing.get("webhook_verify_token_ciphertext") if existing else None
    if body.webhook_verify_token:
        verify_token_ciphertext = _require_encryption().encrypt(body.webhook_verify_token)

    integration = await repository.upsert_integration(
        hotel_id=hotel_id,
        business_id=body.business_id,
        waba_id=body.waba_id,
        phone_number_id=body.phone_number_id,
        display_phone_number=body.display_phone_number,
        verified_name=body.verified_name,
        quality_rating=body.quality_rating,
        messaging_limit=body.messaging_limit,
        token_ciphertext=token_ciphertext,
        token_last4=token_last4,
        token_expires_at=token_expires_at,
        token_scopes=body.token_scopes or (existing.get("token_scopes_json") if existing else []) or [],
        webhook_verify_token_ciphertext=verify_token_ciphertext,
        created_by_admin_id=user.user_id,
        connection_status="active" if token_ciphertext else "draft",
        webhook_status="unknown",
    )
    return {
        "status": "saved",
        "integration": _integration_public_payload(integration),
    }


@router.post("/hotels/{hotel_id}/whatsapp/connect-sessions")
async def create_whatsapp_connect_session(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Create a popup-driven Meta connection session."""
    _ensure_hotel_scope(user, hotel_id)
    config = _config_status()
    if not config["meta_app_configured"]:
        raise HTTPException(status_code=409, detail="Meta App ID ve App Secret tanımlı değil.")
    if not config["token_encryption_configured"]:
        raise HTTPException(status_code=503, detail="WHATSAPP_TOKEN_ENCRYPTION_KEY tanımlı değil.")

    state_token = secrets.token_urlsafe(48)
    repository = WhatsAppIntegrationRepository()
    session = await repository.create_connect_session(
        hotel_id=hotel_id,
        state_token=state_token,
        created_by_admin_id=user.user_id,
    )
    await repository.record_event(
        hotel_id=hotel_id,
        integration_id=None,
        connect_session_id=UUID(str(session["id"])),
        actor_admin_id=user.user_id,
        event_type="connect_session_created",
        safe_payload={"launch_mode": "popup"},
    )
    return {
        "session_id": session["id"],
        "status": session["status"],
        "expires_at": session["expires_at"],
        "auth_url": _build_signup_url(state_token),
        "launch_mode": "popup",
    }


@router.get("/hotels/{hotel_id}/whatsapp/connect-sessions/{session_id}")
async def get_whatsapp_connect_session(
    hotel_id: int,
    session_id: UUID,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Return connection-session status for modal polling."""
    _ensure_hotel_scope(user, hotel_id)
    session = await WhatsAppIntegrationRepository().get_connect_session(session_id, hotel_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Bağlantı oturumu bulunamadı.")
    return {
        "session_id": session["id"],
        "hotel_id": session["hotel_id"],
        "status": session["status"],
        "authorized": bool(session.get("token_ciphertext")),
        "token_mask": mask_secret(session.get("token_last4")),
        "selected_business_id": session.get("selected_business_id"),
        "selected_waba_id": session.get("selected_waba_id"),
        "selected_phone_number_id": session.get("selected_phone_number_id"),
        "error_code": session.get("error_code"),
        "error_message": session.get("error_message"),
        "expires_at": session.get("expires_at"),
    }


@router.get("/whatsapp/oauth/callback", include_in_schema=False)
async def whatsapp_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> HTMLResponse:
    """Receive Meta OAuth callback and notify the opener window."""
    repository = WhatsAppIntegrationRepository()
    session = await repository.get_connect_session_by_state((state or "").strip())
    if session is None:
        return _oauth_popup_response("error", "Bağlantı oturumu bulunamadı veya süresi doldu.")

    session_id = UUID(str(session["id"]))
    if error:
        safe_error = (error_description or error or "Meta bağlantısı tamamlanmadı.").strip()
        await repository.mark_connect_session_error(
            session_id=session_id,
            error_code=error[:128],
            error_message=safe_error,
        )
        return _oauth_popup_response("error", safe_error)

    if not code:
        await repository.mark_connect_session_error(
            session_id=session_id,
            error_code="missing_code",
            error_message="Meta callback kod içermiyor.",
        )
        return _oauth_popup_response("error", "Meta callback kod içermiyor.")

    try:
        token = await _exchange_oauth_code(code)
        cipher = _require_encryption()
        await repository.mark_connect_session_authorized(
            session_id=session_id,
            token_ciphertext=cipher.encrypt(token),
            token_last4=secret_last4(token),
        )
        await repository.record_event(
            hotel_id=int(session["hotel_id"]),
            integration_id=None,
            connect_session_id=session_id,
            actor_admin_id=session.get("created_by_admin_id"),
            event_type="oauth_authorized",
            safe_payload={"token_stored": True},
        )
        return _oauth_popup_response("authorized", "Meta yetkilendirmesi tamamlandı.")
    except Exception as exc:
        logger.warning("whatsapp_oauth_callback_failed", error_type=type(exc).__name__)
        await repository.mark_connect_session_error(
            session_id=session_id,
            error_code=type(exc).__name__,
            error_message="Meta yetkilendirmesi tamamlanamadı.",
        )
        return _oauth_popup_response("error", "Meta yetkilendirmesi tamamlanamadı.")


@router.get("/hotels/{hotel_id}/whatsapp/assets")
async def list_whatsapp_assets(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    session_id: UUID | None = Query(default=None),
) -> dict[str, Any]:
    """List Business/WABA/phone assets available through the stored token."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    token_owner: dict[str, Any] | None = None
    if session_id is not None:
        token_owner = await repository.get_connect_session(session_id, hotel_id)
    if token_owner is None:
        token_owner = await repository.get_active_for_hotel(hotel_id)
    if token_owner is None:
        raise HTTPException(status_code=404, detail="Bağlantı veya token bulunamadı.")

    access_token = _decrypt_token(token_owner)
    try:
        items = await _list_whatsapp_assets_for_token(access_token)
        return {"items": items}
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise HTTPException(
            status_code=502,
            detail=f"Meta varlıkları alınamadı. Graph API HTTP {status_code}.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Meta Graph API bağlantısı kurulamadı.") from exc


@router.post("/hotels/{hotel_id}/whatsapp/connect-sessions/{session_id}/complete")
async def complete_whatsapp_connect_session(
    hotel_id: int,
    session_id: UUID,
    body: CompleteConnectSessionRequest,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Create the active integration from an authorized popup session and selected phone number."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    session = await repository.get_connect_session(session_id, hotel_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Bağlantı oturumu bulunamadı.")
    if session.get("status") not in {"authorized", "completed"}:
        raise HTTPException(status_code=409, detail="Meta yetkilendirmesi henüz tamamlanmadı.")
    expires_at = session.get("expires_at")
    if isinstance(expires_at, datetime) and expires_at < datetime.now(UTC):
        await repository.mark_connect_session_error(
            session_id=session_id,
            error_code="expired",
            error_message="Bağlantı oturumunun süresi doldu.",
        )
        raise HTTPException(status_code=409, detail="Bağlantı oturumunun süresi doldu. Yeniden bağlanın.")

    access_token = _decrypt_token(session)
    try:
        assets = await _list_whatsapp_assets_for_token(access_token)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Meta varlıkları doğrulanamadı. Graph API HTTP {exc.response.status_code}.",
        ) from exc
    selected = next(
        (
            item
            for item in assets
            if str(item.get("phone_number_id") or "") == body.phone_number_id
            and (body.waba_id is None or str(item.get("waba_id") or "") == body.waba_id)
        ),
        None,
    )
    if selected is None:
        raise HTTPException(status_code=409, detail="Seçilen WhatsApp numarası Meta varlıkları içinde bulunamadı.")

    integration = await repository.upsert_integration(
        hotel_id=hotel_id,
        business_id=str(selected.get("business_id") or "").strip() or None,
        waba_id=str(selected.get("waba_id") or "").strip() or None,
        phone_number_id=str(selected["phone_number_id"]),
        display_phone_number=str(selected.get("display_phone_number") or "").strip() or None,
        verified_name=str(selected.get("verified_name") or "").strip() or None,
        quality_rating=str(selected.get("quality_rating") or "").strip() or None,
        messaging_limit=None,
        token_ciphertext=str(session.get("token_ciphertext") or ""),
        token_last4=session.get("token_last4"),
        token_expires_at=None,
        token_scopes=settings.meta_whatsapp_oauth_scope_list,
        webhook_verify_token_ciphertext=None,
        created_by_admin_id=user.user_id,
        connection_status="webhook_pending",
        webhook_status="pending",
    )
    completed_session = await repository.complete_connect_session(
        session_id=session_id,
        business_id=integration.get("business_id"),
        waba_id=str(integration.get("waba_id") or ""),
        phone_number_id=str(integration.get("phone_number_id") or ""),
    )
    await repository.record_event(
        hotel_id=hotel_id,
        integration_id=int(integration["id"]),
        connect_session_id=session_id,
        actor_admin_id=user.user_id,
        event_type="asset_selected",
        safe_payload={
            "business_id": integration.get("business_id"),
            "waba_id": integration.get("waba_id"),
            "phone_number_id": integration.get("phone_number_id"),
        },
    )
    return {
        "status": "completed",
        "session": {
            "session_id": completed_session["id"],
            "status": completed_session["status"],
        },
        "integration": _integration_public_payload(integration),
    }


async def _list_whatsapp_assets_for_token(access_token: str) -> list[dict[str, Any]]:
    """Return WhatsApp Business assets available to the OAuth token."""
    businesses_payload = await _graph_get("/me/businesses", access_token, {"fields": "id,name"})
    businesses = businesses_payload.get("data") if isinstance(businesses_payload.get("data"), list) else []
    items: list[dict[str, Any]] = []
    for business in businesses:
        business_id = str(business.get("id") or "").strip()
        if not business_id:
            continue
        wabas = await _list_business_wabas(business_id, access_token)
        for waba in wabas:
            waba_id = str(waba.get("id") or "").strip()
            if not waba_id:
                continue
            phones_payload = await _graph_get(
                f"/{waba_id}/phone_numbers",
                access_token,
                {"fields": "id,display_phone_number,verified_name,quality_rating"},
            )
            phones = phones_payload.get("data") if isinstance(phones_payload.get("data"), list) else []
            for phone in phones:
                phone_number_id = str(phone.get("id") or "").strip()
                if not phone_number_id:
                    continue
                items.append(
                    {
                        "business_id": business_id,
                        "business_name": business.get("name"),
                        "waba_id": waba_id,
                        "waba_name": waba.get("name"),
                        "phone_number_id": phone_number_id,
                        "display_phone_number": phone.get("display_phone_number"),
                        "verified_name": phone.get("verified_name"),
                        "quality_rating": phone.get("quality_rating"),
                    }
                )
    return items


async def _list_business_wabas(business_id: str, access_token: str) -> list[dict[str, Any]]:
    """Return owned and client WABAs for a business id."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for edge in ("owned_whatsapp_business_accounts", "client_whatsapp_business_accounts"):
        try:
            payload = await _graph_get(f"/{business_id}/{edge}", access_token, {"fields": "id,name"})
        except httpx.HTTPStatusError:
            continue
        for item in payload.get("data") if isinstance(payload.get("data"), list) else []:
            item_id = str(item.get("id") or "").strip()
            if item_id and item_id not in seen:
                result.append(dict(item))
                seen.add(item_id)
    return result


@router.post("/hotels/{hotel_id}/whatsapp/health-check")
async def check_whatsapp_integration_health(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Validate local settings and the active Meta phone number token."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    integration = await repository.get_active_for_hotel(hotel_id)
    if integration is None:
        raise HTTPException(status_code=404, detail="Aktif WhatsApp bağlantısı yok.")

    errors: list[str] = []
    if not settings.whatsapp_app_secret:
        errors.append("WHATSAPP_APP_SECRET eksik.")
    if not settings.whatsapp_verify_token:
        errors.append("WHATSAPP_VERIFY_TOKEN eksik.")
    access_token = _decrypt_token(integration)

    graph_payload: dict[str, Any] = {}
    try:
        graph_payload = await _graph_get(
            f"/{integration['phone_number_id']}",
            access_token,
            {"fields": "id,display_phone_number,verified_name,quality_rating"},
        )
    except httpx.HTTPStatusError as exc:
        errors.append(f"Meta phone number kontrolü başarısız: HTTP {exc.response.status_code}.")
    except httpx.RequestError:
        errors.append("Meta Graph API bağlantısı kurulamadı.")

    next_status = "active" if not errors else "degraded"
    updated = await repository.update_health(
        integration_id=int(integration["id"]),
        hotel_id=hotel_id,
        connection_status=next_status,
        webhook_status="verified" if settings.whatsapp_verify_token else "failed",
        quality_rating=str(graph_payload.get("quality_rating") or integration.get("quality_rating") or "") or None,
        last_error_code=None if not errors else "health_check_failed",
        last_error_message=" | ".join(errors) if errors else None,
    )
    await repository.record_event(
        hotel_id=hotel_id,
        integration_id=int(updated["id"]),
        connect_session_id=None,
        actor_admin_id=user.user_id,
        event_type="health_check",
        safe_payload={"ok": not errors, "error_count": len(errors)},
    )
    return {
        "ok": not errors,
        "errors": errors,
        "integration": _integration_public_payload(updated),
        "graph": {
            "id": graph_payload.get("id"),
            "display_phone_number": graph_payload.get("display_phone_number"),
            "verified_name": graph_payload.get("verified_name"),
            "quality_rating": graph_payload.get("quality_rating"),
        },
    }


@router.post("/hotels/{hotel_id}/whatsapp/webhook/subscribe")
async def subscribe_whatsapp_webhook(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Subscribe the active WABA to app webhook fields."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    integration = await repository.get_active_for_hotel(hotel_id)
    if integration is None:
        raise HTTPException(status_code=404, detail="Aktif WhatsApp bağlantısı yok.")
    waba_id = str(integration.get("waba_id") or "").strip()
    if not waba_id:
        raise HTTPException(status_code=409, detail="WABA ID eksik.")
    access_token = _decrypt_token(integration)
    try:
        payload = await _graph_post(
            f"/{waba_id}/subscribed_apps",
            access_token,
            {"subscribed_fields": ",".join(SUBSCRIBED_FIELDS)},
        )
        updated = await repository.update_health(
            integration_id=int(integration["id"]),
            hotel_id=hotel_id,
            connection_status="active",
            webhook_status="verified",
            last_error_code=None,
            last_error_message=None,
        )
        await repository.record_event(
            hotel_id=hotel_id,
            integration_id=int(updated["id"]),
            connect_session_id=None,
            actor_admin_id=user.user_id,
            event_type="webhook_subscribed",
            safe_payload={"fields": list(SUBSCRIBED_FIELDS), "meta_success": bool(payload.get("success", True))},
        )
        return {"status": "subscribed", "integration": _integration_public_payload(updated)}
    except httpx.HTTPStatusError as exc:
        await repository.update_health(
            integration_id=int(integration["id"]),
            hotel_id=hotel_id,
            connection_status="degraded",
            webhook_status="failed",
            last_error_code=f"graph_http_{exc.response.status_code}",
            last_error_message="Webhook aboneliği Meta tarafından reddedildi.",
        )
        raise HTTPException(
            status_code=502,
            detail=f"Webhook aboneliği tamamlanamadı. Graph API HTTP {exc.response.status_code}.",
        ) from exc


@router.get("/hotels/{hotel_id}/whatsapp/templates")
async def list_whatsapp_templates(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Return local WhatsApp template snapshots."""
    _ensure_hotel_scope(user, hotel_id)
    templates = await WhatsAppIntegrationRepository().list_templates(hotel_id)
    return {"items": templates}


@router.post("/hotels/{hotel_id}/whatsapp/templates")
async def create_local_whatsapp_template(
    hotel_id: int,
    body: TemplateCreateRequest,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Store a local template draft for review before Meta submission."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    integration = await repository.get_active_for_hotel(hotel_id)
    if integration is None or not integration.get("waba_id"):
        raise HTTPException(status_code=409, detail="Template için aktif WABA bağlantısı gerekli.")
    template = await repository.upsert_template(
        hotel_id=hotel_id,
        waba_id=str(integration["waba_id"]),
        meta_template_id=None,
        name=body.name.strip(),
        language=body.language.strip(),
        category=body.category.strip() if body.category else None,
        status="LOCAL_DRAFT",
        components=body.components,
        rejection_reason=None,
    )
    await repository.record_event(
        hotel_id=hotel_id,
        integration_id=int(integration["id"]),
        connect_session_id=None,
        actor_admin_id=user.user_id,
        event_type="template_draft_saved",
        safe_payload={"name": body.name.strip(), "language": body.language.strip()},
    )
    return {"status": "saved", "template": template}


@router.post("/hotels/{hotel_id}/whatsapp/templates/sync")
async def sync_whatsapp_templates(
    hotel_id: int,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Sync message template status snapshots from Meta."""
    _ensure_hotel_scope(user, hotel_id)
    repository = WhatsAppIntegrationRepository()
    integration = await repository.get_active_for_hotel(hotel_id)
    if integration is None:
        raise HTTPException(status_code=404, detail="Aktif WhatsApp bağlantısı yok.")
    waba_id = str(integration.get("waba_id") or "").strip()
    if not waba_id:
        raise HTTPException(status_code=409, detail="WABA ID eksik.")
    access_token = _decrypt_token(integration)
    try:
        payload = await _graph_get(
            f"/{waba_id}/message_templates",
            access_token,
            {"fields": "id,name,language,status,category,components,rejected_reason"},
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Template senkronizasyonu başarısız. Graph API HTTP {exc.response.status_code}.",
        ) from exc
    items = payload.get("data") if isinstance(payload.get("data"), list) else []
    synced = []
    for item in items:
        name = str(item.get("name") or "").strip()
        language = str(item.get("language") or "").strip()
        if not name or not language:
            continue
        components = item.get("components") if isinstance(item.get("components"), list) else []
        synced.append(
            await repository.upsert_template(
                hotel_id=hotel_id,
                waba_id=waba_id,
                meta_template_id=str(item.get("id") or "").strip() or None,
                name=name,
                language=language,
                category=str(item.get("category") or "").strip() or None,
                status=str(item.get("status") or "UNKNOWN").strip().upper(),
                components=[dict(component) for component in components],
                rejection_reason=str(item.get("rejected_reason") or "").strip() or None,
            )
        )
    await repository.record_event(
        hotel_id=hotel_id,
        integration_id=int(integration["id"]),
        connect_session_id=None,
        actor_admin_id=user.user_id,
        event_type="templates_synced",
        safe_payload={"count": len(synced)},
    )
    return {"status": "synced", "count": len(synced), "items": synced}


def _oauth_popup_response(status_value: str, message: str) -> HTMLResponse:
    """Return a tiny popup page that notifies the admin panel and closes."""
    safe_status = status_value.replace("<", "")
    safe_message = escape(message)
    event_payload = json.dumps(
        {"type": "velox:whatsapp-oauth", "status": safe_status, "message": message},
        ensure_ascii=False,
    )
    return HTMLResponse(
        content=f"""\
<!doctype html>
<html lang="tr">
<head><meta charset="utf-8"><title>WhatsApp Bağlantısı</title></head>
<body>
  <p>{safe_message}</p>
  <script>
    if (window.opener) {{
      window.opener.postMessage({event_payload}, window.location.origin);
    }}
    window.close();
  </script>
</body>
</html>
""",
        headers={"Cache-Control": "no-store"},
    )
