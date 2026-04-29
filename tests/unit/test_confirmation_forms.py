"""Unit tests for reservation confirmation form generation."""

from datetime import UTC, datetime

from velox.core.confirmation_forms import (
    COPY,
    build_context_from_manual_payload,
    build_preview,
    hash_public_token,
    mark_confirmation_sent,
    token_is_valid,
)


def test_accommodation_confirmation_preview_uses_customer_language_and_masks_phone() -> None:
    context = build_context_from_manual_payload(
        form_type="accommodation",
        hotel_id=21966,
        language="tr",
        payload={
            "confirmation_no": "VLX-2026-0418",
            "customer": {"guest_name": "John Carter", "phone": "+905301234567"},
            "details": {
                "checkin_date": "2026-05-18",
                "checkout_date": "2026-05-22",
                "room": "Premium Room",
                "guests": "2 yetişkin",
                "total": "840 EUR",
            },
        },
        generated_at=datetime(2026, 4, 29, 10, 30, tzinfo=UTC),
    )

    preview = build_preview(context)

    assert "Rezervasyon Onaylandı" in preview.html
    assert "+90 *** *** 4567" in preview.html
    assert "VLX-2026-0418" in preview.html
    assert "Güvenli onay formunuzu buradan görüntüleyebilirsiniz" in preview.whatsapp_message


def test_restaurant_confirmation_preview_supports_active_language() -> None:
    context = build_context_from_manual_payload(
        form_type="restaurant",
        hotel_id=21966,
        language="de",
        payload={
            "confirmation_no": "R-HOLD-1",
            "customer": {"guest_name": "Maria Klein", "phone": "+491701234567"},
            "details": {
                "date": "2026-06-02",
                "time": "20:00",
                "party_size": "4",
                "area": "Terrace",
            },
        },
        generated_at=datetime(2026, 4, 29, 10, 30, tzinfo=UTC),
    )

    preview = build_preview(context)

    assert "Reservierung bestätigt" in preview.html
    assert "Restaurantdetails" in preview.html
    assert "R-HOLD-1" in preview.whatsapp_message


def test_public_token_validation_and_hashing_are_deterministic() -> None:
    sample_public_id = "abcDEF_123-xyzABC_456-xyzABC_789"

    assert token_is_valid(sample_public_id)
    assert not token_is_valid("../bad-token")
    assert hash_public_token(sample_public_id) == hash_public_token(sample_public_id)
    assert hash_public_token(sample_public_id) != sample_public_id


def test_supported_language_copy_is_complete() -> None:
    required_keys = set(COPY["en"])

    for language, labels in COPY.items():
        assert set(labels) == required_keys, language


async def test_mark_confirmation_sent_uses_explicit_parameter_types() -> None:
    class FakeConnection:
        query = ""
        args: tuple[object, ...] = ()

        async def execute(self, query: str, *args: object) -> None:
            self.query = query
            self.args = args

    conn = FakeConnection()

    await mark_confirmation_sent(  # type: ignore[arg-type]
        conn,
        form_id="00000000-0000-0000-0000-000000000001",
        whatsapp_message_id=None,
        delivered=False,
    )

    assert "$2::varchar" in conn.query
    assert "$3::varchar" in conn.query
    assert "$4::bool" in conn.query
    assert conn.args == ("00000000-0000-0000-0000-000000000001", "DELIVERY_FAILED", None, False)
