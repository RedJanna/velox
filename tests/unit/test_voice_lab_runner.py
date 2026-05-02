"""Unit tests for the AI telesekreter Voice Lab runner."""

from velox.models.hotel_profile import HotelProfile
from velox.voice_lab import VoiceLabAction, VoiceLabResult, VoiceLabRunner, VoiceLabSource


def test_voice_lab_matrix_passes_baseline_scenarios(hotel_profile: HotelProfile) -> None:
    """The initial V001-V018 matrix should be runnable without external services."""
    runner = VoiceLabRunner(hotel_profile)

    results = runner.run_matrix()

    assert len(results) == 18
    assert all(result.result == VoiceLabResult.PASS for result in results), [
        (result.scenario_id, result.violations) for result in results if result.result != VoiceLabResult.PASS
    ]


def test_price_request_requires_booking_quote_tool(hotel_profile: HotelProfile) -> None:
    """Quote requests must not produce fabricated prices in Voice Lab."""
    runner = VoiceLabRunner(hotel_profile)

    result = runner.run_text(
        "3 Mayis ile 5 Mayis tarihleri arasinda iki yetiskin icin fiyat bilgisi alabilir miyim?",
        scenario_id="V001",
    )

    assert result.result == VoiceLabResult.PASS
    assert result.source_type == VoiceLabSource.TOOL
    assert result.action == VoiceLabAction.TOOL_REQUIRED
    assert result.tool_required is True
    assert result.tool_called is False
    assert result.tool_name == "booking.quote"
    assert "75 EUR" not in result.response_text


def test_parking_answer_uses_hotel_profile_without_short_negative(hotel_profile: HotelProfile) -> None:
    """Parking answer should use the detailed HOTEL_PROFILE FAQ response."""
    runner = VoiceLabRunner(hotel_profile)

    result = runner.run_text("Otelinizde otopark var mi?", scenario_id="V011")

    assert result.result == VoiceLabResult.PASS
    assert result.source_type == VoiceLabSource.HOTEL_PROFILE
    assert result.source_detail == "HOTEL_PROFILE.faq_data.parking"
    assert "otopark yok" not in result.response_text.casefold()
    assert "otopark" in result.response_text.casefold()


def test_oludeniz_beach_character_comes_from_faq(hotel_profile: HotelProfile) -> None:
    """Oludeniz beach character answer should include both beach areas."""
    runner = VoiceLabRunner(hotel_profile)

    result = runner.run_text("Oludeniz tasli mi, derin mi?", scenario_id="V018")

    assert result.result == VoiceLabResult.PASS
    assert result.source_detail == "HOTEL_PROFILE.faq_data.oludeniz_beach_character"
    assert "Belcekiz" in result.response_text
    assert "Kumburnu" in result.response_text


def test_payment_installment_is_handoff_without_card_collection(hotel_profile: HotelProfile) -> None:
    """Installment/card questions should be handed off and must not request card data."""
    runner = VoiceLabRunner(hotel_profile)

    result = runner.run_text("Kredi karti icin taksitlendirme uyguluyor musunuz?", scenario_id="V009")

    assert result.result == VoiceLabResult.PASS
    assert result.source_type == VoiceLabSource.HANDOFF
    assert result.handoff_required is True
    assert "PAYMENT_CONFUSION" in result.risk_flags
    assert "cvv" not in result.response_text.casefold()
    assert "kart numaranizi" not in result.response_text.casefold()


def test_card_like_input_is_redacted_and_blocked(hotel_profile: HotelProfile) -> None:
    """Voice Lab should not retain card-like strings in run output."""
    runner = VoiceLabRunner(hotel_profile)

    result = runner.run_text("Kart numaram 4111 1111 1111 1111, odeme alir misiniz?")

    assert result.result == VoiceLabResult.BLOCKED
    assert result.handoff_required is True
    assert "[REDACTED_CARD]" in result.input_transcript
    assert "4111 1111 1111 1111" not in result.input_transcript
    assert "PII_OVERREQUEST" in result.risk_flags


def test_reservation_lookup_requires_pms_tool(hotel_profile: HotelProfile) -> None:
    """Reservation lookups must not claim existence without PMS/tool evidence."""
    runner = VoiceLabRunner(hotel_profile)

    result = runner.run_text(
        "12345678 nolu rezervasyonu kontrol edebilir misiniz? Sisteminizde goruluyor mu?",
        scenario_id="V017",
    )

    assert result.result == VoiceLabResult.PASS
    assert result.source_type == VoiceLabSource.TOOL
    assert result.tool_name == "booking.get_reservation"
    assert "goruluyor" not in result.response_text.casefold()
    assert "gorulmuyor" not in result.response_text.casefold()
