"""Unit tests for static hotel info lookup tool."""

from __future__ import annotations

import pytest

from velox.llm.function_registry import get_tool_definitions
from velox.models.hotel_profile import HotelProfile
from velox.tools.hotel_info import HotelInfoLookupTool


def _build_profile() -> HotelProfile:
    """Create hotel profile fixture with admin-managed extra fields."""
    return HotelProfile.model_validate(
        {
            "hotel_id": 21966,
            "hotel_name": {"tr": "Kassandra Oludeniz", "en": "Kassandra Oludeniz"},
            "contacts": {
                "reception": {
                    "phone": "+905332503277",
                    "email": "info@kassandraoludeniz.com",
                    "hours": "08:00-16:00",
                    "name": "Yağmur",
                },
                "restaurant": {
                    "phone": "+905332503277",
                    "email": "info@kassandraoludeniz.com",
                    "hours": "12:00-22:00",
                    "name": "Suat",
                },
            },
            "location": {
                "country": "Türkiye",
                "city": "Muğla",
                "district": "Fethiye",
                "address": "Ölüdeniz Mahallesi 224 Sk. No:12",
                "google_maps_hotel": "https://maps.app.goo.gl/YhDZEnhxzfnB1WgeA",
                "google_maps_restaurant": "https://maps.app.goo.gl/pMiKmhV57YVvAghe6",
            },
            "description": {
                "tr": "Ölüdeniz'de sakin bir butik otel.",
                "en": "A calm boutique hotel in Oludeniz.",
            },
            "highlights": ["beachside", "family_friendly"],
        }
    )


@pytest.mark.asyncio
async def test_hotel_info_lookup_returns_restaurant_map_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restaurant location query must return profile-backed restaurant map URL."""
    monkeypatch.setattr("velox.tools.hotel_info.get_profile", lambda _hotel_id: _build_profile())

    result = await HotelInfoLookupTool().execute(
        hotel_id=21966,
        query="Restoranınızın Google konum linkini paylaşır mısınız?",
        language="TR",
    )

    assert result["found"] is True
    assert result["topic"] == "restaurant_location"
    assert result["source_path"] == "location.google_maps_restaurant"
    assert result["value"] == "https://maps.app.goo.gl/pMiKmhV57YVvAghe6"


@pytest.mark.asyncio
async def test_hotel_info_lookup_returns_reception_contact_for_contact_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generic contact query should resolve to reception contact."""
    monkeypatch.setattr("velox.tools.hotel_info.get_profile", lambda _hotel_id: _build_profile())

    result = await HotelInfoLookupTool().execute(
        hotel_id=21966,
        query="İletişim numaranız nedir?",
        language="TR",
    )

    assert result["found"] is True
    assert result["topic"] == "reception_contact"
    assert result["source_path"] == "contacts.reception"
    assert result["value"]["phone"] == "+905332503277"


@pytest.mark.asyncio
async def test_hotel_info_lookup_returns_localized_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Description query should return localized value and both language variants."""
    monkeypatch.setattr("velox.tools.hotel_info.get_profile", lambda _hotel_id: _build_profile())

    result = await HotelInfoLookupTool().execute(
        hotel_id=21966,
        query="Can you tell me about your hotel?",
        language="EN",
    )

    assert result["found"] is True
    assert result["topic"] == "hotel_description"
    assert result["value"] == "A calm boutique hotel in Oludeniz."
    assert result["value_tr"] == "Ölüdeniz'de sakin bir butik otel."


def test_function_registry_includes_hotel_info_lookup() -> None:
    """hotel_info_lookup should be exposed to the LLM tool contract."""
    names = [
        str(item.get("function", {}).get("name") or "")
        for item in get_tool_definitions()
    ]
    assert "hotel_info_lookup" in names
