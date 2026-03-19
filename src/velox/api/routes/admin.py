"""Admin panel REST API routes."""

from datetime import UTC, date, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

import asyncpg
import orjson
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from passlib.hash import bcrypt
from pydantic import BaseModel, Field, field_validator

from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.api.middleware.auth import (
    TokenData,
    TokenResponse,
    check_permission,
    create_access_token,
    get_current_user,
    require_role,
)
from velox.config.constants import HoldStatus, Role
from velox.config.settings import settings
from velox.core.hotel_profile_loader import reload_profiles, save_profile_definition
from velox.core.template_engine import reload_templates
from velox.db.repositories.conversation import ConversationRepository
from velox.db.repositories.hotel import NotificationPhoneRepository
from velox.db.repositories.restaurant import RestaurantRepository
from velox.db.repositories.transfer import TransferRepository
from velox.escalation.matrix import reload_matrix
from velox.models.hotel_profile import FAQEntry, FAQStatus, HotelProfile
from velox.models.restaurant import RestaurantSlotCreate, RestaurantSlotUpdate
from velox.models.webhook_events import ApprovalEvent
from velox.utils.admin_security import (
    DEFAULT_SESSION_PRESET,
    DEFAULT_VERIFICATION_PRESET,
    SESSION_DURATION_OPTIONS,
    TRUSTED_DEVICE_COOKIE_NAME,
    VERIFICATION_DURATION_OPTIONS,
    fetch_trusted_device_record,
    generate_csrf_token,
    refresh_trusted_device_session,
    resolve_session_seconds,
    resolve_verification_seconds,
    set_access_cookie,
    set_csrf_cookie,
    set_trusted_device_cookie,
    trusted_device_is_active,
    upsert_trusted_device_record,
)
from velox.utils.id_gen import next_sequential_id
from velox.utils.json import decode_json_object
from velox.utils.privacy import hash_phone
from velox.utils.totp import verify_totp_code

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_HOLD_TYPES = {"stay", "restaurant", "transfer"}
HOLD_TABLES = {
    "S_HOLD_": ("stay_holds", "stay"),
    "R_HOLD_": ("restaurant_holds", "restaurant"),
    "TR_HOLD_": ("transfer_holds", "transfer"),
}
ALLOWED_TICKET_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
ALLOWED_TICKET_PRIORITIES = {"low", "medium", "high"}
ALLOWED_VERIFICATION_PRESETS = {item.value for item in VERIFICATION_DURATION_OPTIONS}
ALLOWED_SESSION_PRESETS = {item.value for item in SESSION_DURATION_OPTIONS}
FAQ_FILTER_STATUSES = {status.value for status in FAQStatus}
FAQ_MANAGE_STATUSES = {FAQStatus.DRAFT.value, FAQStatus.ACTIVE.value, FAQStatus.PAUSED.value}


class LoginRequest(BaseModel):
    username: str
    password: str
    otp_code: str | None = Field(default=None, min_length=6, max_length=8)
    remember_device: bool = False
    verification_preset: str = DEFAULT_VERIFICATION_PRESET
    session_preset: str = DEFAULT_SESSION_PRESET

    @field_validator("verification_preset")
    @classmethod
    def validate_verification_preset(cls, value: str) -> str:
        """Reject unsupported verification presets."""
        if value not in ALLOWED_VERIFICATION_PRESETS:
            raise ValueError("Unsupported verification preset")
        return value

    @field_validator("session_preset")
    @classmethod
    def validate_session_preset(cls, value: str) -> str:
        """Reject unsupported session presets."""
        if value not in ALLOWED_SESSION_PRESETS:
            raise ValueError("Unsupported session preset")
        return value


class HotelProfileUpdate(BaseModel):
    profile_json: dict[str, Any]


class FAQCreateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=120)
    question_tr: str = Field(default="", max_length=500)
    question_en: str = Field(default="", max_length=500)
    answer_tr: str = Field(min_length=1, max_length=4000)
    answer_en: str = Field(min_length=1, max_length=4000)
    question_variants_tr: list[str] = Field(default_factory=list)
    question_variants_en: list[str] = Field(default_factory=list)
    question_variants_ru: list[str] = Field(default_factory=list)
    question_variants_de: list[str] = Field(default_factory=list)
    question_variants_ar: list[str] = Field(default_factory=list)
    question_variants_es: list[str] = Field(default_factory=list)
    question_variants_fr: list[str] = Field(default_factory=list)
    question_variants_zh: list[str] = Field(default_factory=list)
    question_variants_hi: list[str] = Field(default_factory=list)
    question_variants_pt: list[str] = Field(default_factory=list)
    status: FAQStatus = FAQStatus.DRAFT


class FAQUpdateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=120)
    question_tr: str = Field(default="", max_length=500)
    question_en: str = Field(default="", max_length=500)
    answer_tr: str = Field(min_length=1, max_length=4000)
    answer_en: str = Field(min_length=1, max_length=4000)
    question_variants_tr: list[str] = Field(default_factory=list)
    question_variants_en: list[str] = Field(default_factory=list)
    question_variants_ru: list[str] = Field(default_factory=list)
    question_variants_de: list[str] = Field(default_factory=list)
    question_variants_ar: list[str] = Field(default_factory=list)
    question_variants_es: list[str] = Field(default_factory=list)
    question_variants_fr: list[str] = Field(default_factory=list)
    question_variants_zh: list[str] = Field(default_factory=list)
    question_variants_hi: list[str] = Field(default_factory=list)
    question_variants_pt: list[str] = Field(default_factory=list)
    status: FAQStatus = FAQStatus.DRAFT


class FAQStatusUpdateRequest(BaseModel):
    status: FAQStatus


class FAQRemoveRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class ApproveRequest(BaseModel):
    notes: str | None = None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1)


class TicketUpdate(BaseModel):
    status: str | None = None
    assigned_to_role: str | None = None
    assigned_to_name: str | None = None


def _now_iso() -> str:
    """Return an ISO-8601 UTC timestamp for FAQ metadata fields."""
    return datetime.now(UTC).isoformat()


def _faq_allowed_actions(status: FAQStatus) -> list[str]:
    """Map FAQ status to the admin actions allowed from panel."""
    if status == FAQStatus.DRAFT:
        return ["activate", "edit", "remove"]
    if status == FAQStatus.ACTIVE:
        return ["pause", "edit", "remove"]
    if status == FAQStatus.PAUSED:
        return ["activate", "edit", "remove"]
    return []


def _faq_to_payload(entry: FAQEntry) -> dict[str, Any]:
    """Return admin-facing FAQ shape with grouped localized fields."""
    return {
        "faq_id": entry.faq_id,
        "topic": entry.topic,
        "status": entry.status.value,
        "question": {"tr": entry.question_tr, "en": entry.question_en},
        "answer": {"tr": entry.answer_tr, "en": entry.answer_en},
        "question_variants": {
            "tr": entry.question_variants_tr,
            "en": entry.question_variants_en,
            "ru": entry.question_variants_ru,
            "de": entry.question_variants_de,
            "ar": entry.question_variants_ar,
            "es": entry.question_variants_es,
            "fr": entry.question_variants_fr,
            "zh": entry.question_variants_zh,
            "hi": entry.question_variants_hi,
            "pt": entry.question_variants_pt,
        },
        "created_at": entry.created_at,
        "created_by": entry.created_by,
        "updated_at": entry.updated_at,
        "updated_by": entry.updated_by,
        "removed_at": entry.removed_at,
        "removed_by": entry.removed_by,
        "removed_reason": entry.removed_reason,
        "allowed_actions": _faq_allowed_actions(entry.status),
    }


def _faq_search_blob(entry: FAQEntry) -> str:
    """Build a single lowercase text blob used by FAQ search filter."""
    parts = [
        entry.topic,
        entry.question_tr,
        entry.question_en,
        entry.answer_tr,
        entry.answer_en,
        *entry.question_variants_tr,
        *entry.question_variants_en,
        *entry.question_variants_ru,
        *entry.question_variants_de,
        *entry.question_variants_ar,
        *entry.question_variants_es,
        *entry.question_variants_fr,
        *entry.question_variants_zh,
        *entry.question_variants_hi,
        *entry.question_variants_pt,
    ]
    return " ".join(parts).casefold()


def _build_faq_entry(
    body: FAQCreateRequest | FAQUpdateRequest,
    *,
    faq_id: str,
    created_at: str,
    created_by: str,
    updated_at: str,
    updated_by: str,
    removed_at: str | None = None,
    removed_by: str | None = None,
    removed_reason: str | None = None,
) -> FAQEntry:
    """Create a normalized FAQEntry from create/update request payload."""
    return FAQEntry(
        faq_id=faq_id,
        topic=body.topic.strip(),
        status=body.status,
        question_tr=body.question_tr.strip(),
        question_en=body.question_en.strip(),
        answer_tr=body.answer_tr.strip(),
        answer_en=body.answer_en.strip(),
        question_variants_tr=[item.strip() for item in body.question_variants_tr if item.strip()],
        question_variants_en=[item.strip() for item in body.question_variants_en if item.strip()],
        question_variants_ru=[item.strip() for item in body.question_variants_ru if item.strip()],
        question_variants_de=[item.strip() for item in body.question_variants_de if item.strip()],
        question_variants_ar=[item.strip() for item in body.question_variants_ar if item.strip()],
        question_variants_es=[item.strip() for item in body.question_variants_es if item.strip()],
        question_variants_fr=[item.strip() for item in body.question_variants_fr if item.strip()],
        question_variants_zh=[item.strip() for item in body.question_variants_zh if item.strip()],
        question_variants_hi=[item.strip() for item in body.question_variants_hi if item.strip()],
        question_variants_pt=[item.strip() for item in body.question_variants_pt if item.strip()],
        created_at=created_at,
        created_by=created_by,
        updated_at=updated_at,
        updated_by=updated_by,
        removed_at=removed_at,
        removed_by=removed_by,
        removed_reason=removed_reason,
    )


@router.post("/login", response_model=TokenResponse)
async def admin_login(body: LoginRequest, request: Request, response: Response) -> TokenResponse:
    """Authenticate admin user and return JWT token."""
    db = request.app.state.db_pool
    authentication_mode = "otp"
    trusted_device_enabled = False
    verification_expires_at = None
    session_expires_at = None
    current_device = None
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, hotel_id, username, password_hash, role, display_name, totp_secret, is_active
            FROM admin_users WHERE username = $1
            """,
            body.username,
        )
        if not row or not bcrypt.verify(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not row["is_active"]:
            raise HTTPException(status_code=403, detail="Account disabled")

        trusted_device_record = await fetch_trusted_device_record(
            conn,
            request.cookies.get(TRUSTED_DEVICE_COOKIE_NAME),
        )
        current_device = (
            trusted_device_record
            if trusted_device_record is not None and int(trusted_device_record["admin_user_id"]) == int(row["id"])
            else None
        )

        totp_secret = str(row["totp_secret"] or "").strip()
        if not totp_secret:
            raise HTTPException(status_code=403, detail="Two-factor authentication is not configured for this account")
        if body.otp_code:
            if not verify_totp_code(totp_secret, body.otp_code):
                raise HTTPException(status_code=401, detail="Invalid credentials")
        elif current_device is not None and trusted_device_is_active(current_device.get("verification_expires_at")):
            authentication_mode = "trusted_device"
        else:
            raise HTTPException(status_code=401, detail="Google Authenticator kodu gerekli")

        if body.remember_device:
            device_token = await upsert_trusted_device_record(
                conn,
                admin_user=dict(row),
                request=request,
                verification_preset=body.verification_preset,
                session_preset=body.session_preset,
                existing_device_id=current_device["id"] if current_device is not None else None,
            )
            remember_seconds = max(
                resolve_verification_seconds(body.verification_preset),
                resolve_session_seconds(body.session_preset),
            )
            set_trusted_device_cookie(
                response,
                device_token.cookie_value,
                max_age_seconds=max(remember_seconds, 60),
            )
            trusted_device_enabled = True
            verification_expires_at = device_token.verification_expires_at
            session_expires_at = device_token.session_expires_at
        elif current_device is not None:
            trusted_device_enabled = True
            verification_expires_at = current_device.get("verification_expires_at")
            session_expires_at = await refresh_trusted_device_session(
                conn,
                current_device["id"],
                str(current_device["session_preset"]),
            )

    token_data = TokenData(
        user_id=int(row["id"]),
        hotel_id=int(row["hotel_id"]),
        username=str(row["username"]),
        role=Role(row["role"]),
        display_name=row["display_name"],
    )
    access_token = create_access_token(token_data)
    access_max_age = settings.admin_jwt_expire_minutes * 60
    csrf_token = generate_csrf_token()
    set_access_cookie(response, access_token, max_age_seconds=access_max_age)
    set_csrf_cookie(response, csrf_token, max_age_seconds=access_max_age)
    return TokenResponse(
        access_token=access_token,
        expires_in=access_max_age,
        role=token_data.role.value,
        hotel_id=token_data.hotel_id,
        authentication_mode=authentication_mode,
        trusted_device_enabled=trusted_device_enabled,
        verification_expires_at=verification_expires_at,
        session_expires_at=session_expires_at,
    )


@router.post("/reload-config")
async def reload_config(user: Annotated[TokenData, Depends(require_role(Role.ADMIN))]) -> dict[str, object]:
    """Reload profile, escalation matrix, and templates from disk."""
    _ = user
    profiles = reload_profiles()
    matrix = reload_matrix()
    templates = reload_templates()
    return {
        "reloaded": True,
        "profiles_count": len(profiles),
        "matrix_entries_count": len(matrix),
        "templates_count": len(templates),
    }


@router.get("/hotels")
async def list_hotels(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    """List hotels; ADMIN sees all, others see own hotel."""
    check_permission(user, "hotels:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        if user.role == Role.ADMIN:
            rows = await conn.fetch(
                """
                SELECT id, hotel_id, name_tr, name_en, hotel_type, is_active, created_at
                FROM hotels ORDER BY id
                """
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, hotel_id, name_tr, name_en, hotel_type, is_active, created_at
                FROM hotels WHERE hotel_id = $1
                """,
                user.hotel_id,
            )
    return [dict(row) for row in rows]


@router.get("/hotels/{hotel_id}")
async def get_hotel(
    hotel_id: int,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return hotel detail with profile JSON."""
    check_permission(user, "hotels:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM hotels WHERE hotel_id = $1", hotel_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return dict(row)


@router.put("/hotels/{hotel_id}/profile")
async def update_hotel_profile(
    hotel_id: int,
    body: HotelProfileUpdate,
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Update hotel profile JSON, persist YAML, and refresh runtime cache."""
    _ = user
    try:
        profile_path = save_profile_definition(body.profile_json)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE hotels
            SET profile_json = $1, updated_at = now()
            WHERE hotel_id = $2
            """,
            body.profile_json,
            hotel_id,
        )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Hotel not found")
    reload_profiles()
    return {"status": "updated", "hotel_id": hotel_id, "profile_path": profile_path.name}


async def _load_hotel_profile(
    conn: Any,
    hotel_id: int,
) -> tuple[dict[str, Any], HotelProfile]:
    """Load hotel DB row plus validated profile model for FAQ operations."""
    row = await conn.fetchrow("SELECT * FROM hotels WHERE hotel_id = $1", hotel_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    row_payload = dict(row)
    profile_json = decode_json_object(row_payload.get("profile_json"))
    row_payload["profile_json"] = profile_json
    return row_payload, HotelProfile.model_validate(profile_json)


async def _persist_hotel_profile(
    conn: Any,
    hotel_id: int,
    profile_json: dict[str, Any],
) -> str:
    """Persist hotel profile to YAML + DB and return profile file name."""
    profile_path = save_profile_definition(profile_json)
    result = await conn.execute(
        """
        UPDATE hotels
        SET profile_json = $1, updated_at = now()
        WHERE hotel_id = $2
        """,
        profile_json,
        hotel_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Hotel not found")
    reload_profiles()
    return profile_path.name


def _ensure_faq_integrity(faq_items: list[FAQEntry]) -> tuple[list[FAQEntry], bool]:
    """Backfill missing FAQ ids and metadata so admin actions stay stable."""
    changed = False
    normalized: list[FAQEntry] = []
    for entry in faq_items:
        updated_entry = entry.model_copy(deep=True)
        if not updated_entry.faq_id:
            updated_entry.faq_id = str(uuid4())
            changed = True
        if not updated_entry.created_at:
            updated_entry.created_at = _now_iso()
            changed = True
        if not updated_entry.updated_at:
            updated_entry.updated_at = updated_entry.created_at
            changed = True
        if not updated_entry.created_by:
            updated_entry.created_by = "system"
            changed = True
        if not updated_entry.updated_by:
            updated_entry.updated_by = "system"
            changed = True
        normalized.append(updated_entry)
    return normalized, changed


@router.get("/hotels/{hotel_id}/faq")
async def list_hotel_faq_entries(
    hotel_id: int,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
) -> dict[str, Any]:
    """List FAQ items with status/search filters for admin review."""
    check_permission(user, "hotels:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")
    if status_filter and status_filter not in FAQ_FILTER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid FAQ status")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        _, profile = await _load_hotel_profile(conn, hotel_id)
        normalized_faq, changed = _ensure_faq_integrity(profile.faq_data)
        if changed:
            profile.faq_data = normalized_faq
            await _persist_hotel_profile(conn, hotel_id, profile.model_dump(mode="json"))
        filtered_items = normalized_faq
        if status_filter:
            filtered_items = [entry for entry in filtered_items if entry.status.value == status_filter]
        if q:
            search_token = q.casefold().strip()
            filtered_items = [entry for entry in filtered_items if search_token in _faq_search_blob(entry)]
    items = [_faq_to_payload(entry) for entry in filtered_items]
    return {"items": items, "total": len(items)}


@router.post("/hotels/{hotel_id}/faq")
async def create_hotel_faq_entry(
    hotel_id: int,
    body: FAQCreateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Create a new FAQ entry and publish it to runtime profile cache."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        _, profile = await _load_hotel_profile(conn, hotel_id)
        normalized_faq, changed = _ensure_faq_integrity(profile.faq_data)
        now_iso = _now_iso()
        new_entry = _build_faq_entry(
            body,
            faq_id=str(uuid4()),
            created_at=now_iso,
            created_by=user.username,
            updated_at=now_iso,
            updated_by=user.username,
        )
        normalized_faq.append(new_entry)
        profile.faq_data = normalized_faq
        profile_name = await _persist_hotel_profile(conn, hotel_id, profile.model_dump(mode="json"))
    return {
        "status": "created",
        "profile_path": profile_name,
        "item": _faq_to_payload(new_entry),
        "normalized": changed,
    }


@router.put("/hotels/{hotel_id}/faq/{faq_id}")
async def update_hotel_faq_entry(
    hotel_id: int,
    faq_id: str,
    body: FAQUpdateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Update FAQ content or status and refresh runtime FAQ source immediately."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        _, profile = await _load_hotel_profile(conn, hotel_id)
        normalized_faq, _ = _ensure_faq_integrity(profile.faq_data)
        target_index = next((index for index, item in enumerate(normalized_faq) if item.faq_id == faq_id), None)
        if target_index is None:
            raise HTTPException(status_code=404, detail="FAQ entry not found")
        existing = normalized_faq[target_index]
        updated_entry = _build_faq_entry(
            body,
            faq_id=existing.faq_id,
            created_at=existing.created_at,
            created_by=existing.created_by,
            updated_at=_now_iso(),
            updated_by=user.username,
            removed_at=existing.removed_at,
            removed_by=existing.removed_by,
            removed_reason=existing.removed_reason,
        )
        if updated_entry.status != FAQStatus.REMOVED:
            updated_entry.removed_at = None
            updated_entry.removed_by = None
            updated_entry.removed_reason = None
        normalized_faq[target_index] = updated_entry
        profile.faq_data = normalized_faq
        profile_name = await _persist_hotel_profile(conn, hotel_id, profile.model_dump(mode="json"))
    return {"status": "updated", "profile_path": profile_name, "item": _faq_to_payload(updated_entry)}


@router.post("/hotels/{hotel_id}/faq/{faq_id}/status")
async def update_hotel_faq_status(
    hotel_id: int,
    faq_id: str,
    body: FAQStatusUpdateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Change FAQ status without editing full content payload."""
    if body.status.value not in FAQ_MANAGE_STATUSES:
        raise HTTPException(status_code=400, detail="Use remove action for REMOVED status")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        _, profile = await _load_hotel_profile(conn, hotel_id)
        normalized_faq, _ = _ensure_faq_integrity(profile.faq_data)
        entry = next((item for item in normalized_faq if item.faq_id == faq_id), None)
        if entry is None:
            raise HTTPException(status_code=404, detail="FAQ entry not found")
        entry.status = body.status
        entry.updated_at = _now_iso()
        entry.updated_by = user.username
        entry.removed_at = None
        entry.removed_by = None
        entry.removed_reason = None
        profile.faq_data = normalized_faq
        profile_name = await _persist_hotel_profile(conn, hotel_id, profile.model_dump(mode="json"))
    return {"status": "updated", "profile_path": profile_name, "item": _faq_to_payload(entry)}


@router.delete("/hotels/{hotel_id}/faq/{faq_id}")
async def remove_hotel_faq_entry(
    hotel_id: int,
    faq_id: str,
    body: FAQRemoveRequest,
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Soft-remove FAQ entry so runtime stops using it immediately."""
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        _, profile = await _load_hotel_profile(conn, hotel_id)
        normalized_faq, _ = _ensure_faq_integrity(profile.faq_data)
        entry = next((item for item in normalized_faq if item.faq_id == faq_id), None)
        if entry is None:
            raise HTTPException(status_code=404, detail="FAQ entry not found")
        entry.status = FAQStatus.REMOVED
        entry.updated_at = _now_iso()
        entry.updated_by = user.username
        entry.removed_at = entry.updated_at
        entry.removed_by = user.username
        entry.removed_reason = body.reason.strip()
        profile.faq_data = normalized_faq
        profile_name = await _persist_hotel_profile(conn, hotel_id, profile.model_dump(mode="json"))
    return {"status": "removed", "profile_path": profile_name, "item": _faq_to_payload(entry)}


@router.post("/hotels/{hotel_id}/restaurant/slots")
async def create_restaurant_slots(
    hotel_id: int,
    slots: list[RestaurantSlotCreate],
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Create restaurant slots for one or more date ranges."""
    _ = user
    repository = RestaurantRepository()
    try:
        created_count = await repository.create_slots(hotel_id=hotel_id, slots=slots)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "created", "created_count": created_count}


@router.get("/hotels/{hotel_id}/restaurant/slots")
async def list_restaurant_slots(
    hotel_id: int,
    date_from: date,
    date_to: date,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """List restaurant slots with remaining capacity."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to must be >= date_from")

    repository = RestaurantRepository()
    slots = await repository.list_slots(hotel_id=hotel_id, date_from=date_from, date_to=date_to)
    return {"items": [slot.model_dump(mode="json") for slot in slots], "total": len(slots)}


@router.put("/hotels/{hotel_id}/restaurant/slots/{slot_id}")
async def update_restaurant_slot(
    hotel_id: int,
    slot_id: int,
    update: RestaurantSlotUpdate,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> dict[str, Any]:
    """Update restaurant slot capacity or active flag."""
    _ = user
    if update.total_capacity is None and update.is_active is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    repository = RestaurantRepository()
    try:
        row = await repository.update_slot(hotel_id=hotel_id, slot_id=slot_id, update=update)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Slot not found")
    return {"status": "updated", "slot": row}


@router.get("/hotels/{hotel_id}/transfers/holds")
async def list_transfer_holds(
    hotel_id: int,
    user: Annotated[TokenData, Depends(get_current_user)],
    date_from: date | None = Query(None),  # noqa: B008
    date_to: date | None = Query(None),  # noqa: B008
    status_filter: str | None = Query(None, alias="status"),
) -> dict[str, Any]:
    """List transfer holds with optional date and status filters."""
    check_permission(user, "holds:read")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")
    if date_from and date_to and date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to must be >= date_from")
    if status_filter and status_filter not in {status.value for status in HoldStatus}:
        raise HTTPException(status_code=400, detail="Invalid hold status")

    repository = TransferRepository()
    holds = await repository.list_holds(
        hotel_id=hotel_id,
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
    )
    return {"items": [hold.model_dump(mode="json") for hold in holds], "total": len(holds)}


@router.post("/hotels/{hotel_id}/transfers/holds/{hold_id}/approve")
async def approve_transfer_hold(
    hotel_id: int,
    hold_id: str,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Approve transfer hold through approval webhook flow."""
    check_permission(user, "holds:approve")
    if not hold_id.startswith("TR_HOLD_"):
        raise HTTPException(status_code=400, detail="Invalid transfer hold id")

    repository = TransferRepository()
    hold = await repository.get_hold(hold_id)
    if hold is None:
        raise HTTPException(status_code=404, detail="Transfer hold not found")
    if hold.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Transfer hold not found for hotel")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if hold.status != HoldStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=409, detail=f"Hold is not pending approval (current: {hold.status})")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        approval_request_id = await _ensure_approval_request(
            conn=conn,
            hotel_id=hotel_id,
            hold_id=hold_id,
            hold_type="transfer",
        )

    event_processor = getattr(request.app.state, "event_processor", None)
    if event_processor is None:
        raise HTTPException(status_code=503, detail="Event processor unavailable")
    event = ApprovalEvent(
        hotel_id=hotel_id,
        approval_request_id=approval_request_id,
        approved=True,
        approved_by_role=user.role.value,
        timestamp=datetime.now(UTC),
    )
    result = await event_processor.process_approval_event(event)
    return {"status": "approved", "hold_id": hold_id, "hold_type": "transfer", "result": result}


@router.post("/hotels/{hotel_id}/transfers/holds/{hold_id}/reject")
async def reject_transfer_hold(
    hotel_id: int,
    hold_id: str,
    body: RejectRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Reject transfer hold through approval webhook flow."""
    check_permission(user, "holds:reject")
    if not hold_id.startswith("TR_HOLD_"):
        raise HTTPException(status_code=400, detail="Invalid transfer hold id")

    repository = TransferRepository()
    hold = await repository.get_hold(hold_id)
    if hold is None:
        raise HTTPException(status_code=404, detail="Transfer hold not found")
    if hold.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Transfer hold not found for hotel")
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if hold.status != HoldStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=409, detail=f"Hold is not pending approval (current: {hold.status})")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        approval_request_id = await _ensure_approval_request(
            conn=conn,
            hotel_id=hotel_id,
            hold_id=hold_id,
            hold_type="transfer",
        )
        await _update_hold_rejection(conn, "transfer", hold_id, body.reason)

    event_processor = getattr(request.app.state, "event_processor", None)
    if event_processor is None:
        raise HTTPException(status_code=503, detail="Event processor unavailable")
    event = ApprovalEvent(
        hotel_id=hotel_id,
        approval_request_id=approval_request_id,
        approved=False,
        approved_by_role=user.role.value,
        timestamp=datetime.now(UTC),
    )
    result = await event_processor.process_approval_event(event)
    return {"status": "rejected", "hold_id": hold_id, "reason": body.reason, "result": result}


@router.get("/conversations")
async def list_conversations(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    active_only: bool = Query(False),
    date_from: date | None = Query(None),  # noqa: B008
    date_to: date | None = Query(None),  # noqa: B008
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List conversations with filters and pagination."""
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool
    effective_hotel_id = hotel_id if user.role == Role.ADMIN else user.hotel_id
    offset = (page - 1) * per_page

    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.id, c.hotel_id, c.phone_display, c.language,
                   COALESCE(NULLIF(c.current_state, ''), assistant_meta.last_state, 'GREETING') AS current_state,
                   COALESCE(NULLIF(c.current_intent, ''), assistant_meta.last_intent) AS current_intent,
                   c.risk_flags, c.is_active, c.last_message_at, c.created_at,
                   user_meta.last_user_internal_json,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            LEFT JOIN LATERAL (
                SELECT
                    m.internal_json->>'intent' AS last_intent,
                    m.internal_json->>'state' AS last_state
                FROM messages m
                WHERE m.conversation_id = c.id
                  AND m.role = 'assistant'
                ORDER BY m.created_at DESC
                LIMIT 1
            ) assistant_meta ON true
            LEFT JOIN LATERAL (
                SELECT m.internal_json AS last_user_internal_json
                FROM messages m
                WHERE m.conversation_id = c.id
                  AND m.role = 'user'
                ORDER BY m.created_at DESC
                LIMIT 1
            ) user_meta ON true
            WHERE ($1::int IS NULL OR c.hotel_id = $1)
              AND (
                    $2::text IS NULL
                    OR COALESCE(NULLIF(c.current_state, ''), assistant_meta.last_state, 'GREETING') = $2
                  )
              AND ($3::date IS NULL OR c.created_at::date >= $3)
              AND ($4::date IS NULL OR c.created_at::date <= $4)
              AND ($5::bool IS FALSE OR c.is_active = true)
            ORDER BY c.last_message_at DESC
            LIMIT $6 OFFSET $7
            """,
            effective_hotel_id,
            status_filter,
            date_from,
            date_to,
            active_only,
            per_page,
            offset,
        )
        total = int(
            await conn.fetchval(
                """
                SELECT COUNT(*) FROM conversations c
                WHERE ($1::int IS NULL OR c.hotel_id = $1)
                  AND (
                        $2::text IS NULL
                        OR COALESCE(
                            NULLIF(c.current_state, ''),
                            (
                                SELECT m.internal_json->>'state'
                                FROM messages m
                                WHERE m.conversation_id = c.id
                                  AND m.role = 'assistant'
                                ORDER BY m.created_at DESC
                                LIMIT 1
                            ),
                            'GREETING'
                        ) = $2
                      )
                  AND ($3::date IS NULL OR c.created_at::date >= $3)
                  AND ($4::date IS NULL OR c.created_at::date <= $4)
                  AND ($5::bool IS FALSE OR c.is_active = true)
                """,
                effective_hotel_id,
                status_filter,
                date_from,
                date_to,
                active_only,
            )
            or 0
        )

    return {
        "items": [_normalize_unified_hold_row(dict(row)) for row in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return conversation with full message history."""
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        conv = await conn.fetchrow(
            """
            SELECT
                c.*,
                COALESCE(NULLIF(c.current_state, ''), assistant_meta.last_state, 'GREETING') AS resolved_state,
                COALESCE(NULLIF(c.current_intent, ''), assistant_meta.last_intent) AS resolved_intent
            FROM conversations c
            LEFT JOIN LATERAL (
                SELECT
                    m.internal_json->>'intent' AS last_intent,
                    m.internal_json->>'state' AS last_state
                FROM messages m
                WHERE m.conversation_id = c.id
                  AND m.role = 'assistant'
                ORDER BY m.created_at DESC
                LIMIT 1
            ) assistant_meta ON true
            WHERE c.id = $1
            """,
            conversation_id,
        )
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if user.role != Role.ADMIN and int(conv["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")
        messages = await conn.fetch(
            """
            SELECT id, role, content, internal_json, tool_calls, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            """,
            conversation_id,
        )
    conversation_payload = dict(conv)
    resolved_state = conversation_payload.get("resolved_state")
    resolved_intent = conversation_payload.get("resolved_intent")
    if resolved_state:
        conversation_payload["current_state"] = resolved_state
    if resolved_intent:
        conversation_payload["current_intent"] = resolved_intent
    conversation_payload.pop("resolved_state", None)
    conversation_payload.pop("resolved_intent", None)
    return {"conversation": conversation_payload, "messages": [dict(row) for row in messages]}


@router.post("/conversations/{conversation_id}/reset")
async def reset_conversation(
    conversation_id: UUID,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Close a conversation so the next message starts a fresh session."""
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, hotel_id, is_active FROM conversations WHERE id = $1",
            conversation_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user.role != Role.ADMIN and int(row["hotel_id"]) != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not row["is_active"]:
        return {"status": "already_closed", "conversation_id": str(conversation_id)}

    repository = ConversationRepository()
    await repository.close(conversation_id)
    return {"status": "reset", "conversation_id": str(conversation_id)}


@router.post("/conversations/{conversation_id}/messages/{message_id}/send")
async def approve_and_send_message(
    conversation_id: UUID,
    message_id: UUID,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Approve a pending assistant message and send it via WhatsApp."""
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        conv_row = await conn.fetchrow(
            "SELECT id, hotel_id, phone_display FROM conversations WHERE id = $1",
            conversation_id,
        )
        if conv_row is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if user.role != Role.ADMIN and int(conv_row["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")

        msg_row = await conn.fetchrow(
            "SELECT id, role, content, internal_json FROM messages WHERE id = $1 AND conversation_id = $2",
            message_id,
            conversation_id,
        )
        if msg_row is None:
            raise HTTPException(status_code=404, detail="Message not found")
        if msg_row["role"] != "assistant":
            raise HTTPException(status_code=400, detail="Only assistant messages can be sent")

        user_phone_row = await conn.fetchrow(
            """
            SELECT internal_json FROM messages
            WHERE conversation_id = $1 AND role = 'user'
            ORDER BY created_at DESC LIMIT 1
            """,
            conversation_id,
        )

    def _pj(raw: Any) -> dict[str, Any]:
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (str, bytes, bytearray)):
            try:
                v = orjson.loads(raw)
                return v if isinstance(v, dict) else {}
            except Exception:
                return {}
        return {}

    internal = _pj(msg_row["internal_json"])
    if not internal.get("send_blocked") and not internal.get("approval_pending"):
        return {"status": "already_sent", "message_id": str(message_id)}

    phone = str(conv_row["phone_display"] or "")
    if not phone or "*" in phone:
        user_internal = _pj(user_phone_row["internal_json"] if user_phone_row else None)
        wa_id = user_internal.get("wa_id") or ""
        if wa_id:
            phone = wa_id
    if not phone or "*" in phone:
        raise HTTPException(
            status_code=400,
            detail="Bu konusma icin gercek telefon numarasi bulunamadi.",
        )

    whatsapp_client = get_whatsapp_client()
    try:
        send_result = await whatsapp_client.send_text_message(to=phone, body=str(msg_row["content"]), force=True)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"WhatsApp gonderilemedi: {exc}") from exc

    whatsapp_message_id: str | None = None
    if isinstance(send_result, dict):
        messages = send_result.get("messages")
        if isinstance(messages, list) and messages:
            first = messages[0]
            if isinstance(first, dict):
                whatsapp_message_id = str(first.get("id", "")).strip() or None

    internal["send_blocked"] = False
    internal["approval_pending"] = False
    internal["approved_by"] = user.username
    if whatsapp_message_id:
        internal["whatsapp_message_id"] = whatsapp_message_id
    async with db.acquire() as conn:
        await conn.execute(
            """
            UPDATE messages
            SET internal_json = $1,
                whatsapp_message_id = COALESCE($2, whatsapp_message_id)
            WHERE id = $3
            """,
            orjson.dumps(internal).decode(),
            whatsapp_message_id,
            message_id,
        )

    return {"status": "sent", "message_id": str(message_id), "conversation_id": str(conversation_id)}


@router.post("/conversations/{conversation_id}/human-override")
async def toggle_human_override(
    conversation_id: UUID,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    enable: bool = Query(..., description="true = insan devri, false = AI modu"),
) -> dict[str, Any]:
    """Toggle human override for a conversation.

    When enabled, inbound guest messages are recorded but the AI no longer
    generates or sends conversational replies. Reservation/result notifications
    coming from separate system event flows may still be sent.
    """
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, hotel_id, phone_hash, is_active FROM conversations WHERE id = $1",
            conversation_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user.role != Role.ADMIN and int(row["hotel_id"]) != user.hotel_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not row["is_active"]:
        raise HTTPException(status_code=400, detail="Kapali konusmalarda insan devri ayarlanamaz.")

    repository = ConversationRepository()
    await repository.set_human_override(conversation_id, enable)

    # Sync to Redis for fast webhook-level lookup
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is not None:
        redis_key = f"velox:human_override:{row['phone_hash']}"
        try:
            if enable:
                await redis_client.set(redis_key, "1")
            else:
                await redis_client.delete(redis_key)
        except Exception:
            pass  # Best-effort; DB is the source of truth

    import structlog
    structlog.get_logger(__name__).info(
        "human_override_toggled",
        conversation_id=str(conversation_id),
        enabled=enable,
        toggled_by=user.username,
    )
    return {
        "status": "human_override_enabled" if enable else "human_override_disabled",
        "conversation_id": str(conversation_id),
        "human_override": enable,
    }


@router.post("/conversations/reset-by-phone")
async def reset_conversation_by_phone(
    request: Request,
    user: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
    phone: str = Query(..., description="Phone number (e.g. 905xxxxxxxxx)"),
    hotel_id: int | None = Query(None),
) -> dict[str, Any]:
    """Close all active conversations for a phone number to start fresh tests."""
    _ = user
    effective_hotel_id = hotel_id or settings.elektra_hotel_id
    phone_hash = hash_phone(phone)

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id FROM conversations
            WHERE hotel_id = $1 AND phone_hash = $2 AND is_active = true
            """,
            effective_hotel_id,
            phone_hash,
        )
    if not rows:
        return {"status": "no_active_conversations", "phone": phone}

    repository = ConversationRepository()
    closed_ids = []
    for row in rows:
        await repository.close(row["id"])
        closed_ids.append(str(row["id"]))

    return {
        "status": "reset",
        "phone": phone,
        "closed_count": len(closed_ids),
        "closed_conversation_ids": closed_ids,
    }


@router.get("/holds")
async def list_holds(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    hold_type: str | None = Query(None, description="stay, restaurant, or transfer"),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List holds in unified view, filterable by type and status."""
    check_permission(user, "holds:read")
    if hold_type and hold_type not in ALLOWED_HOLD_TYPES:
        raise HTTPException(status_code=400, detail="hold_type must be one of: stay, restaurant, transfer")
    if status_filter and status_filter not in {status.value for status in HoldStatus}:
        raise HTTPException(status_code=400, detail="Invalid hold status")

    db = request.app.state.db_pool
    effective_hotel_id = hotel_id if user.role == Role.ADMIN else user.hotel_id
    offset = (page - 1) * per_page
    queries = _build_unified_hold_queries(hold_type=hold_type, include_stay_workflow=True)

    async with db.acquire() as conn:
        try:
            rows = await conn.fetch(
                queries.items_query,
                effective_hotel_id,
                status_filter,
                per_page,
                offset,
            )
            total = int(
                await conn.fetchval(
                    queries.count_query,
                    effective_hotel_id,
                    status_filter,
                )
                or 0
            )
        except asyncpg.UndefinedColumnError:
            legacy_queries = _build_unified_hold_queries(hold_type=hold_type, include_stay_workflow=False)
            rows = await conn.fetch(
                legacy_queries.items_query,
                effective_hotel_id,
                status_filter,
                per_page,
                offset,
            )
            total = int(
                await conn.fetchval(
                    legacy_queries.count_query,
                    effective_hotel_id,
                    status_filter,
                )
                or 0
            )

    return {
        "items": [_normalize_unified_hold_row(dict(row)) for row in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


class _UnifiedHoldQueries(BaseModel):
    items_query: str
    count_query: str


def _normalize_unified_hold_row(row: dict[str, Any]) -> dict[str, Any]:
    """Decode JSON fields returned as strings by asyncpg union queries."""
    normalized = dict(row)
    normalized["draft_json"] = decode_json_object(normalized.get("draft_json"))
    return normalized


def _build_unified_hold_queries(*, hold_type: str | None, include_stay_workflow: bool) -> _UnifiedHoldQueries:
    """Return SQL queries for paginated unified hold listing."""
    stay_select = (
        """
        SELECT sh.hold_id, 'stay' AS type, sh.hotel_id, sh.status,
               sh.workflow_state, sh.draft_json::jsonb AS draft_json, sh.expires_at,
               sh.pms_create_started_at, sh.pms_create_completed_at, sh.manual_review_reason,
               sh.approval_idempotency_key, sh.create_idempotency_key,
               sh.pms_reservation_id, sh.voucher_no, sh.approved_by, sh.approved_at,
               approval_meta.approval_decided_at, payment_meta.payment_requested_at,
               failure_meta.last_failed_tool, failure_meta.last_failed_error_type,
               sh.created_at, sh.conversation_id
        FROM stay_holds sh
        LEFT JOIN LATERAL (
            SELECT ar.decided_at AS approval_decided_at
            FROM approval_requests ar
            WHERE ar.hotel_id = sh.hotel_id
              AND ar.reference_id = sh.hold_id
              AND ar.approval_type = 'STAY'
            ORDER BY ar.created_at DESC
            LIMIT 1
        ) AS approval_meta ON true
        LEFT JOIN LATERAL (
            SELECT pr.created_at AS payment_requested_at
            FROM payment_requests pr
            WHERE pr.hotel_id = sh.hotel_id
              AND (pr.reference_id = sh.pms_reservation_id OR pr.reference_id = sh.hold_id)
            ORDER BY pr.created_at DESC
            LIMIT 1
        ) AS payment_meta ON true
        LEFT JOIN LATERAL (
            SELECT
                CASE
                    WHEN msg.internal_json->'tool_results'->'booking_get_reservation'->>'success' = 'false'
                        THEN 'booking_get_reservation'
                    WHEN msg.internal_json->'tool_results'->'booking_create_reservation'->>'success' = 'false'
                        THEN 'booking_create_reservation'
                    WHEN msg.internal_json->'tool_results'->'payment_request_prepayment'->>'success' = 'false'
                        THEN 'payment_request_prepayment'
                    ELSE NULL
                END AS last_failed_tool,
                COALESCE(
                    msg.internal_json->'tool_results'->'booking_get_reservation'->>'error_type',
                    msg.internal_json->'tool_results'->'booking_create_reservation'->>'error_type',
                    msg.internal_json->'tool_results'->'payment_request_prepayment'->>'error_type'
                ) AS last_failed_error_type
            FROM messages msg
            WHERE msg.conversation_id = sh.conversation_id
              AND msg.role = 'system'
              AND msg.internal_json->>'event_type' = 'approval.updated'
            ORDER BY msg.created_at DESC
            LIMIT 1
        ) AS failure_meta ON true
        WHERE ($1::int IS NULL OR sh.hotel_id = $1) AND ($2::text IS NULL OR sh.status = $2)
        """
        if include_stay_workflow
        else """
        SELECT sh.hold_id, 'stay' AS type, sh.hotel_id, sh.status,
               NULL::text AS workflow_state, sh.draft_json::jsonb AS draft_json, NULL::timestamptz AS expires_at,
                NULL::timestamptz AS pms_create_started_at, NULL::timestamptz AS pms_create_completed_at,
                NULL::text AS manual_review_reason, NULL::text AS approval_idempotency_key,
               NULL::text AS create_idempotency_key, sh.pms_reservation_id, sh.voucher_no,
               sh.approved_by, sh.approved_at,
               approval_meta.approval_decided_at, payment_meta.payment_requested_at,
               failure_meta.last_failed_tool, failure_meta.last_failed_error_type,
               sh.created_at, sh.conversation_id
        FROM stay_holds sh
        LEFT JOIN LATERAL (
            SELECT ar.decided_at AS approval_decided_at
            FROM approval_requests ar
            WHERE ar.hotel_id = sh.hotel_id
              AND ar.reference_id = sh.hold_id
              AND ar.approval_type = 'STAY'
            ORDER BY ar.created_at DESC
            LIMIT 1
        ) AS approval_meta ON true
        LEFT JOIN LATERAL (
            SELECT pr.created_at AS payment_requested_at
            FROM payment_requests pr
            WHERE pr.hotel_id = sh.hotel_id
              AND (pr.reference_id = sh.pms_reservation_id OR pr.reference_id = sh.hold_id)
            ORDER BY pr.created_at DESC
            LIMIT 1
        ) AS payment_meta ON true
        LEFT JOIN LATERAL (
            SELECT
                CASE
                    WHEN msg.internal_json->'tool_results'->'booking_get_reservation'->>'success' = 'false'
                        THEN 'booking_get_reservation'
                    WHEN msg.internal_json->'tool_results'->'booking_create_reservation'->>'success' = 'false'
                        THEN 'booking_create_reservation'
                    WHEN msg.internal_json->'tool_results'->'payment_request_prepayment'->>'success' = 'false'
                        THEN 'payment_request_prepayment'
                    ELSE NULL
                END AS last_failed_tool,
                COALESCE(
                    msg.internal_json->'tool_results'->'booking_get_reservation'->>'error_type',
                    msg.internal_json->'tool_results'->'booking_create_reservation'->>'error_type',
                    msg.internal_json->'tool_results'->'payment_request_prepayment'->>'error_type'
                ) AS last_failed_error_type
            FROM messages msg
            WHERE msg.conversation_id = sh.conversation_id
              AND msg.role = 'system'
              AND msg.internal_json->>'event_type' = 'approval.updated'
            ORDER BY msg.created_at DESC
            LIMIT 1
        ) AS failure_meta ON true
        WHERE ($1::int IS NULL OR sh.hotel_id = $1) AND ($2::text IS NULL OR sh.status = $2)
        """
    )
    restaurant_select = """
        SELECT hold_id, 'restaurant' AS type, hotel_id, status,
               NULL::text AS workflow_state,
               jsonb_build_object(
                   'date', date,
                   'time', time,
                   'party_size', party_size,
                   'guest_name', guest_name,
                   'area', area
               ) AS draft_json,
                NULL::timestamptz AS expires_at, NULL::timestamptz AS pms_create_started_at,
                NULL::timestamptz AS pms_create_completed_at, NULL::text AS manual_review_reason,
                NULL::text AS approval_idempotency_key, NULL::text AS create_idempotency_key,
               NULL::text AS pms_reservation_id, NULL::text AS voucher_no, approved_by, approved_at,
               NULL::timestamptz AS approval_decided_at, NULL::timestamptz AS payment_requested_at,
               NULL::text AS last_failed_tool, NULL::text AS last_failed_error_type,
               created_at, conversation_id
        FROM restaurant_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
    """
    transfer_select = """
        SELECT hold_id, 'transfer' AS type, hotel_id, status,
               NULL::text AS workflow_state,
               jsonb_build_object(
                   'route', route,
                   'date', date,
                   'time', time,
                   'pax_count', pax_count,
                   'guest_name', guest_name,
                   'price_eur', price_eur
               ) AS draft_json,
                NULL::timestamptz AS expires_at, NULL::timestamptz AS pms_create_started_at,
                NULL::timestamptz AS pms_create_completed_at, NULL::text AS manual_review_reason,
                NULL::text AS approval_idempotency_key, NULL::text AS create_idempotency_key,
               NULL::text AS pms_reservation_id, NULL::text AS voucher_no, approved_by, approved_at,
               NULL::timestamptz AS approval_decided_at, NULL::timestamptz AS payment_requested_at,
               NULL::text AS last_failed_tool, NULL::text AS last_failed_error_type,
               created_at, conversation_id
        FROM transfer_holds
        WHERE ($1::int IS NULL OR hotel_id = $1) AND ($2::text IS NULL OR status = $2)
    """

    parts: list[str] = []
    if hold_type in (None, "stay"):
        parts.append(stay_select.strip())
    if hold_type in (None, "restaurant"):
        parts.append(restaurant_select.strip())
    if hold_type in (None, "transfer"):
        parts.append(transfer_select.strip())

    union_sql = "\nUNION ALL\n".join(parts)
    return _UnifiedHoldQueries(
        items_query=(
            "WITH unified_holds AS (\n"
            f"{union_sql}\n"
            ")\n"
            "SELECT * FROM unified_holds\n"
            "ORDER BY created_at DESC\n"
            "LIMIT $3 OFFSET $4"
        ),
        count_query=(
            "WITH unified_holds AS (\n"
            f"{union_sql}\n"
            ")\n"
            "SELECT COUNT(*) FROM unified_holds"
        ),
    )


def _resolve_hold_target(hold_id: str) -> tuple[str, str]:
    """Resolve table/type by hold id prefix."""
    for prefix, target in HOLD_TABLES.items():
        if hold_id.startswith(prefix):
            return target
    raise HTTPException(status_code=400, detail="Unknown hold_id prefix")


@router.post("/holds/{hold_id}/approve")
async def approve_hold(
    hold_id: str,
    body: ApproveRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Approve hold and trigger approval/retry webhook flow inside backend."""
    _ = body
    check_permission(user, "holds:approve")
    _table, hold_type = _resolve_hold_target(hold_id)
    db = request.app.state.db_pool
    effective_hotel_id: int
    approval_request_id: str

    async with db.acquire() as conn:
        row = await _fetch_hold_row(conn, hold_type, hold_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Hold not found")
        current_status = str(row["status"])
        allowed_statuses = (
            {
                HoldStatus.PENDING_APPROVAL.value,
                HoldStatus.APPROVED.value,
                HoldStatus.MANUAL_REVIEW.value,
                HoldStatus.PMS_FAILED.value,
            }
            if hold_type == "stay"
            else {HoldStatus.PENDING_APPROVAL.value}
        )
        if current_status not in allowed_statuses:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Hold cannot be approved/retried in current status "
                    f"(current: {current_status})"
                ),
            )
        if hold_type == "stay" and current_status == HoldStatus.MANUAL_REVIEW.value:
            manual_review_reason = str(row.get("manual_review_reason") or "")
            create_was_uncertain = manual_review_reason in {
                "create_missing_identifiers",
                "create_unverified_after_readback",
            }
            if row.get("pms_reservation_id") or row.get("voucher_no") or create_was_uncertain:
                raise HTTPException(
                    status_code=409,
                    detail="Stay hold already reached an uncertain PMS create state; manual review is required instead of retry.",
                )
        if user.role != Role.ADMIN and int(row["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")
        effective_hotel_id = int(row["hotel_id"])
        approval_request_id = await _ensure_approval_request(
            conn=conn,
            hotel_id=effective_hotel_id,
            hold_id=hold_id,
            hold_type=hold_type,
        )

    event_processor = getattr(request.app.state, "event_processor", None)
    if event_processor is None:
        raise HTTPException(status_code=503, detail="Event processor unavailable")

    event = ApprovalEvent(
        hotel_id=effective_hotel_id,
        approval_request_id=approval_request_id,
        approved=True,
        approved_by_role=user.role.value,
        timestamp=datetime.now(UTC),
    )
    result = await event_processor.process_approval_event(event)
    return {"status": "approved", "hold_id": hold_id, "hold_type": hold_type, "result": result}


@router.post("/holds/{hold_id}/reject")
async def reject_hold(
    hold_id: str,
    body: RejectRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Reject hold and trigger approval webhook flow inside backend."""
    check_permission(user, "holds:reject")
    _table, hold_type = _resolve_hold_target(hold_id)
    db = request.app.state.db_pool
    effective_hotel_id: int
    approval_request_id: str

    async with db.acquire() as conn:
        row = await _fetch_hold_row(conn, hold_type, hold_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Hold not found")
        if row["status"] != HoldStatus.PENDING_APPROVAL:
            raise HTTPException(status_code=409, detail=f"Hold is not pending approval (current: {row['status']})")
        if user.role != Role.ADMIN and int(row["hotel_id"]) != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")
        effective_hotel_id = int(row["hotel_id"])
        approval_request_id = await _ensure_approval_request(
            conn=conn,
            hotel_id=effective_hotel_id,
            hold_id=hold_id,
            hold_type=hold_type,
        )
        # Rejection reason should still be persisted on hold row.
        await _update_hold_rejection(conn, hold_type, hold_id, body.reason)

    event_processor = getattr(request.app.state, "event_processor", None)
    if event_processor is None:
        raise HTTPException(status_code=503, detail="Event processor unavailable")

    event = ApprovalEvent(
        hotel_id=effective_hotel_id,
        approval_request_id=approval_request_id,
        approved=False,
        approved_by_role=user.role.value,
        timestamp=datetime.now(UTC),
    )
    result = await event_processor.process_approval_event(event)
    return {"status": "rejected", "hold_id": hold_id, "reason": body.reason, "result": result}


@router.get("/tickets")
async def list_tickets(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List tickets with role-based visibility and filters."""
    check_permission(user, "tickets:read")
    if status_filter and status_filter not in ALLOWED_TICKET_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid ticket status")
    if priority and priority not in ALLOWED_TICKET_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid ticket priority")
    db = request.app.state.db_pool
    effective_hotel_id = hotel_id if user.role == Role.ADMIN else user.hotel_id
    assigned_role = None if user.role == Role.ADMIN else user.role.value
    offset = (page - 1) * per_page

    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ticket_id, hotel_id, conversation_id, reason, transcript_summary,
                   priority, dedupe_key, status, assigned_to_role, assigned_to_name,
                   resolved_at, created_at
            FROM tickets
            WHERE ($1::int IS NULL OR hotel_id = $1)
              AND ($2::text IS NULL OR assigned_to_role = $2)
              AND ($3::text IS NULL OR status = $3)
              AND ($4::text IS NULL OR priority = $4)
            ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, created_at DESC
            LIMIT $5 OFFSET $6
            """,
            effective_hotel_id,
            assigned_role,
            status_filter,
            priority,
            per_page,
            offset,
        )
        total = int(
            await conn.fetchval(
                """
                SELECT COUNT(*) FROM tickets
                WHERE ($1::int IS NULL OR hotel_id = $1)
                  AND ($2::text IS NULL OR assigned_to_role = $2)
                  AND ($3::text IS NULL OR status = $3)
                  AND ($4::text IS NULL OR priority = $4)
                """,
                effective_hotel_id,
                assigned_role,
                status_filter,
                priority,
            )
            or 0
        )
    return {"items": [dict(row) for row in rows], "total": total, "page": page, "per_page": per_page}


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update ticket status and assignment."""
    check_permission(user, "tickets:write")
    if body.status and body.status not in ALLOWED_TICKET_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid ticket status")
    if body.assigned_to_role and body.assigned_to_role not in {role.value for role in Role if role != Role.NONE}:
        raise HTTPException(status_code=400, detail="Invalid role")
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_id = $1", ticket_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if user.role != Role.ADMIN:
            if int(row["hotel_id"]) != user.hotel_id:
                raise HTTPException(status_code=403, detail="Access denied")
            if row["assigned_to_role"] != user.role.value:
                raise HTTPException(status_code=403, detail="Ticket not assigned to your role")

        if not any([body.status, body.assigned_to_role, body.assigned_to_name]):
            raise HTTPException(status_code=400, detail="No fields to update")

        await conn.execute(
            """
            UPDATE tickets
            SET status = COALESCE($1, status),
                assigned_to_role = COALESCE($2, assigned_to_role),
                assigned_to_name = COALESCE($3, assigned_to_name),
                resolved_at = CASE
                    WHEN COALESCE($1, status) IN ('RESOLVED', 'CLOSED') THEN COALESCE(resolved_at, now())
                    ELSE resolved_at
                END,
                updated_at = now()
            WHERE ticket_id = $4
            """,
            body.status,
            body.assigned_to_role,
            body.assigned_to_name,
            ticket_id,
        )
    return {"status": "updated", "ticket_id": ticket_id}


async def _fetch_hold_row(conn: Any, hold_type: str, hold_id: str) -> Any:
    """Fetch one hold row by normalized hold type."""
    if hold_type == "stay":
        return await conn.fetchrow("SELECT * FROM stay_holds WHERE hold_id = $1", hold_id)
    if hold_type == "restaurant":
        return await conn.fetchrow("SELECT * FROM restaurant_holds WHERE hold_id = $1", hold_id)
    return await conn.fetchrow("SELECT * FROM transfer_holds WHERE hold_id = $1", hold_id)


async def _ensure_approval_request(conn: Any, hotel_id: int, hold_id: str, hold_type: str) -> str:
    """Load active approval request id or create a fallback one if missing."""
    approval_type = hold_type.upper()
    row = await conn.fetchrow(
        """
        SELECT request_id
        FROM approval_requests
        WHERE hotel_id = $1 AND reference_id = $2 AND approval_type = $3
        ORDER BY created_at DESC
        LIMIT 1
        """,
        hotel_id,
        hold_id,
        approval_type,
    )
    if row is not None:
        return str(row["request_id"])

    request_id = await next_sequential_id("APR_", "approval_requests", "request_id")
    details_summary = f"{approval_type} hold approval requested from admin panel: {hold_id}"
    await conn.execute(
        """
        INSERT INTO approval_requests (
            request_id, hotel_id, approval_type, reference_id, details_summary, required_roles, any_of, status
        )
        VALUES ($1, $2, $3, $4, $5, $6, false, 'REQUESTED')
        """,
        request_id,
        hotel_id,
        approval_type,
        hold_id,
        details_summary,
        ["ADMIN"],
    )
    return request_id


async def _update_hold_approval(conn: Any, hold_type: str, hold_id: str, username: str) -> None:
    """Approve one hold row using a static query per hold type."""
    if hold_type == "stay":
        await conn.execute(
            """
            UPDATE stay_holds
            SET status = $1, approved_by = $2, approved_at = now(), updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.APPROVED.value,
            username,
            hold_id,
        )
        return
    if hold_type == "restaurant":
        await conn.execute(
            """
            UPDATE restaurant_holds
            SET status = $1, approved_by = $2, approved_at = now(), updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.APPROVED.value,
            username,
            hold_id,
        )
        return
    await conn.execute(
        """
        UPDATE transfer_holds
        SET status = $1, approved_by = $2, approved_at = now(), updated_at = now()
        WHERE hold_id = $3
        """,
        HoldStatus.APPROVED.value,
        username,
        hold_id,
    )


async def _update_hold_rejection(conn: Any, hold_type: str, hold_id: str, reason: str) -> None:
    """Reject one hold row using a static query per hold type."""
    if hold_type == "stay":
        await conn.execute(
            """
            UPDATE stay_holds
            SET status = $1, rejected_reason = $2, updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.REJECTED.value,
            reason,
            hold_id,
        )
        return
    if hold_type == "restaurant":
        await conn.execute(
            """
            UPDATE restaurant_holds
            SET status = $1, rejected_reason = $2, updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.REJECTED.value,
            reason,
            hold_id,
        )
        return
    await conn.execute(
        """
        UPDATE transfer_holds
        SET status = $1, rejected_reason = $2, updated_at = now()
        WHERE hold_id = $3
        """,
        HoldStatus.REJECTED.value,
        reason,
        hold_id,
    )


# ---------------------------------------------------------------------------
# Notification phones management
# ---------------------------------------------------------------------------

_notification_phone_repo = NotificationPhoneRepository()


class NotificationPhoneAdd(BaseModel):
    phone: str
    label: str = ""

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        cleaned = "".join(c for c in value.strip() if c.isdigit() or c == "+")
        if cleaned.startswith("00"):
            cleaned = f"+{cleaned[2:]}"
        if cleaned and not cleaned.startswith("+"):
            cleaned = f"+{cleaned}"
        digit_count = len(cleaned.replace("+", ""))
        if digit_count < 10 or digit_count > 15:
            raise ValueError("Telefon numarasi 10-15 rakam icermelidir.")
        return cleaned


@router.get("/notification-phones")
async def list_notification_phones(
    user: Annotated[TokenData, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    """List active notification phones for the hotel."""
    check_permission(user, "notification_phones:read")
    try:
        return await _notification_phone_repo.list_active(user.hotel_id)
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=503,
            detail="notification_phones tablosu bulunamadi. Migration 004 uygulanmali.",
        ) from exc


@router.post("/notification-phones", status_code=201)
async def add_notification_phone(
    body: NotificationPhoneAdd,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, Any]:
    """Add a notification phone number."""
    check_permission(user, "notification_phones:write")
    try:
        return await _notification_phone_repo.add(user.hotel_id, body.phone, body.label)
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=503,
            detail="notification_phones tablosu bulunamadi. Migration 004 uygulanmali.",
        ) from exc


@router.delete("/notification-phones/{phone}")
async def remove_notification_phone(
    phone: str,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, str]:
    """Remove a notification phone. Default admin phone cannot be removed."""
    check_permission(user, "notification_phones:write")
    decoded_phone = phone.replace("_", "+")
    try:
        removed = await _notification_phone_repo.remove(user.hotel_id, decoded_phone)
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=503,
            detail="notification_phones tablosu bulunamadi. Migration 004 uygulanmali.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not removed:
        raise HTTPException(status_code=404, detail="Numara bulunamadi.")
    return {"status": "removed", "phone": decoded_phone}
