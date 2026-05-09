"""Unit tests for static hotel info lookup tool."""

from __future__ import annotations

import pytest

from velox.llm.function_registry import get_tool_definitions
from velox.models.hotel_information import HotelInformationDataset
from velox.models.hotel_profile import HotelProfile
from velox.tools.faq import FAQLookupTool
from velox.tools.hotel_info import HotelInfoLookupTool


def _build_profile() -> HotelProfile:
    """Create hotel profile fixture with admin-managed extra fields."""
    return HotelProfile.model_validate(
        {
            "hotel_id": 21966,
            "hotel_name": {"tr": "Kassandra Oludeniz", "en": "Kassandra Oludeniz"},
            "hotel_information_source": "data/hotel_information/kassandra_oludeniz.json",
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


def _build_information_dataset() -> HotelInformationDataset:
    """Create structured hotel information fixture with final JSON fields."""
    return HotelInformationDataset.model_validate(
        {
            "hotel_data_version": "1.0.0",
            "language": "tr",
            "status": "final",
            "hotel_information": [
                {
                    "id": "breakfast_service_type",
                    "category": "breakfast",
                    "title_tr": "Kahvaltı Servis Türü",
                    "answer_tr": "Kahvaltı açık büfe olarak servis edilmektedir.",
                    "data_type": "text",
                    "value": "Açık büfe",
                    "unit": None,
                    "confidence": "high",
                    "human_handoff_required": False,
                    "missing_information": False,
                    "notes": "Genel kahvaltı sorularında bu cevap verilebilir.",
                    "trigger_examples": ["Kahvaltı açık büfe mi?"],
                },
                {
                    "id": "product_detail_handoff_rule",
                    "category": "human_handoff",
                    "title_tr": "Ürün Detayı Sorularında İnsan Temsilciye Devir",
                    "answer_tr": (
                        "Bu ürünle ilgili en doğru bilgiyi verebilmemiz için sizi "
                        "ekip arkadaşlarımıza yönlendiriyoruz."
                    ),
                    "data_type": "rule",
                    "value": "Ürün detayı insan temsilciye devredilmelidir.",
                    "unit": None,
                    "confidence": "high",
                    "human_handoff_required": True,
                    "missing_information": False,
                    "notes": "Ürün detayı hakkında kesin bilgi verilmemelidir.",
                    "trigger_examples": ["Kahvaltıda Ezine peyniri var mı?"],
                },
                {
                    "id": "belcekiz_beach_distance",
                    "category": "location",
                    "title_tr": "Belcekız Plajı Mesafesi",
                    "answer_tr": (
                        "Otelimiz, Belcekız Plajı’na yaklaşık 300 metre mesafededir. "
                        "Yürüyerek ortalama 2–5 dakika içinde ulaşım sağlayabilirsiniz."
                    ),
                    "data_type": "distance",
                    "value": {"distance_meters": 300},
                    "unit": {"distance": "metre", "time": "dakika"},
                    "confidence": "high",
                    "human_handoff_required": False,
                    "missing_information": False,
                    "notes": "Genel plaj sorularında kullanılır.",
                    "trigger_examples": ["Plaja kaç metre?"],
                },
                {
                    "id": "room_door_lock_system",
                    "category": "room_feature",
                    "title_tr": "Oda Kapı Kilit Sistemi",
                    "answer_tr": (
                        "Oda kapılarında oda tipine göre klasik anahtar veya elektrik "
                        "kartlı sistem kullanılmaktadır. Bazı odalarda klasik anahtar, "
                        "bazı odalarda ise elektrik kartlı sistem mevcuttur."
                    ),
                    "data_type": "mixed",
                    "value": ["Klasik anahtar", "Elektrik kartlı sistem"],
                    "unit": None,
                    "confidence": "high",
                    "human_handoff_required": False,
                    "missing_information": False,
                    "notes": "Oda kapı sistemi sorularında kullanılır.",
                    "trigger_examples": ["Oda kapıları kartlı mı?"],
                },
            ],
            "global_response_rules": [],
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


@pytest.mark.asyncio
async def test_hotel_info_lookup_returns_json_answer_tr_for_beach_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """General beach queries must use the structured Belcekiz answer."""
    monkeypatch.setattr("velox.tools.hotel_info.get_profile", lambda _hotel_id: _build_profile())
    monkeypatch.setattr("velox.tools.hotel_info.get_hotel_information", lambda _hotel_id: _build_information_dataset())

    result = await HotelInfoLookupTool().execute(hotel_id=21966, query="Plaja kaç metre?", language="TR")

    assert result["source"] == "HOTEL_INFORMATION_JSON"
    assert result["topic"] == "belcekiz_beach_distance"
    assert result["answer"] == _build_information_dataset().entry_by_id("belcekiz_beach_distance").answer_tr
    assert result["handoff"]["needed"] is False


@pytest.mark.asyncio
async def test_hotel_info_lookup_handoffs_product_detail_questions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Specific breakfast/minibar/product detail questions must trigger handoff."""
    monkeypatch.setattr("velox.tools.hotel_info.get_profile", lambda _hotel_id: _build_profile())
    monkeypatch.setattr("velox.tools.hotel_info.get_hotel_information", lambda _hotel_id: _build_information_dataset())

    result = await HotelInfoLookupTool().execute(
        hotel_id=21966,
        query="Kahvaltıda Ezine peyniri var mı?",
        language="TR",
    )

    assert result["topic"] == "product_detail_handoff_rule"
    assert result["human_handoff_required"] is True
    assert result["should_answer_directly"] is False
    assert result["handoff"]["needed"] is True


@pytest.mark.asyncio
async def test_hotel_info_lookup_returns_room_door_answer_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Door lock questions should return the final JSON answer_tr text."""
    monkeypatch.setattr("velox.tools.hotel_info.get_profile", lambda _hotel_id: _build_profile())
    monkeypatch.setattr("velox.tools.hotel_info.get_hotel_information", lambda _hotel_id: _build_information_dataset())

    result = await HotelInfoLookupTool().execute(hotel_id=21966, query="Oda kapıları kartlı mı?", language="TR")

    expected = _build_information_dataset().entry_by_id("room_door_lock_system").answer_tr
    assert result["answer"] == expected
    assert result["value"] == ["Klasik anahtar", "Elektrik kartlı sistem"]


@pytest.mark.asyncio
async def test_faq_lookup_prefers_hotel_information_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FAQ lookup should not override structured hotel-information answers."""
    monkeypatch.setattr("velox.tools.faq.get_profile", lambda _hotel_id: _build_profile())
    monkeypatch.setattr("velox.tools.faq.get_hotel_information", lambda _hotel_id: _build_information_dataset())

    result = await FAQLookupTool().execute(hotel_id=21966, query="Denize uzaklığınız nedir?", language="TR")

    assert result["source"] == "HOTEL_INFORMATION_JSON"
    assert result["topic"] == "belcekiz_beach_distance"
    assert result["answer"] == _build_information_dataset().entry_by_id("belcekiz_beach_distance").answer_tr
