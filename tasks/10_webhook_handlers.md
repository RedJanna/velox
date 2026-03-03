# Task 10: Webhook Handlers (Approval + Payment Events)

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/error_handling.md`
> - `skills/security_privacy.md`

## Objective
Implement backend webhook endpoints that receive approval decisions and payment status updates from the admin panel, then push "system events" into the relevant conversation for LLM processing.

## Reference
- `docs/master_prompt_v2.md` — A10 (Webhook Assumption), A9.4 (Operational Flow), B6 (Webhooks)
- `src/velox/models/webhook_events.py` — ApprovalEvent, PaymentEvent, TransferEvent

## Files to Create/Modify

### 1. `src/velox/api/routes/admin_webhook.py`

```python
router = APIRouter(prefix="/webhook", tags=["admin-webhooks"])

@router.post("/approval")
async def approval_webhook(event: ApprovalEvent, request: Request):
    """
    Called when admin approves/rejects a hold from the admin panel.
    Flow:
    1. Validate webhook signature (shared secret)
    2. Find approval_request by approval_request_id
    3. Update approval_request status (APPROVED/REJECTED)
    4. Update the referenced hold status
    5. If APPROVED:
       a. For STAY: backend calls booking.create_reservation via Elektraweb
       b. For RESTAURANT: update hold to CONFIRMED
       c. For TRANSFER: update hold to CONFIRMED
       d. Trigger payment flow if applicable (A9.2 rules)
    6. Push system event into conversation
    7. LLM processes event and sends user notification
    """

@router.post("/payment")
async def payment_webhook(event: PaymentEvent, request: Request):
    """
    Called when admin marks payment as PAID/FAILED/EXPIRED.
    Flow:
    1. Validate webhook signature
    2. Find payment_request by payment_request_id
    3. Update payment_request status
    4. If PAID: update hold/reservation to final CONFIRMED state
    5. If FAILED/EXPIRED: notify user, offer alternatives
    6. Push system event into conversation
    """

@router.post("/transfer")
async def transfer_webhook(event: TransferEvent, request: Request):
    """Similar flow for transfer confirmations."""
```

### 2. System Event Processing

Create `src/velox/core/event_processor.py`:

```python
class EventProcessor:
    async def process_approval_event(self, event: ApprovalEvent) -> None:
        """Process approval decision and continue conversation."""
        # 1. Load conversation linked to the hold
        # 2. Append system message to conversation:
        #    {"role": "system", "content": "SYSTEM_EVENT: approval.updated ..."}
        # 3. Trigger LLM to generate response for user
        # 4. Send WhatsApp message to user

    async def process_payment_event(self, event: PaymentEvent) -> None:
        """Process payment status and continue conversation."""
        # Similar flow

    async def inject_system_event(self, conversation_id: UUID, event_data: dict) -> None:
        """Inject a system event into conversation and trigger LLM."""
```

### 3. Post-Approval Actions

For STAY approval flow (A9.4):
```
Admin approves -> approval_webhook receives event
  |
  v
Backend calls booking.create_reservation via Elektraweb
  |
  v
If NON_REFUNDABLE:
  -> payment.request_prepayment(due_mode=NOW)
  -> notify SALES
  -> User message: "Rezervasyonunuz onaylandi! On odeme sureci icin satis ekibimiz sizinle iletisime gececek."

If FREE_CANCEL:
  -> payment.request_prepayment(due_mode=SCHEDULED, scheduled_date=checkin-7)
  -> notify SALES
  -> User message: "Rezervasyonunuz onaylandi! Check-in tarihinizden 7 gun once satis ekibimiz odeme detaylari icin sizinle iletisime gececek."
```

### 4. Webhook Security

```python
def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate HMAC-SHA256 webhook signature from admin panel."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Expected Outcome
- Admin approval decisions flow through to conversation
- Payment status updates trigger appropriate user notifications
- Post-approval actions (Elektraweb booking, payment requests) execute automatically
- Webhook signatures are validated
- System events are properly logged in message history
