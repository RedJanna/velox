"""Unit tests for reservation confirmation form generation."""

from datetime import UTC, datetime

import pytest

from velox.core.confirmation_forms import (
    COPY,
    build_context_from_manual_payload,
    build_preview,
    hash_public_token,
    mark_confirmation_sent,
    token_is_valid,
)
from velox.core.hotel_profile_loader import load_all_profiles


@pytest.fixture(autouse=True)
def loaded_hotel_profiles() -> None:
    """Mirror app startup so confirmation previews use profile-backed branding."""
    load_all_profiles()


def test_accommodation_confirmation_preview_uses_customer_language_and_displays_contact_details() -> None:
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
    assert "Kassandra Ölüdeniz" in preview.html
    assert "Kassandra Oludeniz" not in preview.html
    assert "+905301234567" in preview.html
    assert "+90 *** *** 4567" not in preview.html
    assert "VLX-2026-0418" in preview.html
    assert "Güvenli onay formunuzu buradan görüntüleyebilirsiniz" in preview.whatsapp_message


def test_manual_preview_renders_blank_line_template_without_required_fields() -> None:
    context = build_context_from_manual_payload(
        form_type="accommodation",
        hotel_id=21966,
        language="tr",
        payload={"customer": {}, "details": {}},
        generated_at=datetime(2026, 4, 29, 10, 30, tzinfo=UTC),
    )

    preview = build_preview(context)

    assert "KONAKLAMA REZERVASYON ONAY FORMU" in preview.html
    assert "document-section section-customer" in preview.html
    assert "Misafir Adı" in preview.html
    assert "E-posta" in preview.html
    assert "Rezervasyon Numarası" in preview.html
    assert 'line-value">&nbsp;</span>' in preview.html


def test_confirmation_templates_share_language_but_have_type_specific_designs() -> None:
    html_by_type = {}
    for form_type in ("accommodation", "restaurant", "transfer"):
        context = build_context_from_manual_payload(
            form_type=form_type,
            hotel_id=21966,
            language="tr",
            payload={"customer": {}, "details": {}},
            generated_at=datetime(2026, 4, 29, 10, 30, tzinfo=UTC),
        )
        html_by_type[form_type] = build_preview(context).html

    assert "template-accommodation-ledger" in html_by_type["accommodation"]
    assert "template-restaurant-table" in html_by_type["restaurant"]
    assert "template-transfer-route" in html_by_type["transfer"]
    assert "ornament-accommodation" in html_by_type["accommodation"]
    assert "ornament-restaurant" in html_by_type["restaurant"]
    assert "ornament-transfer" in html_by_type["transfer"]
    assert all("brand-lockup" in html and "section-heading" in html for html in html_by_type.values())
    assert all("Kassandra Ölüdeniz" in html for html in html_by_type.values())
    assert all("#192f9a" in html and "Aviano Sans" in html for html in html_by_type.values())


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
    assert "document-body" in preview.html
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
    assert "Transfer rezervasyon onay detayları" in preview.html
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
