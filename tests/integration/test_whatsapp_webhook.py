"""Integration tests for WhatsApp webhook routes."""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

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
    assert ok.json() == "abc"
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
