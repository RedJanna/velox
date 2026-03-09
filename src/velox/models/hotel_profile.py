"""Hotel profile data models."""

from pydantic import BaseModel, Field


class LocalizedText(BaseModel):
    tr: str = ""
    en: str = ""


class ContactInfo(BaseModel):
    phone: str = ""
    email: str = ""
    hours: str = ""


class RoomType(BaseModel):
    id: int
    pms_room_type_id: int
    name: LocalizedText
    max_pax: int
    size_m2: int
    bed_type: str
    view: str
    features: list[str] = Field(default_factory=list)
    extra_bed: bool = False
    baby_crib: bool = False
    accessible: bool = False


class BoardType(BaseModel):
    id: int
    code: str  # BB, HB, FB, AI
    name: LocalizedText


class RateMapping(BaseModel):
    rate_type_id: int
    rate_code_id: int


class CancellationRule(BaseModel):
    free_cancel_deadline_days: int | None = None
    prepayment_days_before: int | None = None
    prepayment_amount: str = "1_night"
    prepayment_immediate: bool = False
    refund: bool = True
    refund_after_deadline: bool = False
    exception_days_before: int | None = None
    exception_refund: str | None = None


class TransferRouteConfig(BaseModel):
    route_code: str
    from_location: str
    to_location: str
    price_eur: float
    vehicle_type: str
    max_pax: int
    duration_min: int
    baby_seat: bool = False
    oversize_vehicle: dict | None = None


class RestaurantConfig(BaseModel):
    name: str
    concept: str
    capacity_min: int = 0
    capacity_max: int = 0
    area_types: list[str] = Field(default_factory=list)
    hours: dict[str, str] = Field(default_factory=dict)
    max_ai_party_size: int = 8
    late_tolerance_min: int = 15
    external_guests_allowed: bool = True


class HotelProfile(BaseModel):
    hotel_id: int
    hotel_name: LocalizedText
    hotel_type: str = "boutique"
    timezone: str = "Europe/Istanbul"
    currency_base: str = "EUR"
    pms: str = "elektraweb"
    whatsapp_number: str = ""
    season: dict[str, str] = Field(default_factory=dict)  # {open, close}
    contacts: dict[str, ContactInfo] = Field(default_factory=dict)
    room_types: list[RoomType] = Field(default_factory=list)
    board_types: list[BoardType] = Field(default_factory=list)
    rate_mapping: dict[str, RateMapping] = Field(default_factory=dict)
    cancellation_rules: dict[str, CancellationRule] = Field(default_factory=dict)
    transfer_routes: list[TransferRouteConfig] = Field(default_factory=list)
    restaurant: RestaurantConfig | None = None
    facility_policies: dict = Field(default_factory=dict)
    faq_data: list[dict] = Field(default_factory=list)
    payment: dict = Field(default_factory=dict)
