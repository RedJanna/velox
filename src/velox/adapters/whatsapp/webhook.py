"""WhatsApp webhook verification and payload parsing utilities."""

import hashlib
import hmac
from dataclasses import dataclass


@dataclass(slots=True)
class IncomingMessage:
    """Normalized incoming WhatsApp message."""

    message_id: str
    phone: str
    display_name: str
    text: str
    timestamp: int
    message_type: str
    phone_number_id: str | None = None
    display_phone_number: str | None = None


class WhatsAppWebhook:
    """WhatsApp webhook helper for verification and message extraction."""

    def __init__(self, verify_token: str, app_secret: str) -> None:
        self.verify_token = verify_token
        self.app_secret = app_secret

    def verify_subscription(self, mode: str, token: str, challenge: str) -> str | None:
        """Verify webhook subscription and return challenge when valid."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def validate_signature(self, payload: bytes, signature_header: str) -> bool:
        """Validate Meta X-Hub-Signature-256 signature."""
        if not self.app_secret or not signature_header:
            return False
        expected = hmac.new(self.app_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature_header)

    def parse_message(self, body: dict) -> IncomingMessage | None:
        """Extract first incoming user message from webhook payload."""
        entries = body.get("entry")
        if not isinstance(entries, list):
            return None

        for entry in entries:
            changes = entry.get("changes")
            if not isinstance(changes, list):
                continue

            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages")
                if not isinstance(messages, list) or not messages:
                    continue
                metadata = value.get("metadata", {})
                phone_number_id = None
                display_phone_number = None
                if isinstance(metadata, dict):
                    phone_number_id_raw = str(metadata.get("phone_number_id", "")).strip()
                    display_phone_raw = str(metadata.get("display_phone_number", "")).strip()
                    phone_number_id = phone_number_id_raw or None
                    display_phone_number = display_phone_raw or None

                contacts = value.get("contacts", [])
                display_name = ""
                if isinstance(contacts, list) and contacts:
                    profile = contacts[0].get("profile", {})
                    if isinstance(profile, dict):
                        display_name = str(profile.get("name", ""))

                for msg in messages:
                    parsed = self._parse_single_message(
                        msg,
                        display_name,
                        phone_number_id=phone_number_id,
                        display_phone_number=display_phone_number,
                    )
                    if parsed is not None:
                        return parsed
        return None

    def _parse_single_message(
        self,
        message: dict,
        display_name: str,
        *,
        phone_number_id: str | None = None,
        display_phone_number: str | None = None,
    ) -> IncomingMessage | None:
        """Normalize a single message object into IncomingMessage."""
        message_id = str(message.get("id", ""))
        phone = str(message.get("from", ""))
        message_type = str(message.get("type", "unknown"))

        try:
            timestamp = int(str(message.get("timestamp", "0")))
        except ValueError:
            timestamp = 0

        if not message_id or not phone:
            return None

        text = ""
        if message_type == "text":
            text = str(message.get("text", {}).get("body", ""))
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            reply_type = str(interactive.get("type", ""))
            if reply_type == "button_reply":
                reply = interactive.get("button_reply", {})
                text = str(reply.get("title") or reply.get("id") or "")
            elif reply_type == "list_reply":
                reply = interactive.get("list_reply", {})
                text = str(reply.get("title") or reply.get("id") or "")
        elif message_type == "reaction":
            reaction = message.get("reaction", {})
            emoji = str(reaction.get("emoji", "")).strip()
            text = emoji or "reaction"
        elif message_type == "location":
            location = message.get("location", {})
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            name = str(location.get("name", "")).strip()
            address = str(location.get("address", "")).strip()
            parts = [part for part in [name, address] if part]
            if latitude is not None and longitude is not None:
                parts.append(f"{latitude},{longitude}")
            text = " | ".join(parts) if parts else "location shared"
        elif message_type in {"image", "video", "audio", "document", "sticker"}:
            media = message.get(message_type, {})
            text = str(media.get("caption", "")).strip() or message_type
        else:
            text = message_type

        text = text.strip()
        return IncomingMessage(
            message_id=message_id,
            phone=phone,
            display_name=display_name,
            text=text,
            timestamp=timestamp,
            message_type=message_type,
            phone_number_id=phone_number_id,
            display_phone_number=display_phone_number,
        )
