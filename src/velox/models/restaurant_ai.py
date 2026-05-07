"""Restaurant AI menu assistant models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MenuItemStatus = Literal["active", "passive", "pending_approval"]
ManualMenuStatus = Literal["catalog_verified", "approval_required", "rejected"]
OrderConfirmationStatus = Literal[
    "draft",
    "customer_confirmed_once",
    "customer_confirmed_twice",
    "sent_to_staff",
    "pending_staff_approval",
    "accepted_by_staff",
    "rejected_by_staff",
    "preparing",
    "completed",
    "cancelled",
    "pending_confirmation",
    "confirmed",
    "sent_to_waiter",
    "failed",
]
WhatsAppSendStatus = Literal["not_sent", "sent", "failed", "partial"]
RestaurantPublicOrderServiceType = Literal["table_service", "room_service"]
RestaurantPublicOrderMealPeriod = Literal["breakfast", "lunch", "dinner"]


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class RestaurantAiMenuItem(BaseModel):
    """Single menu catalog row used by the restaurant assistant."""

    model_config = ConfigDict(str_strip_whitespace=True)

    menu_item_id: str
    venue: str
    menu_type: str
    category: str
    name_en: str
    name_tr: str | None = None
    price_try: Decimal | None = Field(default=None, ge=0)
    description_en: str | None = None
    description_tr: str | None = None
    tags: list[str] = Field(default_factory=list)
    dietary_tags: list[str] = Field(default_factory=list)
    allergen_tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    source_pdf: str | None = None
    source_page: int | None = Field(default=None, ge=1)
    status: MenuItemStatus = "active"
    manual_status: ManualMenuStatus = "catalog_verified"
    notes: str | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("menu_item_id", "venue", "menu_type", "category", "name_en")
    @classmethod
    def _required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Bu alan boş olamaz.")
        return stripped

    @field_validator("name_tr", "description_en", "description_tr", "source_pdf", "notes")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantAiManualMenuItemCreate(BaseModel):
    """Panel request for manual menu item proposals.

    Manual proposals are intentionally not active catalog items. They enter the
    system as approval-required records so production answers stay bound to the
    imported catalog.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    hotel_id: int = Field(ge=1)
    venue: str
    menu_type: str
    category: str
    name_en: str
    name_tr: str | None = None
    price_try: Decimal | None = Field(default=None, ge=0)
    description_en: str | None = None
    description_tr: str | None = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("venue", "menu_type", "category", "name_en")
    @classmethod
    def _required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Bu alan boş olamaz.")
        return stripped

    @field_validator("name_tr", "description_en", "description_tr", "notes")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantAiMenuItemContentUpdate(BaseModel):
    """Editable customer-facing content for a catalog item."""

    model_config = ConfigDict(str_strip_whitespace=True)

    description_en: str | None = Field(default=None, max_length=1000)
    description_tr: str | None = Field(default=None, max_length=1000)
    ingredients: list[str] | None = Field(default=None, max_length=80)

    @field_validator("description_en", "description_tr")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @field_validator("ingredients")
    @classmethod
    def _ingredients(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [item.strip() for item in value if item.strip()]


class RestaurantAiWaiterCreate(BaseModel):
    """Waiter WhatsApp routing create request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    hotel_id: int = Field(ge=1)
    waiter_name: str = Field(min_length=2, max_length=120)
    whatsapp_number: str = Field(min_length=8, max_length=32)
    role: str | None = Field(default=None, max_length=80)
    venue: str | None = Field(default=None, max_length=120)
    active: bool = True
    receives_order_notifications: bool = True

    @field_validator("whatsapp_number")
    @classmethod
    def _phone_shape(cls, value: str) -> str:
        normalized = value.replace(" ", "").replace("-", "")
        if not normalized.startswith("+") or not normalized[1:].isdigit():
            raise ValueError("WhatsApp numarası +905XXXXXXXXX formatında olmalı.")
        return normalized

    @field_validator("role", "venue")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantAiWaiterUpdate(BaseModel):
    """Waiter WhatsApp routing update request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    waiter_name: str | None = Field(default=None, min_length=2, max_length=120)
    whatsapp_number: str | None = Field(default=None, min_length=8, max_length=32)
    role: str | None = Field(default=None, max_length=80)
    venue: str | None = Field(default=None, max_length=120)
    active: bool | None = None
    receives_order_notifications: bool | None = None

    @field_validator("whatsapp_number")
    @classmethod
    def _phone_shape(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.replace(" ", "").replace("-", "")
        if not normalized.startswith("+") or not normalized[1:].isdigit():
            raise ValueError("WhatsApp numarası +905XXXXXXXXX formatında olmalı.")
        return normalized

    @field_validator("role", "venue")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantAiOrderStatusUpdate(BaseModel):
    """Order log status update from the panel."""

    confirmation_status: OrderConfirmationStatus | None = None
    whatsapp_send_status: WhatsAppSendStatus | None = None


class RestaurantAiMenuItemStatusUpdate(BaseModel):
    """Catalog item status update from the panel."""

    status: MenuItemStatus


class RestaurantAiTableLinkRequest(BaseModel):
    """Admin request for generating one public table ordering link."""

    hotel_id: int = Field(ge=1)
    venue: str = Field(min_length=2, max_length=120)
    table_no: str = Field(min_length=1, max_length=40)

    @field_validator("venue", "table_no")
    @classmethod
    def _required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Bu alan boş olamaz.")
        return stripped


class RestaurantOffMenuRequestCreate(BaseModel):
    """Off-menu request log create request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    hotel_id: int = Field(ge=1)
    requested_text: str = Field(min_length=2, max_length=240)
    detected_intent: str | None = Field(default=None, max_length=80)
    venue: str | None = Field(default=None, max_length=120)
    guest_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("detected_intent", "venue")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantAiMessageSettingsUpdate(BaseModel):
    """Editable message templates for Restaurant AI.

    The menu-out-of-scope guard is not included by design; it is always enabled.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    off_menu_response: str = Field(min_length=20, max_length=1200)
    order_confirmation_message: str = Field(min_length=20, max_length=1200)
    whatsapp_notification_template: str = Field(min_length=20, max_length=2500)
    allergy_warning_text: str = Field(min_length=20, max_length=1200)


class RestaurantAiTestConsoleRequest(BaseModel):
    """Restaurant AI deterministic panel test request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    hotel_id: int = Field(ge=1)
    question: str = Field(min_length=2, max_length=1000)
    venue: str | None = Field(default=None, max_length=120)
    menu_type: str | None = Field(default=None, max_length=80)

    @field_validator("venue", "menu_type")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantPublicOrderItem(BaseModel):
    """One customer-selected item in the public ordering panel."""

    model_config = ConfigDict(str_strip_whitespace=True)

    menu_item_id: str = Field(min_length=1, max_length=180)
    quantity: int = Field(ge=1, le=20)
    note: str | None = Field(default=None, max_length=240)

    @field_validator("note")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class RestaurantPublicOrderCreate(BaseModel):
    """Public customer order request after two customer confirmations."""

    model_config = ConfigDict(str_strip_whitespace=True)

    token: str = Field(min_length=20, max_length=2000)
    language_code: str = Field(min_length=2, max_length=12)
    meal_period: RestaurantPublicOrderMealPeriod
    service_type: RestaurantPublicOrderServiceType
    items: list[RestaurantPublicOrderItem] = Field(min_length=1, max_length=40)
    customer_note: str | None = Field(default=None, max_length=500)
    allergy_note: str | None = Field(default=None, max_length=500)
    room_number: str | None = Field(default=None, min_length=1, max_length=32)
    customer_confirmation_count: int = Field(ge=2, le=2)

    @field_validator("language_code")
    @classmethod
    def _language_code(cls, value: str) -> str:
        normalized = value.strip().lower().replace("_", "-")
        if not normalized:
            raise ValueError("Dil kodu boş olamaz.")
        return normalized

    @field_validator("customer_note", "allergy_note", "room_number")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)
