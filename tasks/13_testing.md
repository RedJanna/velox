# Task 13: Testing

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/testing_qa.md`

## Objective
Implement comprehensive test suite: unit tests, integration tests, and scenario-based E2E tests.

## Reference
- `docs/master_prompt_v2.md` — B10 (Test Strategy)
- `data/scenarios/` — Scenario files from DİKKAT\Senaryolar
- All `src/velox/` modules

## Test Framework Setup

### `tests/conftest.py`
```python
import pytest
import asyncio
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db():
    """Mock database connection."""

@pytest.fixture
def mock_redis():
    """Mock Redis client."""

@pytest.fixture
def mock_elektraweb():
    """Mock Elektraweb adapter with predefined responses."""

@pytest.fixture
def mock_whatsapp():
    """Mock WhatsApp client."""

@pytest.fixture
def mock_openai():
    """Mock OpenAI client with predefined responses."""

@pytest.fixture
def hotel_profile():
    """Load Kassandra Oludeniz profile from YAML."""

@pytest.fixture
def escalation_matrix():
    """Load escalation matrix from YAML."""
```

## Unit Tests

### `tests/unit/test_intent_engine.py`
Test intent detection accuracy (if using local classification):
- Turkish reservation requests -> stay_availability/stay_booking_create
- English FAQ questions -> faq_info
- Transfer queries -> transfer_info
- Complaint detection -> complaint
- Handoff requests -> human_handoff

### `tests/unit/test_state_machine.py`
Test state transitions:
- GREETING -> INTENT_DETECTED (on first meaningful message)
- INTENT_DETECTED -> NEEDS_VERIFICATION (missing slots)
- NEEDS_VERIFICATION -> READY_FOR_TOOL (all slots filled)
- READY_FOR_TOOL -> TOOL_RUNNING (tool called)
- TOOL_RUNNING -> NEEDS_CONFIRMATION (results presented)
- NEEDS_CONFIRMATION -> PENDING_APPROVAL (user confirmed)
- PENDING_APPROVAL -> CONFIRMED (admin approved)
- Any -> HANDOFF (escalation triggered)

### `tests/unit/test_verification.py`
Test slot verification logic:
- Date validation (valid format, future dates, check-out > check-in)
- Guest count validation (adults >= 1, child ages valid)
- Phone number validation (international format)
- Currency code validation (ISO 4217)

### `tests/unit/test_escalation.py`
Test escalation matrix matching:
- Single risk flag -> correct level + role
- Multiple risk flags -> highest level wins
- Dedupe key generation
- L0 flags -> no action
- L3 flags -> immediate high-priority ticket + notify

### `tests/unit/test_policies.py`
Test business rule enforcement:
- FREE_CANCEL: prepayment scheduled 7 days before check-in
- NON_REFUNDABLE: immediate prepayment required
- FREE_CANCEL refund deadline: 5 days before check-in
- Rate mapping: FREE_CANCEL -> rate_type_id=10, NON_REFUNDABLE -> rate_type_id=11
- Transfer pricing: correct vehicle selection based on pax count
- Restaurant: 9+ pax triggers GROUP_BOOKING escalation

## Integration Tests

### `tests/integration/test_elektraweb_adapter.py`
Test with mocked HTTP responses:
- Successful availability query
- Successful quote with offers
- Auth token refresh on 401
- Retry logic on timeout
- Error handling on 500

### `tests/integration/test_whatsapp_webhook.py`
Test webhook endpoints:
- GET verification with correct/incorrect tokens
- POST with valid signature -> message processed
- POST with invalid signature -> 403
- Status updates (delivered, read) -> 200 without processing
- Deduplication of repeated webhooks

### `tests/integration/test_llm_pipeline.py`
Test full LLM pipeline with mocked OpenAI:
- User sends greeting -> LLM returns greeting USER_MESSAGE
- User asks availability -> LLM calls booking_availability tool
- Tool result -> LLM formats response for user
- Multi-turn: greeting -> availability -> quote -> confirm -> hold

## Scenario Tests (E2E)

### `tests/scenarios/runner.py`
```python
class ScenarioRunner:
    """Run scenario test cases against the full pipeline."""

    async def run_scenario(self, scenario: dict) -> ScenarioResult:
        """
        scenario = {
            "code": "S001",
            "name": "Hotel Reservation",
            "steps": [
                {"user": "Merhaba, 15-18 Temmuz icin oda bakmak istiyorum",
                 "expect_intent": "stay_availability",
                 "expect_state": "NEEDS_VERIFICATION",
                 "expect_tool_calls": [],
                 "expect_reply_contains": ["tarih", "kisi"]},
                ...
            ]
        }
        """
```

### `tests/scenarios/test_s001_hotel_reservation.py`
Full stay booking flow: greeting -> dates -> availability -> quote -> confirm -> hold -> approval

### `tests/scenarios/test_s024_restaurant_reservation.py`
Restaurant booking: greeting -> date/time/pax -> availability -> confirm -> hold -> approval

## Running Tests
```bash
# All tests
pytest

# Unit only
pytest tests/unit/

# With coverage
pytest --cov=velox --cov-report=html

# Specific scenario
pytest tests/scenarios/test_s001_hotel_reservation.py -v
```

## Expected Outcome
- 80%+ code coverage
- All critical paths tested
- Scenario tests validate real user flows
- CI-ready test suite (no external dependencies required)
