"""Unit tests for prompt builder conversational-flow constraints."""

from velox.llm.prompt_builder import PromptBuilder
from velox.models.conversation import Conversation
from velox.models.hotel_profile import HotelProfile


def _build_profile(hotel_id: int = 21966) -> HotelProfile:
    return HotelProfile(
        hotel_id=hotel_id,
        hotel_name={"tr": "Kassandra Oludeniz", "en": "Kassandra Oludeniz"},
        contacts={
            "reception": {
                "phone": "+905332503277",
                "email": "info@kassandraoludeniz.com",
                "hours": "24/7",
            }
        },
        room_types=[
            {
                "id": 1,
                "pms_room_type_id": 101,
                "name": {"tr": "Deluxe Oda", "en": "Deluxe Room"},
                "max_pax": 3,
                "size_m2": 28,
                "bed_type": "double",
                "view": "garden",
                "features": ["balcony"],
                "extra_bed": True,
                "baby_crib": True,
                "accessible": False,
            }
        ],
        board_types=[
            {"id": 1, "code": "BB", "name": {"tr": "Kahvalti", "en": "Breakfast"}}
        ],
        restaurant={
            "name": "Moonlight",
            "concept": "a_la_carte",
            "capacity_min": 2,
            "capacity_max": 40,
            "area_types": ["outdoor"],
            "hours": {"dinner": "19:00-23:00"},
            "menu": {"desserts": [{"name_tr": "Meyve Tabagi"}]},
        },
        facility_policies={
            "check_in": {"time": "14:00"},
            "wifi": {"available": True},
        },
        faq_data=[
            {
                "faq_id": "faq_checkin",
                "topic": "check_in_time",
                "question_tr": "Check-in saati kac?",
                "answer_tr": "Standart check-in saatimiz 14:00 itibariyladir.",
            }
        ],
        location={
            "country": "Türkiye",
            "city": "Muğla",
            "district": "Fethiye",
            "address": "Ölüdeniz Mahallesi 224 Sk. No:12",
            "google_maps_hotel": "https://maps.app.goo.gl/YhDZEnhxzfnB1WgeA",
            "google_maps_restaurant": "https://maps.app.goo.gl/pMiKmhV57YVvAghe6",
        },
        description={
            "tr": "Otel aciklamasi tr",
            "en": "Hotel description en",
        },
        highlights=["beachside", "family_friendly"],
        hotel_conversational_flow={
            "style": "concise_premium",
            "max_paragraph_lines": 3,
            "max_list_items": 5,
            "max_follow_up_questions": 2,
            "avoid_repeating_confirmed_facts": True,
            "summarize_large_price_lists": True,
            "ask_before_full_price_dump": True,
        },
        assistant={
            "menu_source_documents": [
                "https://www.kassandrarestaurant.com/alacarte.pdf",
                "https://www.kassandrarestaurant.com/wines.pdf",
                "https://www.kassandrarestaurant.com/snack.pdf",
            ],
            "menu_scope_prompt": "[RESTAURANT_MENU_STRICT_MODE] sadece menuden yanit ver [END_RESTAURANT_MENU_STRICT_MODE]",
        },
    )


def test_build_messages_includes_hotel_conversational_flow_rules() -> None:
    builder = PromptBuilder(
        hotel_profiles={21966: _build_profile()},
        escalation_matrix=[],
        template_library=[],
    )
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    messages = builder.build_messages(conversation, "2 ayrı oda istiyorum")
    system_contents = [str(item["content"]) for item in messages if item.get("role") == "system"]
    joined = "\n".join(system_contents)

    assert "HOTEL_CONVERSATIONAL_FLOW (STRICT)" in joined
    assert "Show at most 5 list items in one message." in joined
    assert "Ask at most 2 follow-up question(s) per turn." in joined
    assert "avoid_repeating_confirmed_facts=true" in joined
    assert "include every eligible and available room type suitable for the requested occupancy" in joined
    assert "keep the reply limited to that room type only" in joined
    assert "compact shortlist" not in joined


def test_build_system_prompt_is_compact_and_grounded() -> None:
    builder = PromptBuilder(
        hotel_profiles={21966: _build_profile()},
        escalation_matrix=[],
        template_library=[],
    )

    system_prompt = builder.build_system_prompt(21966)

    assert "VELox runtime core" in system_prompt
    assert "HOTEL_IDENTITY" in system_prompt
    assert "HOTEL_ADMIN_CONTEXT" in system_prompt
    assert "MENU_SOURCE_DOCUMENTS" in system_prompt
    assert "MENU_SCOPE_INSTRUCTION_STRICT" in system_prompt
    assert "alacarte.pdf" in system_prompt
    assert "ROOM_TYPES" in system_prompt
    assert "FAQ_CONTEXT" in system_prompt
    assert "faq_lookup" in system_prompt
    assert "SPECIAL OCCASIONS (STRICT)" in system_prompt
    assert "Birthday, honeymoon, anniversary, and marriage proposal requests are supported" in system_prompt
    assert "Never provide special-occasion pricing" in system_prompt
    assert "maps.app.goo.gl/pMiKmhV57YVvAghe6" in system_prompt
    assert "menu_preview" in system_prompt
    assert "Meyve Tabagi" in system_prompt
    assert "Standart check-in saatimiz 14:00 itibariyladir." not in system_prompt
    assert len(system_prompt) < 12000


def test_build_messages_falls_back_to_default_conversational_limits_when_profile_missing() -> None:
    builder = PromptBuilder(
        hotel_profiles={},
        escalation_matrix=[],
        template_library=[],
    )
    conversation = Conversation(hotel_id=99999, phone_hash="hash", language="tr")

    messages = builder.build_messages(conversation, "fiyat alabilir miyim")
    system_contents = [str(item["content"]) for item in messages if item.get("role") == "system"]
    joined = "\n".join(system_contents)

    assert "HOTEL_CONVERSATIONAL_FLOW (STRICT)" in joined
    assert "Each paragraph must be <= 3 lines." in joined
    assert "Show at most 5 list items in one message." in joined


def test_build_messages_includes_resolved_reply_context() -> None:
    builder = PromptBuilder(
        hotel_profiles={21966: _build_profile()},
        escalation_matrix=[],
        template_library=[],
    )
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    messages = builder.build_messages(
        conversation,
        "bunu istiyorum",
        reply_context={
            "present": True,
            "resolved": True,
            "target_role": "assistant",
            "target_content": "Deluxe: 180 EUR / Premium: 220 EUR. Hangisini tercih edersiniz?",
        },
    )
    system_contents = [str(item["content"]) for item in messages if item.get("role") == "system"]
    joined = "\n".join(system_contents)

    assert "REPLY_CONTEXT: The guest explicitly used WhatsApp reply-to for this turn." in joined
    assert "Replied target role: assistant" in joined
    assert "Deluxe: 180 EUR / Premium: 220 EUR." in joined


def test_build_messages_warns_when_reply_context_is_unresolved() -> None:
    builder = PromptBuilder(
        hotel_profiles={21966: _build_profile()},
        escalation_matrix=[],
        template_library=[],
    )
    conversation = Conversation(hotel_id=21966, phone_hash="hash", language="tr")

    messages = builder.build_messages(
        conversation,
        "evet",
        reply_context={"present": True, "resolved": False, "reason": "target_not_found"},
    )
    system_contents = [str(item["content"]) for item in messages if item.get("role") == "system"]
    joined = "\n".join(system_contents)

    assert "REPLY_CONTEXT: The guest used WhatsApp reply-to" in joined
    assert "do not over-assume the target" in joined
