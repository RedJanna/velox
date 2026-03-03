# Task 11: Restaurant Module

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/error_handling.md`

## Objective
Implement the restaurant reservation system: slot/capacity management, availability queries, hold creation, and the full booking flow. This module uses only the Admin Panel DB (no Elektraweb).

## Reference
- `docs/master_prompt_v2.md` — A8.2 (Restaurant Tools), A9.1 (Approval Rules), B5 (Restaurant Module)
- `data/hotel_profiles/kassandra_oludeniz.yaml` — restaurant section
- `src/velox/db/migrations/001_initial.sql` — restaurant_holds, restaurant_slots tables
- `src/velox/models/restaurant.py` — RestaurantHold, RestaurantSlot models

## Files to Create/Modify

### 1. `src/velox/db/repositories/restaurant.py`

```python
class RestaurantRepository:
    async def get_available_slots(self, hotel_id: int, date: date, time: time, party_size: int, area: str | None) -> list[RestaurantSlot]:
        """Query restaurant_slots where capacity_left >= party_size."""
        # Filter by hotel_id, date, time range (+/- 1 hour), area if specified
        # Order by time proximity to requested time

    async def create_hold(self, hold: RestaurantHold) -> RestaurantHold:
        """Insert restaurant hold and decrement slot capacity."""
        # 1. Insert into restaurant_holds
        # 2. UPDATE restaurant_slots SET booked_count = booked_count + party_size
        # 3. Use transaction to ensure atomicity

    async def update_hold_status(self, hold_id: str, status: str, **kwargs) -> None:
        """Update hold status (CONFIRMED, CANCELLED, etc.)."""

    async def cancel_hold(self, hold_id: str, reason: str) -> None:
        """Cancel hold and restore slot capacity."""
        # 1. Update hold status to CANCELLED
        # 2. UPDATE restaurant_slots SET booked_count = booked_count - party_size
        # Transaction for atomicity

    async def get_hold(self, hold_id: str) -> RestaurantHold | None:
        """Fetch hold by ID."""
```

### 2. Slot Management (Admin API)

Add to `src/velox/api/routes/admin.py`:

```python
@router.post("/hotels/{hotel_id}/restaurant/slots")
async def create_restaurant_slots(hotel_id: int, slots: list[SlotCreate]):
    """Admin creates available restaurant slots for a date range."""

@router.get("/hotels/{hotel_id}/restaurant/slots")
async def list_restaurant_slots(hotel_id: int, date_from: date, date_to: date):
    """List restaurant slots with availability."""

@router.put("/hotels/{hotel_id}/restaurant/slots/{slot_id}")
async def update_slot(hotel_id: int, slot_id: int, update: SlotUpdate):
    """Update slot capacity or active status."""
```

### 3. Restaurant Tool Implementations

Already outlined in Task 07, but specifics:

**restaurant.availability**:
- Query slots within +/- 1 hour of requested time
- Check `capacity_left >= party_size`
- If party_size > max_ai_party_size (8): return `{"available": false, "reason": "GROUP_BOOKING", "suggestion": "handoff"}`
- Return matching slots with time + capacity info

**restaurant.create_hold**:
- Validate party_size, date/time within restaurant hours
- Check slot availability one more time (race condition guard)
- Create hold with PENDING_APPROVAL status
- Auto-trigger approval.request (ADMIN or CHEF, any_of=true)

### 4. Business Rules (from Hotel Profile)

```yaml
# From kassandra_oludeniz.yaml
restaurant:
  hours:
    breakfast: "08:00-10:30"
    lunch: "12:00-17:00"
    dinner: "18:00-22:00"
  max_ai_party_size: 8       # 9+ = GROUP_BOOKING handoff
  late_tolerance_min: 15      # 15 min grace period
  external_guests_allowed: true
```

- Requests outside restaurant hours: inform user, suggest valid times
- Requests for 9+ people: escalate as GROUP_BOOKING (L2, SALES)
- Allergy/special diet notes: add ALLERGY_ALERT risk flag, notify CHEF (L1)

## Expected Outcome
- Admin can create/manage restaurant time slots
- AI can check availability and create holds
- Approval flow works (ADMIN or CHEF)
- Capacity tracking is accurate (no overbooking)
- Large group requests escalate properly
