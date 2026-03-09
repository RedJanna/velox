"""Integration tests for WhatsApp webhook routes."""

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from velox.adapters.whatsapp.webhook import IncomingMessage
from velox.api.routes import whatsapp_webhook


@pytest.fixture
def webhook_client(reset_whatsapp_webhook_state: None) -> TestClient:
    """Build lightweight app exposing only whatsapp webhook routes."""
    app = FastAPI()
    app.include_router(whatsapp_webhook.router, prefix="/api/v1")
    app.state.tool_dispatcher = None
    app.state.escalation_engine = None
    app.state.db_pool = None
    return TestClient(app)


def test_get_verification_correct_and_incorrect_tokens(
    webhook_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET verify endpoint should return challenge only for matching token."""
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "verify_token", "verify-123")
    ok = webhook_client.get(
        "/api/v1/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-123", "hub.challenge": "abc"},
    )
    bad = webhook_client.get(
        "/api/v1/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "abc"},
    )
    assert ok.status_code == 200
    assert ok.text == "abc"
    assert bad.status_code == 403


def test_post_with_valid_signature_message_accepted(
    webhook_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid signature and parsed message should return accepted status."""
    incoming = IncomingMessage(
        message_id="m-accepted",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=1710000000,
        message_type="text",
    )
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", lambda *_: incoming)
    monkeypatch.setattr(whatsapp_webhook, "_schedule_background_task", lambda *args, **kwargs: None)
    response = webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


def test_post_with_invalid_signature_returns_403(
    webhook_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid signature should be rejected before payload processing."""
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: False)
    response = webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": []},
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 403


def test_status_update_payload_returns_ok_without_processing(
    webhook_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Status payloads (no user message) should return ok."""
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", lambda *_: None)
    response = webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_deduplication_of_repeated_webhooks(
    webhook_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated webhook with same message id should be ignored on second call."""
    incoming = IncomingMessage(
        message_id="m-dedupe-1",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=1710000000,
        message_type="text",
    )

    def _parse(_: dict[str, Any]) -> IncomingMessage:
        return incoming

    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "validate_signature", lambda *_: True)
    monkeypatch.setattr(whatsapp_webhook.webhook_handler, "parse_message", _parse)
    monkeypatch.setattr(whatsapp_webhook, "_schedule_background_task", lambda *args, **kwargs: None)

    first = webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    second = webhook_client.post(
        "/api/v1/webhook/whatsapp",
        json={"entry": [{"changes": [{"value": {}}]}]},
        headers={"X-Hub-Signature-256": "sha256=test"},
    )
    assert first.status_code == 200
    assert first.json() == {"status": "accepted"}
    assert second.status_code == 200
    assert second.json() == {"status": "ok"}


def test_child_quote_mismatch_creates_manual_verification_response() -> None:
    """Child occupancy mismatch should force manual quote verification."""
    executed_calls = [
        {
            "name": "booking_quote",
            "arguments": '{"checkin_date":"2026-08-03","checkout_date":"2026-08-04","adults":2,"chd_count":1,"chd_ages":[7],"currency":"EUR"}',
            "result": '{"error":"CHILD_OCCUPANCY_UNVERIFIED: PMS quote did not reflect requested child occupancy.","tool":"booking_quote"}',
        }
    ]
    response = whatsapp_webhook._build_child_quote_handoff_response(executed_calls)
    assert response.internal_json.state == "HANDOFF"
    assert response.internal_json.entities["chd_count"] == 1
    assert "Çocuklu konaklamalarda" in response.user_message


def test_quote_notes_only_added_when_booking_quote_was_executed() -> None:
    """Policy notes should not be appended to non-price follow-up messages."""
    no_quote_calls = [{"name": "faq_lookup"}]
    with_quote_calls = [{"name": "booking_quote"}]

    assert whatsapp_webhook._executed_booking_quote(no_quote_calls) is False
    assert whatsapp_webhook._executed_booking_quote(with_quote_calls) is True


def test_child_bedding_reply_uses_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two-child bedding replies should not claim a single extra bed."""
    profile = SimpleNamespace(
        facility_policies={
            "children": {
                "bedding_note_tr": (
                    "2 çocuklu konaklamalarda oda tipine ve uygunluğa göre 2 ek yatak "
                    "veya 1 ek yatak + 1 sofa hazırlanabilir."
                )
            }
        },
        room_types=[
            SimpleNamespace(name=SimpleNamespace(tr="Deluxe"), max_pax=3, extra_bed=True),
            SimpleNamespace(name=SimpleNamespace(tr="Premium"), max_pax=4, extra_bed=True),
            SimpleNamespace(name=SimpleNamespace(tr="Penthouse"), max_pax=4, extra_bed=True),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_turkish_child_bedding_reply(
        21966,
        {"adults": 2, "chd_count": 2},
    )

    assert "tek ek yatak bilgisi doğru değildir" in reply
    assert "2 ek yatak veya 1 ek yatak + 1 sofa" in reply
    assert "**Premium**" in reply
    assert "**Penthouse**" in reply


def test_parking_reply_uses_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parking questions should use the exact profile-driven parking reply."""
    profile = SimpleNamespace(
        facility_policies={
            "parking": {
                "reply_tr": (
                    "Aracınız için park yeri ayarlayabiliriz. Ücretsiz cadde park yerleri "
                    "mevcuttur, ayrıca otelin karşısında özel bir otopark da bulunmaktadır. "
                    "Varışınızda sizi park alanına yönlendireceğiz."
                )
            }
        }
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_turkish_parking_reply(21966)

    assert "Ücretsiz cadde park yerleri" in reply
    assert "Varışınızda sizi park alanına yönlendireceğiz." in reply


def test_payment_reply_uses_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Payment-method questions should use the exact profile-driven payment reply."""
    profile = SimpleNamespace(
        model_dump=lambda: {
            "payment": {
                "reply_tr": (
                    "Evet, kredi kartı dışında nakit ve havale kabul ediyoruz. "
                    "İsterseniz rezervasyon aşamasında size uygun ödeme yöntemini "
                    "birlikte netleştirebiliriz."
                )
            }
        }
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_turkish_payment_methods_reply(21966)

    assert "nakit ve havale kabul ediyoruz" in reply


def test_elevator_reply_uses_profile_policy_for_russian(monkeypatch: pytest.MonkeyPatch) -> None:
    """Elevator questions should use profile-driven accessibility policy."""
    profile = SimpleNamespace(
        facility_policies={
            "accessibility": {
                "elevator_available": False,
                "reply_ru": "В нашем отеле лифта нет. На первом этаже есть доступные варианты номеров.",
            }
        }
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)

    reply = whatsapp_webhook._build_elevator_reply(21966, "ru")

    assert "лифта нет" in reply


def test_elevator_detection_matches_russian_and_turkish() -> None:
    """Elevator detector should catch both Russian and Turkish variants."""
    assert whatsapp_webhook._is_elevator_question("В вашем отеле есть лифт?") is True
    assert whatsapp_webhook._is_elevator_question("Otelde asansör var mı?") is True


def test_parking_detection_does_not_match_havale() -> None:
    """Parking detection must not confuse 'havale' with 'vale'."""
    assert whatsapp_webhook._is_parking_question("Kredi kartı dışında havale kabul ediyor musunuz?") is False
    assert whatsapp_webhook._is_payment_method_question("Kredi kartı dışında havale kabul ediyor musunuz?") is True


def test_deterministic_turkish_quote_reply_uses_live_rate_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stay quote replies should be built from live FREE_CANCEL/NON_REFUNDABLE offers only."""
    profile = SimpleNamespace(
        rate_mapping={
            "FREE_CANCEL": SimpleNamespace(rate_type_id=24178),
            "NON_REFUNDABLE": SimpleNamespace(rate_type_id=24171),
        },
        room_types=[
            SimpleNamespace(
                pms_room_type_id=396094,
                name=SimpleNamespace(tr="Deluxe"),
                size_m2=25,
            ),
            SimpleNamespace(
                pms_room_type_id=396097,
                name=SimpleNamespace(tr="Superior"),
                size_m2=30,
            ),
            SimpleNamespace(
                pms_room_type_id=397738,
                name=SimpleNamespace(tr="Exclusive Land"),
                size_m2=40,
            ),
        ],
    )
    monkeypatch.setattr(whatsapp_webhook, "get_profile", lambda _hotel_id: profile)
    executed_calls = [
        {
            "name": "booking_quote",
            "result": (
                '{"offers":['
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24169,"rate_type":"Kontrat","price":"710","discounted_price":"497","currency_code":"EUR","room_area":25,"cancel_possible":false},'
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"710","discounted_price":"496.9","currency_code":"EUR","room_area":25,"cancel_possible":false},'
                '{"room_type_id":396094,"room_type":"DELUXE","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"781","discounted_price":"546.7","currency_code":"EUR","room_area":25,"cancel_possible":true},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"729","discounted_price":"510.3","currency_code":"EUR","room_area":30,"cancel_possible":false},'
                '{"room_type_id":396097,"room_type":"SUPERIOR","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"801.9","discounted_price":"561.3","currency_code":"EUR","room_area":30,"cancel_possible":true},'
                '{"room_type_id":397738,"room_type":"EXCLUSIVE LAND","rate_type_id":24171,"rate_type":"İptal Edilemez","price":"748","discounted_price":"523.6","currency_code":"EUR","room_area":40,"cancel_possible":false},'
                '{"room_type_id":397738,"room_type":"EXCLUSIVE LAND","rate_type_id":24178,"rate_type":"Ücretsiz İptal","price":"822.8","discounted_price":"575.9","currency_code":"EUR","room_area":40,"cancel_possible":true}'
                ']}'
            ),
        }
    ]

    reply = whatsapp_webhook._build_deterministic_turkish_stay_quote_reply(21966, executed_calls)

    assert reply is not None
    assert "Deluxe (25m2)" in reply
    assert "İptal edilemez: 495 €" in reply
    assert "Ücretsiz İptal: 545 €" in reply
    assert "Superior (30m2)" in reply
    assert "Exclusive Sokak Manzaralı (40m2)" in reply
    assert "Kontrat" not in reply


def test_normalized_turkish_quote_reply_keeps_notes_single() -> None:
    """Deterministic quote text should receive the required notes exactly once."""
    reply = whatsapp_webhook._normalize_turkish_stay_quote_reply(
        "Deluxe (25m2)\nİptal edilemez: 495 €\nÜcretsiz İptal: 545 €",
        "3 Ağustos ile 5 Ağustos arasında 1 yetişkin + 1 çocuk (8 yaş) için fiyat alabilir miyim?",
    )

    assert reply.count(whatsapp_webhook.TR_FREE_CANCEL_NOTE) == 1
    assert reply.count(whatsapp_webhook.TR_NON_REFUNDABLE_NOTE) == 1
    assert reply.count(whatsapp_webhook.TR_ROOM_NUMBER_NOTE) == 1
