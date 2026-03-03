# Task 07: Tool Implementations

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/error_handling.md`
> - `skills/security_privacy.md`

## Objective
Implement all tool functions that the LLM calls via function calling. Each tool is a self-contained module that interacts with adapters, DB, or config.

## Reference
- `docs/master_prompt_v2.md` — A8.1-A8.5 (full tool contracts)
- `src/velox/models/` — All Pydantic models
- `src/velox/adapters/` — Elektraweb + WhatsApp adapters
- `src/velox/db/repositories/` — DB repositories

## Files to Create

### 1. `src/velox/tools/base.py`

```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Base class for all tools."""

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        """Execute the tool and return result dict."""

    def validate_required(self, kwargs: dict, required: list[str]) -> None:
        """Raise ValueError if required params are missing."""
        missing = [k for k in required if k not in kwargs or kwargs[k] is None]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")


class ToolDispatcher:
    """Maps tool name strings to implementations."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, name: str, tool: BaseTool) -> None:
        self._tools[name] = tool

    async def dispatch(self, name: str, **kwargs) -> dict:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return {"error": str(e), "tool": name}
```

### 2. `src/velox/tools/booking.py`
- `BookingAvailabilityTool` — calls Elektraweb adapter `availability()`
- `BookingQuoteTool` — calls Elektraweb adapter `quote()`
- `StayCreateHoldTool` — inserts into `stay_holds` table via repository, generates `S_HOLD_xxx` ID
- `BookingCreateReservationTool` — calls Elektraweb adapter `create_reservation()`
- `BookingGetReservationTool` — calls Elektraweb adapter `get_reservation()`
- `BookingModifyTool` — calls Elektraweb adapter `modify_reservation()`
- `BookingCancelTool` — calls Elektraweb adapter `cancel_reservation()`

### 3. `src/velox/tools/restaurant.py`
- `RestaurantAvailabilityTool` — queries `restaurant_slots` table for available slots
- `RestaurantCreateHoldTool` — inserts into `restaurant_holds`, generates `R_HOLD_xxx`
- `RestaurantConfirmTool` — updates hold status to CONFIRMED
- `RestaurantModifyTool` — updates hold with new data
- `RestaurantCancelTool` — updates hold status to CANCELLED, restores slot capacity

### 4. `src/velox/tools/transfer.py`
- `TransferGetInfoTool` — reads from `HotelProfile.transfer_routes`, matches route + pax count, returns price/vehicle/duration
- `TransferCreateHoldTool` — inserts into `transfer_holds`, generates `TR_HOLD_xxx`
- `TransferConfirmTool` — updates hold status
- `TransferModifyTool` — updates hold
- `TransferCancelTool` — updates hold status

### 5. `src/velox/tools/approval.py`
- `ApprovalRequestTool`:
  - Insert into `approval_requests` table, generate `APR_xxx` ID
  - Set the referenced hold's status to `PENDING_APPROVAL`
  - Send notification to required_roles via `notify.send`
  - Respect `any_of` flag:
    - STAY: required_roles=["ADMIN"], any_of=false
    - RESTAURANT: required_roles=["ADMIN","CHEF"], any_of=true
    - TRANSFER: required_roles=["ADMIN"], any_of=false

### 6. `src/velox/tools/payment.py`
- `PaymentRequestPrepaymentTool`:
  - Insert into `payment_requests`, generate `PAY_xxx` ID
  - Determine due_mode: NOW (non-refundable) or SCHEDULED (free cancel)
  - Send notification to SALES role
  - LLM NEVER collects payment info — always handled_by=SALES

### 7. `src/velox/tools/notification.py`
- `NotifySendTool`:
  - Insert into `notifications` table, generate `N_xxx` ID
  - Format message using A11.8 notification template standard
  - Channel routing: panel (always), + whatsapp/email if configured
  - Include metadata (intent, state, risk_flags, reference_id)

### 8. `src/velox/tools/handoff.py`
- `HandoffCreateTicketTool`:
  - Dedupe check: query tickets with same `dedupe_key` in OPEN/IN_PROGRESS status
  - If exists: return existing ticket_id (no duplicate)
  - If new: insert into `tickets`, generate `T_xxx` ID
  - Include handoff snapshot: intent, state, entities, risk_flags, transcript_summary
  - Send notification to assigned role

### 9. `src/velox/tools/crm.py`
- `CRMLogTool`:
  - Insert into `crm_logs`
  - Hash phone number (SHA-256) for privacy
  - Include: intent, entities, actions taken, outcome, transcript summary

### 10. `src/velox/tools/faq.py`
- `FAQLookupTool`:
  - Search `HotelProfile.faq_data` by topic keyword matching
  - Fuzzy match: if exact topic not found, find closest match
  - Return answer in requested language (tr/en)
  - If not found: return `{"found": false}` — LLM will handoff or say "I'll check"

## ID Generation Pattern
```python
import uuid

def generate_hold_id(prefix: str) -> str:
    """Generate sequential-looking ID: S_HOLD_a1b2c3"""
    short = uuid.uuid4().hex[:6].upper()
    return f"{prefix}_{short}"

# Usage:
# generate_hold_id("S_HOLD")  -> "S_HOLD_A1B2C3"
# generate_hold_id("R_HOLD")  -> "R_HOLD_X9Y8Z7"
# generate_hold_id("APR")     -> "APR_M3N4O5"
```

## Tool Registration (in main.py or startup)
```python
dispatcher = ToolDispatcher()
dispatcher.register("booking_availability", BookingAvailabilityTool(elektraweb_client))
dispatcher.register("booking_quote", BookingQuoteTool(elektraweb_client))
dispatcher.register("stay_create_hold", StayCreateHoldTool(stay_repo))
# ... register all tools
```

## Expected Outcome
- All 22+ tools are implemented and registered
- Each tool validates inputs, executes logic, returns structured dict
- DB operations are async (asyncpg)
- Error handling returns `{"error": "..."}` instead of raising exceptions to LLM
- Dedupe logic prevents duplicate tickets
