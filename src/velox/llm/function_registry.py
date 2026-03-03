"""OpenAI function-calling tool definitions for Velox."""

from typing import Any


def _def(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Build a function definition item."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return tool definitions aligned with master_prompt_v2 A8.1-A8.5."""
    return [
        _def(
            "booking_availability",
            "Check room availability for stay dates and guest count.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "checkin_date": {"type": "string", "format": "date"},
                    "checkout_date": {"type": "string", "format": "date"},
                    "adults": {"type": "integer"},
                    "chd_count": {"type": "integer", "default": 0},
                    "chd_ages": {"type": "array", "items": {"type": "integer"}},
                    "currency": {"type": "string", "default": "EUR"},
                },
                "required": ["hotel_id", "checkin_date", "checkout_date", "adults"],
            },
        ),
        _def(
            "booking_quote",
            "Get official stay price offer from PMS.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "checkin_date": {"type": "string", "format": "date"},
                    "checkout_date": {"type": "string", "format": "date"},
                    "adults": {"type": "integer"},
                    "chd_count": {"type": "integer", "default": 0},
                    "chd_ages": {"type": "array", "items": {"type": "integer"}},
                    "currency": {"type": "string", "default": "EUR"},
                    "language": {"type": "string", "enum": ["TR", "EN"], "default": "EN"},
                    "nationality": {"type": "string", "default": "GB"},
                    "only_best_offer": {"type": "boolean", "default": False},
                    "cancel_policy_type": {"type": "string", "enum": ["NON_REFUNDABLE", "FREE_CANCEL"]},
                },
                "required": ["hotel_id", "checkin_date", "checkout_date", "adults"],
            },
        ),
        _def(
            "stay_create_hold",
            "Create stay draft hold before admin approval.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "draft": {
                        "type": "object",
                        "properties": {
                            "checkin_date": {"type": "string", "format": "date"},
                            "checkout_date": {"type": "string", "format": "date"},
                            "room_type_id": {"type": "integer"},
                            "board_type_id": {"type": "integer"},
                            "rate_type_id": {"type": "integer"},
                            "rate_code_id": {"type": "integer"},
                            "price_agency_id": {"type": "integer"},
                            "currency_display": {"type": "string"},
                            "total_price_eur": {"type": "number"},
                            "adults": {"type": "integer"},
                            "chd_ages": {"type": "array", "items": {"type": "integer"}},
                            "guest_name": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string"},
                            "notes": {"type": "string"},
                        },
                        "required": [
                            "checkin_date",
                            "checkout_date",
                            "room_type_id",
                            "board_type_id",
                            "rate_type_id",
                            "rate_code_id",
                            "price_agency_id",
                            "currency_display",
                            "total_price_eur",
                            "adults",
                            "guest_name",
                            "phone",
                        ],
                    },
                },
                "required": ["hotel_id", "draft"],
            },
        ),
        _def(
            "booking_create_reservation",
            "Create final stay reservation in PMS.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "draft": {
                        "type": "object",
                        "properties": {
                            "checkin_date": {"type": "string", "format": "date"},
                            "checkout_date": {"type": "string", "format": "date"},
                            "room_type_id": {"type": "integer"},
                            "board_type_id": {"type": "integer"},
                            "rate_type_id": {"type": "integer"},
                            "rate_code_id": {"type": "integer"},
                            "price_agency_id": {"type": "integer"},
                            "currency": {"type": "string"},
                            "total_price": {"type": "number"},
                            "adults": {"type": "integer"},
                            "chd_ages": {"type": "array", "items": {"type": "integer"}},
                            "guest_name": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string"},
                            "notes": {"type": "string"},
                        },
                        "required": [
                            "checkin_date",
                            "checkout_date",
                            "room_type_id",
                            "board_type_id",
                            "rate_type_id",
                            "rate_code_id",
                            "price_agency_id",
                            "currency",
                            "total_price",
                            "adults",
                            "guest_name",
                            "phone",
                        ],
                    },
                },
                "required": ["hotel_id", "draft"],
            },
        ),
        _def(
            "booking_get_reservation",
            "Fetch reservation detail by reservation id or voucher number.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "reservation_id": {"type": "string"},
                    "voucher_no": {"type": "string"},
                },
                "required": ["hotel_id"],
            },
        ),
        _def(
            "booking_modify",
            "Modify an existing stay reservation.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "reservation_id": {"type": "string"},
                    "voucher_no": {"type": "string"},
                    "updates": {"type": "object", "additionalProperties": True},
                },
                "required": ["hotel_id", "updates"],
            },
        ),
        _def(
            "booking_cancel",
            "Cancel an existing stay reservation.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "reservation_id": {"type": "string"},
                    "voucher_no": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["hotel_id"],
            },
        ),
        _def(
            "restaurant_availability",
            "Check restaurant slot availability.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "date": {"type": "string", "format": "date"},
                    "time": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "area": {"type": "string", "enum": ["indoor", "outdoor"]},
                    "notes": {"type": "string"},
                },
                "required": ["hotel_id", "date", "time", "party_size"],
            },
        ),
        _def(
            "restaurant_create_hold",
            "Create restaurant hold before approval.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "slot_id": {"type": "string"},
                    "guest_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "notes": {"type": "string"},
                },
                "required": ["hotel_id", "slot_id", "guest_name", "phone", "party_size"],
            },
        ),
        _def(
            "restaurant_confirm",
            "Confirm approved restaurant hold.",
            {
                "type": "object",
                "properties": {"hotel_id": {"type": "integer"}, "restaurant_hold_id": {"type": "string"}},
                "required": ["hotel_id", "restaurant_hold_id"],
            },
        ),
        _def(
            "restaurant_modify",
            "Modify restaurant hold details.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "restaurant_hold_id": {"type": "string"},
                    "updates": {"type": "object", "additionalProperties": True},
                },
                "required": ["hotel_id", "restaurant_hold_id", "updates"],
            },
        ),
        _def(
            "restaurant_cancel",
            "Cancel restaurant hold or reservation.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "restaurant_hold_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["hotel_id", "restaurant_hold_id"],
            },
        ),
        _def(
            "approval_request",
            "Create approval request for stay, restaurant, or transfer.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "approval_type": {"type": "string", "enum": ["STAY", "RESTAURANT", "TRANSFER"]},
                    "reference_id": {"type": "string"},
                    "details_summary": {"type": "string"},
                    "required_roles": {"type": "array", "items": {"type": "string"}},
                    "any_of": {"type": "boolean", "default": False},
                },
                "required": ["hotel_id", "approval_type", "reference_id", "details_summary", "required_roles"],
            },
        ),
        _def(
            "payment_request_prepayment",
            "Create manual prepayment request handled by sales/admin.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "reference_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "methods": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["BANK_TRANSFER", "PAYMENT_LINK", "MAIL_ORDER"]},
                    },
                    "due_mode": {"type": "string", "enum": ["NOW", "SCHEDULED"]},
                    "scheduled_date": {"type": "string", "format": "date"},
                },
                "required": ["hotel_id", "reference_id", "amount", "currency", "methods", "due_mode"],
            },
        ),
        _def(
            "notify_send",
            "Send internal notification to role/channel.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "to_role": {"type": "string", "enum": ["ADMIN", "CHEF", "SALES", "OPS"]},
                    "channel": {"type": "string", "enum": ["whatsapp", "email", "panel"]},
                    "message": {"type": "string"},
                    "metadata": {"type": "object", "additionalProperties": True},
                },
                "required": ["hotel_id", "to_role", "channel", "message"],
            },
        ),
        _def(
            "handoff_create_ticket",
            "Create handoff/support ticket for human follow-up.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "reason": {"type": "string"},
                    "transcript_summary": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "dedupe_key": {"type": "string"},
                },
                "required": ["hotel_id", "reason", "transcript_summary"],
            },
        ),
        _def(
            "crm_log",
            "Log structured CRM trace of the conversation turn.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "user_phone_hash": {"type": "string"},
                    "intent": {"type": "string"},
                    "entities": {"type": "object", "additionalProperties": True},
                    "actions": {"type": "array", "items": {"type": "string"}},
                    "outcome": {"type": "string"},
                    "transcript_summary": {"type": "string"},
                },
                "required": ["hotel_id", "user_phone_hash", "intent", "entities", "actions", "outcome"],
            },
        ),
        _def(
            "transfer_get_info",
            "Get transfer route, vehicle, and EUR pricing info.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "route": {
                        "type": "string",
                        "enum": [
                            "DALAMAN_AIRPORT_TO_HOTEL",
                            "ANTALYA_AIRPORT_TO_HOTEL",
                            "HOTEL_TO_DALAMAN_AIRPORT",
                            "HOTEL_TO_ANTALYA_AIRPORT",
                            "CUSTOM",
                        ],
                    },
                    "pax_count": {"type": "integer"},
                },
                "required": ["hotel_id", "route", "pax_count"],
            },
        ),
        _def(
            "transfer_create_hold",
            "Create transfer hold before admin approval.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "route": {"type": "string"},
                    "date": {"type": "string", "format": "date"},
                    "time": {"type": "string"},
                    "pax_count": {"type": "integer"},
                    "guest_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "flight_no": {"type": "string"},
                    "baby_seat": {"type": "boolean", "default": False},
                    "notes": {"type": "string"},
                },
                "required": ["hotel_id", "route", "date", "time", "pax_count", "guest_name", "phone"],
            },
        ),
        _def(
            "transfer_confirm",
            "Confirm approved transfer hold.",
            {
                "type": "object",
                "properties": {"hotel_id": {"type": "integer"}, "transfer_hold_id": {"type": "string"}},
                "required": ["hotel_id", "transfer_hold_id"],
            },
        ),
        _def(
            "transfer_modify",
            "Modify transfer hold details.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "transfer_hold_id": {"type": "string"},
                    "updates": {"type": "object", "additionalProperties": True},
                },
                "required": ["hotel_id", "transfer_hold_id", "updates"],
            },
        ),
        _def(
            "transfer_cancel",
            "Cancel transfer hold or reservation.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "transfer_hold_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["hotel_id", "transfer_hold_id"],
            },
        ),
        _def(
            "faq_lookup",
            "Look up FAQ answer from HOTEL_PROFILE FAQ data.",
            {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "integer"},
                    "query": {"type": "string"},
                    "language": {"type": "string", "enum": ["TR", "EN"], "default": "EN"},
                },
                "required": ["hotel_id", "query", "language"],
            },
        ),
    ]
