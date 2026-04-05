"""Static hotel information lookup tool backed by HOTEL_PROFILE."""

from __future__ import annotations

import unicodedata
from typing import Any

from velox.core.hotel_profile_loader import get_profile
from velox.models.hotel_profile import HotelProfile
from velox.tools.base import BaseTool


def _normalize_text(value: str) -> str:
    """Normalize text for keyword matching across accents and punctuation."""
    lowered = str(value or "").casefold().strip()
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(stripped.split())


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Return True when normalized text contains any keyword token."""
    return any(keyword in text for keyword in keywords)


def _profile_extras(profile: HotelProfile) -> dict[str, Any]:
    """Return extra admin-managed keys that are not explicitly modelled."""
    extras = profile.model_extra
    if isinstance(extras, dict):
        return extras
    return {}


def _contact_payload(profile: HotelProfile, key: str) -> dict[str, Any] | None:
    """Return one contact object as JSON-serializable dict."""
    contact = profile.contacts.get(key)
    if contact is None:
        return None
    payload = contact.model_dump(mode="json")
    return payload if isinstance(payload, dict) else None


class HotelInfoLookupTool(BaseTool):
    """Resolve static hotel facts from HOTEL_PROFILE using guest query text."""

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.validate_required(kwargs, ["hotel_id", "query", "language"])
        hotel_id = int(kwargs["hotel_id"])
        query = str(kwargs["query"] or "").strip()
        language = str(kwargs["language"] or "en").casefold()

        profile = get_profile(hotel_id)
        if profile is None:
            return {"found": False, "error": "Hotel profile not found."}

        normalized_query = _normalize_text(query)
        extras = _profile_extras(profile)
        location = extras.get("location") if isinstance(extras.get("location"), dict) else {}
        description = extras.get("description") if isinstance(extras.get("description"), dict) else {}
        highlights = extras.get("highlights") if isinstance(extras.get("highlights"), list) else []

        wants_location = _contains_any(
            normalized_query,
            (
                "konum",
                "location",
                "where",
                "adres",
                "address",
                "map",
                "maps",
                "google",
                "yol tarifi",
                "direction",
            ),
        )
        wants_restaurant = _contains_any(
            normalized_query,
            ("restoran", "restaurant", "dinner", "lunch", "kahvalti", "kahvaltı"),
        )
        wants_hotel = _contains_any(normalized_query, ("otel", "hotel", "property"))
        wants_contact = _contains_any(
            normalized_query,
            ("iletisim", "iletişim", "contact", "phone", "telefon", "email", "e-posta", "mail", "hours"),
        )
        wants_description = _contains_any(
            normalized_query,
            ("hakkinda", "hakkında", "about", "description", "tanit", "tanıt", "hotel info", "otel bilgi"),
        )
        wants_highlights = _contains_any(
            normalized_query,
            ("ozellik", "özellik", "feature", "highlights", "avantaj", "imkan", "imkanlar", "facility"),
        )

        restaurant_map = str(location.get("google_maps_restaurant") or "").strip()
        hotel_map = str(location.get("google_maps_hotel") or "").strip()
        if wants_location and wants_restaurant and restaurant_map:
            return {
                "found": True,
                "topic": "restaurant_location",
                "source": "HOTEL_PROFILE",
                "source_path": "location.google_maps_restaurant",
                "value": restaurant_map,
            }

        if wants_location and hotel_map and (wants_hotel or not wants_restaurant):
            return {
                "found": True,
                "topic": "hotel_location",
                "source": "HOTEL_PROFILE",
                "source_path": "location.google_maps_hotel",
                "value": hotel_map,
            }

        if wants_location and location:
            return {
                "found": True,
                "topic": "hotel_address",
                "source": "HOTEL_PROFILE",
                "source_path": "location",
                "value": {
                    "country": location.get("country"),
                    "city": location.get("city"),
                    "district": location.get("district"),
                    "address": location.get("address"),
                    "google_maps_hotel": location.get("google_maps_hotel"),
                    "google_maps_restaurant": location.get("google_maps_restaurant"),
                },
            }

        if wants_contact and wants_restaurant:
            restaurant_contact = _contact_payload(profile, "restaurant")
            if restaurant_contact:
                return {
                    "found": True,
                    "topic": "restaurant_contact",
                    "source": "HOTEL_PROFILE",
                    "source_path": "contacts.restaurant",
                    "value": restaurant_contact,
                }

        if wants_contact and _contains_any(normalized_query, ("housekeeping", "kat hizmetleri")):
            housekeeping_contact = _contact_payload(profile, "housekeeping")
            if housekeeping_contact:
                return {
                    "found": True,
                    "topic": "housekeeping_contact",
                    "source": "HOTEL_PROFILE",
                    "source_path": "contacts.housekeeping",
                    "value": housekeeping_contact,
                }

        if wants_contact and _contains_any(normalized_query, ("admin", "yonetim", "yönetim", "escalation")):
            escalation_contact = _contact_payload(profile, "escalation_admin")
            if escalation_contact:
                return {
                    "found": True,
                    "topic": "escalation_contact",
                    "source": "HOTEL_PROFILE",
                    "source_path": "contacts.escalation_admin",
                    "value": escalation_contact,
                }

        if wants_contact:
            reception_contact = _contact_payload(profile, "reception")
            if reception_contact:
                return {
                    "found": True,
                    "topic": "reception_contact",
                    "source": "HOTEL_PROFILE",
                    "source_path": "contacts.reception",
                    "value": reception_contact,
                }

        if wants_description and description:
            localized_description = (
                description.get("tr")
                if language == "tr"
                else description.get("en")
            ) or description.get("en") or description.get("tr")
            return {
                "found": True,
                "topic": "hotel_description",
                "source": "HOTEL_PROFILE",
                "source_path": "description",
                "value": localized_description,
                "value_tr": description.get("tr"),
                "value_en": description.get("en"),
            }

        if wants_highlights and highlights:
            return {
                "found": True,
                "topic": "hotel_highlights",
                "source": "HOTEL_PROFILE",
                "source_path": "highlights",
                "value": highlights,
            }

        return {
            "found": False,
            "source": "HOTEL_PROFILE",
            "available_paths": [
                "location.google_maps_hotel",
                "location.google_maps_restaurant",
                "location.address",
                "contacts.reception",
                "contacts.restaurant",
                "contacts.housekeeping",
                "contacts.escalation_admin",
                "description",
                "highlights",
            ],
        }
