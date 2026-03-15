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
