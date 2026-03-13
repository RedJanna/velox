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
        hotel_conversational_flow={
            "style": "concise_premium",
            "max_paragraph_lines": 3,
            "max_list_items": 5,
            "max_follow_up_questions": 2,
            "avoid_repeating_confirmed_facts": True,
            "summarize_large_price_lists": True,
            "ask_before_full_price_dump": True,
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
