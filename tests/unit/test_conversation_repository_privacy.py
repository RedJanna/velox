"""Privacy tests for conversation transcript export helpers."""

from velox.db.repositories.conversation import ConversationRepository, _mask_phone_display


def test_mask_phone_display_redacts_long_numbers() -> None:
    """Transcript exports must not expose raw WhatsApp phone numbers."""
    assert _mask_phone_display("+90 530 123 45 67") == "905***67"


def test_transcript_filename_uses_masked_phone_label() -> None:
    """Chat Lab live import filenames should contain only the masked label."""
    filename = ConversationRepository._build_transcript_filename(
        "c76dbd8b-5cee-4f0d-8ad9-8499ccb36615",
        _mask_phone_display("+90 530 123 45 67"),
    )
    assert filename == "live_conv_c76dbd8b-5cee-4f0d-8ad9-8499ccb36615_905_67.json"
    assert "123" not in filename
    assert "4567" not in filename
