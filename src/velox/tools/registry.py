"""Tool registration and singleton dispatcher."""

from velox.db.repositories.hotel import (
    ApprovalRequestRepository,
    CrmLogRepository,
    NotificationPhoneRepository,
    NotificationRepository,
    PaymentRequestRepository,
    TicketRepository,
)
from velox.db.repositories.reservation import ReservationRepository
from velox.db.repositories.restaurant import RestaurantRepository
from velox.db.repositories.transfer import TransferRepository
from velox.tools.approval import ApprovalRequestTool
from velox.tools.base import ToolDispatcher
from velox.tools.booking import (
    BookingAvailabilityTool,
    BookingCancelTool,
    BookingCreateReservationTool,
    BookingGetReservationTool,
    BookingModifyTool,
    BookingQuoteTool,
    StayCreateHoldTool,
)
from velox.tools.crm import CRMLogTool
from velox.tools.faq import FAQLookupTool
from velox.tools.hotel_info import HotelInfoLookupTool
from velox.tools.handoff import HandoffCreateTicketTool
from velox.tools.notification import NotifySendTool
from velox.tools.payment import PaymentRequestPrepaymentTool
from velox.tools.restaurant import (
    RestaurantAvailabilityTool,
    RestaurantCancelTool,
    RestaurantConfirmTool,
    RestaurantCreateHoldTool,
    RestaurantModifyTool,
)
from velox.tools.room_service import RoomServiceCreateOrderTool
from velox.tools.transfer import (
    TransferCancelTool,
    TransferConfirmTool,
    TransferCreateHoldTool,
    TransferGetInfoTool,
    TransferModifyTool,
)

_dispatcher: ToolDispatcher | None = None


def build_dispatcher() -> ToolDispatcher:
    """Build dispatcher with all tool registrations."""
    dispatcher = ToolDispatcher()

    reservation_repository = ReservationRepository()
    restaurant_repository = RestaurantRepository()
    transfer_repository = TransferRepository()
    approval_repository = ApprovalRequestRepository()
    payment_repository = PaymentRequestRepository()
    ticket_repository = TicketRepository()
    notification_repository = NotificationRepository()
    crm_repository = CrmLogRepository()
    notification_phone_repository = NotificationPhoneRepository()

    approval_tool = ApprovalRequestTool(
        approval_repository, notification_repository, notification_phone_repository,
    )

    dispatcher.register("booking_availability", BookingAvailabilityTool())
    dispatcher.register("booking_quote", BookingQuoteTool())
    dispatcher.register(
        "stay_create_hold",
        StayCreateHoldTool(reservation_repository, approval_tool),
    )
    dispatcher.register("booking_create_reservation", BookingCreateReservationTool())
    dispatcher.register("booking_get_reservation", BookingGetReservationTool())
    dispatcher.register("booking_modify", BookingModifyTool())
    dispatcher.register("booking_cancel", BookingCancelTool())

    dispatcher.register("restaurant_availability", RestaurantAvailabilityTool(restaurant_repository))
    dispatcher.register(
        "restaurant_create_hold",
        RestaurantCreateHoldTool(
            restaurant_repository,
            approval_repository,
            notification_repository,
        ),
    )
    dispatcher.register("restaurant_confirm", RestaurantConfirmTool(restaurant_repository))
    dispatcher.register("restaurant_modify", RestaurantModifyTool())
    dispatcher.register("restaurant_cancel", RestaurantCancelTool(restaurant_repository))

    dispatcher.register(
        "room_service_create_order",
        RoomServiceCreateOrderTool(notification_repository),
    )

    dispatcher.register("transfer_get_info", TransferGetInfoTool())
    dispatcher.register("transfer_create_hold", TransferCreateHoldTool(transfer_repository, approval_tool))
    dispatcher.register("transfer_confirm", TransferConfirmTool())
    dispatcher.register("transfer_modify", TransferModifyTool())
    dispatcher.register("transfer_cancel", TransferCancelTool())

    dispatcher.register("approval_request", approval_tool)
    dispatcher.register(
        "payment_request_prepayment",
        PaymentRequestPrepaymentTool(payment_repository, notification_repository),
    )
    dispatcher.register("notify_send", NotifySendTool(notification_repository))
    dispatcher.register("handoff_create_ticket", HandoffCreateTicketTool(ticket_repository, notification_repository))
    dispatcher.register("crm_log", CRMLogTool(crm_repository))
    dispatcher.register("faq_lookup", FAQLookupTool())
    dispatcher.register("hotel_info_lookup", HotelInfoLookupTool())

    return dispatcher


def initialize_tool_dispatcher() -> ToolDispatcher:
    """Initialize singleton dispatcher and return it."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = build_dispatcher()
    return _dispatcher


def get_tool_dispatcher() -> ToolDispatcher:
    """Get initialized tool dispatcher."""
    if _dispatcher is None:
        return initialize_tool_dispatcher()
    return _dispatcher
