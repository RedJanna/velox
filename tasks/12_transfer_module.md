# Task 12: Transfer Module

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/error_handling.md`

## Objective
Implement the airport/location transfer service: route info lookup, price calculation, hold creation, and booking flow. This module uses Admin Panel DB only (no Elektraweb).

## Reference
- `docs/master_prompt_v2.md` — A8.4 (Transfer Tools), A9.5 (Transfer Rules)
- `data/hotel_profiles/kassandra_oludeniz.yaml` — transfer_routes section
- `src/velox/models/transfer.py` — TransferHold, TransferRoute models

## Files to Create/Modify

### 1. Transfer Tool Implementations

**transfer.get_info**:
```python
class TransferGetInfoTool(BaseTool):
    async def execute(self, hotel_id: int, route: str, pax_count: int) -> dict:
        # 1. Load hotel profile
        # 2. Find matching route in transfer_routes
        # 3. Determine vehicle type based on pax_count:
        #    - pax <= max_pax: standard vehicle (Vito)
        #    - pax > max_pax: oversize vehicle (Sprinter) if configured
        #    - pax > oversize max: return error/handoff suggestion
        # 4. Return: route, distance, duration, price, vehicle, baby_seat info
```

**transfer.create_hold**:
```python
class TransferCreateHoldTool(BaseTool):
    async def execute(self, hotel_id: int, route: str, date: str, time: str,
                      pax_count: int, guest_name: str, phone: str,
                      flight_no: str = None, baby_seat: bool = False,
                      notes: str = None) -> dict:
        # 1. Validate route exists in hotel profile
        # 2. Calculate price (including oversize if needed)
        # 3. Insert into transfer_holds table
        # 4. Return hold_id, status, summary
```

### 2. `src/velox/db/repositories/transfer.py`

```python
class TransferRepository:
    async def create_hold(self, hold: TransferHold) -> TransferHold:
        """Insert transfer hold."""

    async def get_hold(self, hold_id: str) -> TransferHold | None:
        """Fetch hold by ID."""

    async def update_hold_status(self, hold_id: str, status: str, **kwargs) -> None:
        """Update hold status."""

    async def list_holds(self, hotel_id: int, date_from: date = None, date_to: date = None, status: str = None) -> list[TransferHold]:
        """List holds with optional filters."""
```

### 3. Transfer Routes Configuration

From Kassandra Oludeniz profile:
```
Route                         | Price  | Vehicle | Max Pax | Duration
DALAMAN_AIRPORT_TO_HOTEL      | 75 EUR | Vito    | 7       | 75 min
HOTEL_TO_DALAMAN_AIRPORT      | 75 EUR | Vito    | 7       | 75 min
ANTALYA_AIRPORT_TO_HOTEL      | 220 EUR| Vito    | 7       | 240 min
HOTEL_TO_ANTALYA_AIRPORT      | 220 EUR| Vito    | 7       | 240 min

Oversize (8+ pax): Sprinter, 100 EUR (Dalaman only)
Baby seat: Available, free
Custom routes: ADMIN handoff
```

### 4. Business Rules
- Standard route requests: provide info + offer booking
- Custom/unknown routes: L2 escalation to ADMIN
- Same-day urgent requests (< 3 hours): L2 escalation to OPS
- Payment: usually cash/card at reception (default), admin can override
- Flight delay handling: if guest reports delay, notify OPS (L1)

### 5. Admin API Endpoints

Add to admin routes:
```python
@router.get("/hotels/{hotel_id}/transfers/holds")
async def list_transfer_holds(hotel_id: int, status: str = None)

@router.post("/hotels/{hotel_id}/transfers/holds/{hold_id}/approve")
async def approve_transfer(hotel_id: int, hold_id: str)

@router.post("/hotels/{hotel_id}/transfers/holds/{hold_id}/reject")
async def reject_transfer(hotel_id: int, hold_id: str, reason: str)
```

## Expected Outcome
- AI provides accurate transfer info from hotel profile
- Transfer holds are created and tracked in DB
- Approval flow works via admin panel
- Oversize vehicle logic applies automatically for 8+ pax
- Custom/unknown routes escalate to admin
