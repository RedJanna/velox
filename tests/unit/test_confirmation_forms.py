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

    assert "KONAKLAMA REZERVASYON ONAY FORMU" in preview.html
    assert "linework" in preview.html
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
    assert "form-grid" in preview.html
    assert "decor-map" in preview.html
    assert "R-HOLD-1" in preview.whatsapp_message


def test_restaurant_confirmation_uses_prompt_specific_fields() -> None:
    context = build_context_from_manual_payload(
        form_type="restaurant",
        hotel_id=21966,
        language="en",
        payload={
            "confirmation_no": "REST-42",
            "customer": {"guest_name": "Ada Stone", "phone": "+447700900123"},
            "details": {
                "date": "2026-06-12",
                "time": "19:30",
                "party_size": "2",
                "area": "Outdoor",
                "table": "Terrace front",
                "occasion": "Anniversary",
                "notes": "Quiet table",
            },
        },
        generated_at=datetime(2026, 4, 29, 10, 30, tzinfo=UTC),
    )

    preview = build_preview(context)

    assert "RESTAURANT RESERVATION CONFIRMATION FORM" in preview.html
    assert "Indoor" in preview.html
    assert "Outdoor Preference" in preview.html
    assert "Table Type" in preview.html
    assert "Seating Preference" in preview.html
    assert "Occasion" in preview.html
    assert "Authorized Confirmation" in preview.html


def test_transfer_confirmation_uses_prompt_specific_fields() -> None:
    context = build_context_from_manual_payload(
        form_type="transfer",
        hotel_id=21966,
        language="tr",
        payload={
            "confirmation_no": "TRF-77",
            "customer": {"guest_name": "Deneme Misafir", "phone": "+905301234567"},
            "details": {
                "transfer_type": "Airport transfer",
                "pickup_location": "Dalaman Airport",
                "dropoff_location": "Kassandra Ölüdeniz",
                "date": "2026-05-18",
                "time": "14:00",
                "pax": "3",
                "vehicle": "VIP Van",
                "flight_no": "TK1234",
            },
        },
        generated_at=datetime(2026, 4, 29, 10, 30, tzinfo=UTC),
    )

    preview = build_preview(context)

    assert "TRANSFER REZERVASYON ONAY FORMU" in preview.html
    assert "Transfer reservation confirmation details" in preview.html
    assert "Alış Noktası" in preview.html
    assert "Pick-up Location" in preview.html
    assert "Bırakış Noktası" in preview.html
    assert "Drop-off Location" in preview.html
    assert "motif-transfer" in preview.html


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
