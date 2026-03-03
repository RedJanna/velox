# Task 05: WhatsApp Integration (Meta Business API)

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/error_handling.md`
> - `skills/security_privacy.md`
> - `skills/whatsapp_format.md`

## Objective
Implement the WhatsApp adapter layer: sending messages, receiving webhooks, signature verification, and message formatting.

## Reference
- `docs/master_prompt_v2.md` — A3 (WhatsApp format), B4 (Meta Business API)
- `src/velox/config/settings.py` — WhatsApp env vars
- Meta Cloud API docs: https://developers.facebook.com/docs/whatsapp/cloud-api

## Files to Create/Modify

### 1. `src/velox/adapters/whatsapp/client.py`

WhatsApp Cloud API client for sending messages.

```python
class WhatsAppClient:
    """Meta WhatsApp Business Cloud API client."""

    def __init__(self, settings):
        self.base_url = f"{settings.whatsapp_api_base_url}/{settings.whatsapp_api_version}"
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        # Use httpx.AsyncClient

    async def send_text_message(self, to: str, body: str) -> dict:
        """Send a plain text message."""
        # POST /{phone_number_id}/messages
        # Body: {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
        # Max body length: 4096 chars — truncate if needed

    async def send_template_message(self, to: str, template_name: str, language: str, components: list) -> dict:
        """Send a template message (for first contact / 24h window reopening)."""

    async def mark_as_read(self, message_id: str) -> None:
        """Mark incoming message as read (blue checkmarks)."""
        # POST /{phone_number_id}/messages
        # Body: {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
```

### 2. `src/velox/adapters/whatsapp/webhook.py`

Webhook verification and message parsing.

```python
import hmac
import hashlib

class WhatsAppWebhook:
    def __init__(self, verify_token: str, app_secret: str):
        self.verify_token = verify_token
        self.app_secret = app_secret

    def verify_subscription(self, mode: str, token: str, challenge: str) -> str | None:
        """Verify webhook subscription. Returns challenge if valid, None if invalid."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def validate_signature(self, payload: bytes, signature_header: str) -> bool:
        """Validate X-Hub-Signature-256 header."""
        expected = hmac.new(self.app_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature_header)

    def parse_message(self, body: dict) -> IncomingMessage | None:
        """Extract message from webhook payload."""
        # Navigate: body.entry[0].changes[0].value.messages[0]
        # Extract: from (phone), text.body, id, timestamp, type
        # Handle: text, interactive (button/list replies), reaction, location
        # Return None if no message (status updates, etc.)
```

Data class:
```python
@dataclass
class IncomingMessage:
    message_id: str
    phone: str           # Sender phone (e.g. "905332503277")
    display_name: str    # WhatsApp display name
    text: str            # Message text
    timestamp: int       # Unix timestamp
    message_type: str    # "text", "interactive", "image", etc.
```

### 3. `src/velox/adapters/whatsapp/formatter.py`

Format messages for WhatsApp display.

```python
class WhatsAppFormatter:
    MAX_LENGTH = 4096

    @staticmethod
    def format_options(options: list[str]) -> str:
        """Format numbered options list."""
        # 1. Option A
        # 2. Option B

    @staticmethod
    def bold(text: str) -> str:
        return f"*{text}*"

    @staticmethod
    def italic(text: str) -> str:
        return f"_{text}_"

    @staticmethod
    def truncate(text: str, max_len: int = 4096) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
```

### 4. `src/velox/api/routes/whatsapp_webhook.py`

FastAPI route handlers.

```python
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """Meta webhook verification endpoint."""

@router.post("")
async def receive_message(request: Request):
    """Handle incoming WhatsApp messages."""
    # 1. Validate signature
    # 2. Parse message
    # 3. Rate limit check (phone-based)
    # 4. Load/create conversation
    # 5. Process message through LLM pipeline
    # 6. Send reply via WhatsApp client
    # 7. Log to DB
    # Return 200 immediately (async processing)
```

## Important Notes
- Always return HTTP 200 to Meta quickly (within 5s) to avoid retries
- Process heavy logic in background task (FastAPI BackgroundTasks)
- Phone numbers come without `+` prefix from Meta (e.g. "905332503277")
- Handle deduplication: Meta may send the same webhook multiple times
- Status webhooks (delivered, read) should be acknowledged but not processed as messages

## Expected Outcome
- Webhook verification works with Meta
- Incoming text messages are parsed correctly
- Replies are sent via Cloud API
- Signature validation prevents tampering
- Message deduplication prevents double processing
