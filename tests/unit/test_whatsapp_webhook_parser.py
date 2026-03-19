"""Unit tests for WhatsApp webhook payload parser metadata extraction."""

from velox.adapters.whatsapp.webhook import WhatsAppWebhook


def test_parse_message_extracts_destination_metadata() -> None:
    """Parser should include destination phone metadata for tenant routing."""
    webhook = WhatsAppWebhook(verify_token="token", app_secret="secret")  # noqa: S106
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "display_phone_number": "+90 555 123 45 67",
                                "phone_number_id": "123456789012345",
                            },
                            "contacts": [{"profile": {"name": "Guest User"}}],
                            "messages": [
                                {
                                    "id": "wamid.HBgM...",
                                    "from": "905551112233",
                                    "timestamp": "1710000000",
                                    "type": "text",
                                    "text": {"body": "Merhaba"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    parsed = webhook.parse_message(payload)
    assert parsed is not None
    assert parsed.phone_number_id == "123456789012345"
    assert parsed.display_phone_number == "+90 555 123 45 67"
    assert parsed.message_id == "wamid.HBgM..."
    assert parsed.phone == "905551112233"
    assert parsed.text == "Merhaba"


def test_parse_message_extracts_reply_context_metadata() -> None:
    """Parser should preserve reply-to metadata for downstream context resolution."""
    webhook = WhatsAppWebhook(verify_token="token", app_secret="secret")  # noqa: S106
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"profile": {"name": "Guest User"}}],
                            "messages": [
                                {
                                    "id": "wamid.reply.1",
                                    "from": "905551112233",
                                    "timestamp": "1710000001",
                                    "type": "text",
                                    "text": {"body": "bunu alalim"},
                                    "context": {
                                        "id": "wamid.previous.7",
                                        "from": "905559998877",
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    parsed = webhook.parse_message(payload)
    assert parsed is not None
    assert parsed.reply_to_message_id == "wamid.previous.7"
    assert parsed.reply_to_from == "905559998877"


def test_parse_status_events_extracts_failed_delivery_details() -> None:
    """Parser should capture status failure details for observability."""
    webhook = WhatsAppWebhook(verify_token="token", app_secret="secret")  # noqa: S106
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.gBGGSFc...",
                                    "status": "failed",
                                    "timestamp": "1710000100",
                                    "recipient_id": "905551112233",
                                    "errors": [
                                        {
                                            "code": 131047,
                                            "title": "Re-engagement message",
                                            "details": "Message failed because more than 24 hours have passed.",
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    events = webhook.parse_status_events(payload)
    assert len(events) == 1
    event = events[0]
    assert event.message_id == "wamid.gBGGSFc..."
    assert event.status == "failed"
    assert event.recipient_id == "905551112233"
    assert event.timestamp == 1710000100
    assert event.error_code == 131047
    assert event.error_title == "Re-engagement message"
