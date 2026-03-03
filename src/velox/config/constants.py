"""Velox system constants — Intent, State, RiskFlag, Role enums."""

from enum import StrEnum


class Intent(StrEnum):
    # Stay
    STAY_AVAILABILITY = "stay_availability"
    STAY_QUOTE = "stay_quote"
    STAY_BOOKING_CREATE = "stay_booking_create"
    STAY_MODIFY = "stay_modify"
    STAY_CANCEL = "stay_cancel"

    # Restaurant
    RESTAURANT_AVAILABILITY = "restaurant_availability"
    RESTAURANT_BOOKING_CREATE = "restaurant_booking_create"
    RESTAURANT_MODIFY = "restaurant_modify"
    RESTAURANT_CANCEL = "restaurant_cancel"

    # Transfer
    TRANSFER_INFO = "transfer_info"
    TRANSFER_BOOKING_CREATE = "transfer_booking_create"
    TRANSFER_MODIFY = "transfer_modify"
    TRANSFER_CANCEL = "transfer_cancel"

    # Guest Operations
    GUEST_MODIFY_NAME = "guest_modify_name"
    GUEST_MODIFY_ROOM = "guest_modify_room"
    EARLY_CHECKIN_REQUEST = "early_checkin_request"
    LATE_CHECKOUT_REQUEST = "late_checkout_request"
    SPECIAL_EVENT_REQUEST = "special_event_request"

    # General
    FAQ_INFO = "faq_info"
    COMPLAINT = "complaint"
    HUMAN_HANDOFF = "human_handoff"
    PAYMENT_INQUIRY = "payment_inquiry"
    OTHER = "other"


class ConversationState(StrEnum):
    GREETING = "GREETING"
    INTENT_DETECTED = "INTENT_DETECTED"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    READY_FOR_TOOL = "READY_FOR_TOOL"
    TOOL_RUNNING = "TOOL_RUNNING"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    HANDOFF = "HANDOFF"
    CLOSED = "CLOSED"


class RiskFlag(StrEnum):
    # L3 — Critical
    LEGAL_REQUEST = "LEGAL_REQUEST"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    THREAT_SELF_HARM = "THREAT_SELF_HARM"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"

    # L2 — Assisted
    PAYMENT_CONFUSION = "PAYMENT_CONFUSION"
    CHARGEBACK_MENTION = "CHARGEBACK_MENTION"
    REFUND_DISPUTE = "REFUND_DISPUTE"
    ANGRY_COMPLAINT = "ANGRY_COMPLAINT"
    HARASSMENT_HATE = "HARASSMENT_HATE"
    FRAUD_SIGNAL = "FRAUD_SIGNAL"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    TOOL_ERROR_REPEAT = "TOOL_ERROR_REPEAT"
    DATA_INCONSISTENCY = "DATA_INCONSISTENCY"
    RATE_MAPPING_MISSING = "RATE_MAPPING_MISSING"
    GROUP_BOOKING = "GROUP_BOOKING"
    SPECIAL_EVENT = "SPECIAL_EVENT"
    PII_OVERREQUEST = "PII_OVERREQUEST"

    # L1 — Soft
    VIP_REQUEST = "VIP_REQUEST"
    ALLERGY_ALERT = "ALLERGY_ALERT"
    ACCESSIBILITY_NEED = "ACCESSIBILITY_NEED"
    NO_SHOW_RISK = "NO_SHOW_RISK"
    CAPACITY_LIMIT = "CAPACITY_LIMIT"
    OVERBOOK_RISK = "OVERBOOK_RISK"
    POLICY_MISSING = "POLICY_MISSING"
    LOST_ITEM = "LOST_ITEM"

    # L0 — Self-Serve
    TEMPLATE_MISSING = "TEMPLATE_MISSING"
    LANGUAGE_UNSUPPORTED = "LANGUAGE_UNSUPPORTED"
    RESERVATION_ID_MISSING = "RESERVATION_ID_MISSING"
    DATE_INVALID = "DATE_INVALID"
    CURRENCY_CONVERSION_REQUEST = "CURRENCY_CONVERSION_REQUEST"


class EscalationLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Role(StrEnum):
    ADMIN = "ADMIN"
    SALES = "SALES"
    OPS = "OPS"
    CHEF = "CHEF"
    NONE = "NONE"


class ApprovalType(StrEnum):
    STAY = "STAY"
    RESTAURANT = "RESTAURANT"
    TRANSFER = "TRANSFER"


class PaymentDueMode(StrEnum):
    NOW = "NOW"
    SCHEDULED = "SCHEDULED"


class PaymentMethod(StrEnum):
    BANK_TRANSFER = "BANK_TRANSFER"
    PAYMENT_LINK = "PAYMENT_LINK"
    MAIL_ORDER = "MAIL_ORDER"


class CancelPolicyType(StrEnum):
    FREE_CANCEL = "FREE_CANCEL"
    NON_REFUNDABLE = "NON_REFUNDABLE"


class HoldStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class NotifyChannel(StrEnum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PANEL = "panel"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


SUPPORTED_LANGUAGES = ["en", "tr", "ru", "de", "ar", "es", "fr", "zh", "hi", "pt"]
TOOL_LANGUAGES = ["TR", "EN"]
DEFAULT_LANGUAGE = "en"
BASE_CURRENCY = "EUR"

# Session
SESSION_TIMEOUT_SECONDS = 1800  # 30 min
SESSION_HARD_TIMEOUT_SECONDS = 86400  # 24 hours
CONTEXT_WINDOW_MAX_MESSAGES = 20

# Rate Limits
MAX_TOOL_RETRIES = 3
TOOL_RETRY_BACKOFF_SECONDS = [1, 3, 5]

# Restaurant
MAX_AI_RESTAURANT_PARTY_SIZE = 8
RESTAURANT_LATE_TOLERANCE_MINUTES = 15
