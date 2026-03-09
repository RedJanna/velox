"""Unit tests for FAQ lookup matching."""

import pytest

from velox.models.hotel_profile import HotelProfile
from velox.tools.faq import FAQLookupTool


def _build_profile() -> HotelProfile:
    """Create a minimal hotel profile for FAQ lookup tests."""
    return HotelProfile.model_validate(
        {
            "hotel_id": 21966,
            "hotel_name": {"tr": "Kassandra Oludeniz", "en": "Kassandra Oludeniz"},
            "faq_data": [
                {
                    "topic": "spa_hamam",
                    "question_tr": "Spa, hamam veya sauna var mi?",
                    "question_en": "Do you have a spa or sauna?",
                    "question_variants_tr": ["Hamam var mi?", "Spa mevcut mu?"],
                    "question_variants_en": ["Do you have spa?", "Is there a Turkish bath?"],
                    "answer_tr": "Spa, hamam ve sauna bulunmamaktadir.",
                    "answer_en": "There is no spa, Turkish bath, or sauna.",
                },
                {
                    "topic": "late_arrival",
                    "question_tr": "Gec varis yaparsam ne olmali?",
                    "question_en": "What if I arrive late?",
                    "answer_tr": "Gece yarisindan sonraki varislar icin onceden bilgi veriniz.",
                    "answer_en": "Please inform us in advance for arrivals after midnight.",
                },
            ],
        }
    )


@pytest.mark.asyncio
async def test_faq_lookup_matches_turkish_question_variant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Turkish question variants should produce direct FAQ matches."""
    monkeypatch.setattr("velox.tools.faq.get_profile", lambda _hotel_id: _build_profile())

    result = await FAQLookupTool().execute(
        hotel_id=21966,
        query="Hamam var mı?",
        language="TR",
    )

    assert result["found"] is True
    assert result["topic"] == "spa_hamam"
    assert result["answer"] == "Spa, hamam ve sauna bulunmamaktadir."
    assert result["match_score"] == 1.0


@pytest.mark.asyncio
async def test_faq_lookup_matches_english_question_variant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """English question variants should be matched before answer fallback."""
    monkeypatch.setattr("velox.tools.faq.get_profile", lambda _hotel_id: _build_profile())

    result = await FAQLookupTool().execute(
        hotel_id=21966,
        query="Is there a Turkish bath?",
        language="EN",
    )

    assert result["found"] is True
    assert result["topic"] == "spa_hamam"
    assert result["answer"] == "There is no spa, Turkish bath, or sauna."
    assert result["match_score"] == 1.0


@pytest.mark.asyncio
async def test_faq_lookup_preserves_existing_question_matching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entries without variants should still match their base question text."""
    monkeypatch.setattr("velox.tools.faq.get_profile", lambda _hotel_id: _build_profile())

    result = await FAQLookupTool().execute(
        hotel_id=21966,
        query="What if I arrive late?",
        language="EN",
    )

    assert result["found"] is True
    assert result["topic"] == "late_arrival"
    assert result["answer"] == "Please inform us in advance for arrivals after midnight."
