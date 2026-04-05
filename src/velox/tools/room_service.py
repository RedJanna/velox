"""Room service order tool — routes food/beverage orders to OPS/CHEF via notification."""

from __future__ import annotations

from typing import Any

import structlog

from velox.config.constants import RiskFlag
from velox.core.hotel_profile_loader import get_profile
from velox.db.repositories.hotel import NotificationRepository
from velox.tools.base import BaseTool
from velox.tools.notification import NotifySendTool

logger = structlog.get_logger(__name__)


class RoomServiceCreateOrderTool(BaseTool):
    """Create a room-service order request and notify OPS + CHEF.

    This tool does NOT fulfil the order itself.  It records the guest's
    request, validates it against the hotel-profile menu catalogue (if
    available) and sends notifications so that the kitchen / operations
    team can act on it.

    Required kwargs
    ---------------
    hotel_id : int
    room_number : str
    items : list[dict]          – each item: {"name": str, "quantity": int, "notes"?: str}

    Optional kwargs
    ---------------
    guest_name : str
    phone : str
    dietary_notes : str         – e.g. "vegan", "gluten-free"
    """

    def __init__(
        self,
        notification_repository: NotificationRepository,
    ) -> None:
        self._notification_repo = notification_repository

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "room_number", "items"])

        hotel_id: int = kwargs["hotel_id"]
        room_number: str = str(kwargs["room_number"])
        items: list[dict[str, Any]] = kwargs["items"]
        guest_name: str = kwargs.get("guest_name", "")
        phone: str = kwargs.get("phone", "")
        dietary_notes: str = kwargs.get("dietary_notes", "")

        # --- Menu catalogue validation ---
        profile = get_profile(hotel_id)
        menu_catalogue = _get_menu_catalogue(profile)
        validation = _validate_items_against_menu(items, menu_catalogue)

        risk_flags: list[str] = []
        if dietary_notes:
            risk_flags.append(RiskFlag.ALLERGY_ALERT)

        if not validation["all_verified"]:
            risk_flags.append(RiskFlag.MENU_HALLUCINATION_RISK)
            logger.warning(
                "room_service_unverified_items",
                hotel_id=hotel_id,
                unverified=validation["unverified_items"],
            )

        # --- Build notification message ---
        items_text = "\n".join(
            f"  - {item.get('name', '?')} x{item.get('quantity', 1)}"
            + (f" ({item['notes']})" if item.get("notes") else "")
            for item in items
        )
        menu_validation_label = (
            "Tamami dogrulandi"
            if validation["all_verified"]
            else "BAZI URUNLER DOGRULANAMADI - " + ", ".join(validation["unverified_items"])
        )

        notification_message = (
            f"[VELOX-L1] OPS/CHEF | room_service_order\n"
            f"Hotel: #{hotel_id}\n"
            f"Misafir: {guest_name} | {phone}\n"
            f"Oda: {room_number}\n"
            f"Siparis:\n{items_text}\n"
            f"Diyet Notu: {dietary_notes or 'Yok'}\n"
            f"Menu Dogrulama: {menu_validation_label}\n"
            f"Risk: {', '.join(risk_flags) if risk_flags else 'Yok'}"
        )

        # Notify CHEF
        notify_tool = NotifySendTool(self._notification_repo)
        await notify_tool.execute(
            hotel_id=hotel_id,
            to_role="CHEF",
            channel="panel",
            message=notification_message,
            metadata={
                "type": "room_service_order",
                "room_number": room_number,
                "items": items,
                "dietary_notes": dietary_notes,
                "menu_validated": validation["all_verified"],
            },
        )

        # Also notify OPS
        await notify_tool.execute(
            hotel_id=hotel_id,
            to_role="OPS",
            channel="panel",
            message=notification_message,
            metadata={
                "type": "room_service_order",
                "room_number": room_number,
            },
        )

        logger.info(
            "room_service_order_created",
            hotel_id=hotel_id,
            room_number=room_number,
            item_count=len(items),
            menu_validated=validation["all_verified"],
        )

        return {
            "success": True,
            "room_number": room_number,
            "items_count": len(items),
            "menu_validated": validation["all_verified"],
            "unverified_items": validation["unverified_items"],
            "risk_flags": risk_flags,
            "notifications_sent": ["CHEF", "OPS"],
            "message": (
                "Siparisiniz mutfak ve operasyon ekibine iletildi."
                if validation["all_verified"]
                else (
                    "Siparisiniz iletildi ancak bazi urunler menu katalogundan "
                    "dogrulanamadi. Ekibimiz sizinle iletisime gececektir."
                )
            ),
        }


def _get_menu_catalogue(profile: Any) -> list[str]:
    """Extract flat list of menu item names from hotel profile.

    Returns an empty list if the menu catalogue is not configured,
    which means NO item can be verified — triggering the hallucination
    guard.
    """
    if profile is None:
        return []

    restaurant = getattr(profile, "restaurant", None)
    if restaurant is None:
        return []

    menu = restaurant.get("menu") if isinstance(restaurant, dict) else getattr(restaurant, "menu", None)
    if menu is None:
        return []

    all_items: set[str] = set()
    _collect_menu_item_names(menu, all_items)
    return sorted(all_items)


def _collect_menu_item_names(value: Any, collector: set[str]) -> None:
    """Collect item names from flexible menu structures recursively."""
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized:
            collector.add(normalized)
        return

    if isinstance(value, list):
        for item in value:
            _collect_menu_item_names(item, collector)
        return

    if isinstance(value, dict):
        preferred_name_keys = ("name_tr", "name_en", "name", "item", "title")
        for key in preferred_name_keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                collector.add(candidate.strip().lower())
        for nested in value.values():
            _collect_menu_item_names(nested, collector)


def _validate_items_against_menu(
    items: list[dict[str, Any]],
    menu_catalogue: list[str],
) -> dict[str, Any]:
    """Check each ordered item against the known menu catalogue.

    If the menu catalogue is empty (not configured), ALL items are
    treated as unverified.
    """
    if not menu_catalogue:
        return {
            "all_verified": False,
            "unverified_items": [item.get("name", "?") for item in items],
            "reason": "menu_catalogue_not_configured",
        }

    unverified: list[str] = []
    for item in items:
        item_name = (item.get("name") or "").lower()
        if item_name and item_name not in menu_catalogue:
            unverified.append(item.get("name", "?"))

    return {
        "all_verified": len(unverified) == 0,
        "unverified_items": unverified,
    }
