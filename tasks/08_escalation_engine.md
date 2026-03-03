# Task 08: Escalation Engine

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/anti_hallucination.md`

## Objective
Implement the risk detection and escalation engine that analyzes conversation risk flags (from LLM INTERNAL_JSON output and user message pattern matching), maps them to the escalation matrix, selects the highest escalation level, generates actions, and deduplicates tickets. Integrate the engine into the main message processing pipeline so that after every LLM response, escalation checks run automatically.

## Prerequisites
- Tasks 01-07 completed (project setup, DB, config, adapters, WhatsApp, LLM engine, tools)
- Models exist: `src/velox/models/escalation.py` (EscalationMatrixEntry, EscalationResult)
- Constants exist: `src/velox/config/constants.py` (RiskFlag, EscalationLevel, Role, TicketPriority enums)
- Escalation matrix data: `data/escalation_matrix.yaml` (29 risk flag entries with levels L0-L3)
- Database tables: `tickets` (with dedupe_key unique index), `notifications`
- Tool stubs: `handoff.create_ticket`, `notify.send` (from Task 07)

---

## Step 1: Implement Risk Detector

### File: `src/velox/escalation/risk_detector.py`

This module detects risk flags from two sources:
1. **INTERNAL_JSON risk_flags** — the LLM explicitly reports risk flags in its structured output
2. **User message pattern matching** — a secondary safety net that scans raw user text for keywords/patterns the LLM might miss

```python
"""Risk flag detection from LLM output and user message analysis."""

import re
from velox.config.constants import RiskFlag
from velox.models.conversation import InternalJSON
```

### 1.1 Define keyword/pattern dictionaries

Create a `RISK_PATTERNS` dictionary mapping each `RiskFlag` to a list of compiled regex patterns. These patterns should match Turkish and English keywords. Include at minimum:

```python
RISK_PATTERNS: dict[RiskFlag, list[re.Pattern]] = {
    RiskFlag.LEGAL_REQUEST: [
        re.compile(r"\b(avukat|lawyer|dava|lawsuit|mahkeme|court|hukuk|legal|savc[ıi]|prosecutor)\b", re.IGNORECASE),
    ],
    RiskFlag.SECURITY_INCIDENT: [
        re.compile(r"\b(h[ıi]rs[ıi]z|thief|stolen|cald[ıi]|robbery|g[uü]venlik\s*ihlal|security\s*breach|break.?in)\b", re.IGNORECASE),
    ],
    RiskFlag.THREAT_SELF_HARM: [
        re.compile(r"\b(intihar|suicide|kendime\s*zarar|self.?harm|[oö]lmek\s*ist|want\s*to\s*die)\b", re.IGNORECASE),
    ],
    RiskFlag.MEDICAL_EMERGENCY: [
        re.compile(r"\b(ambulans|ambulance|acil\s*t[ıi]bbi|emergency\s*medical|kalp\s*krizi|heart\s*attack|bayıld[ıi]|fainted|kan[ıi]yor|bleeding|zehirlen|poisoning)\b", re.IGNORECASE),
    ],
    RiskFlag.ANGRY_COMPLAINT: [
        re.compile(r"\b(rezalet|disgrace|utan[ıi]n|shame\s*on|berbat|terrible|asla\s*gelmem|never\s*come\s*back|[şs]ikayet\s*edece[gğ]im|will\s*complain)\b", re.IGNORECASE),
    ],
    RiskFlag.PAYMENT_CONFUSION: [
        re.compile(r"\b([oö]deme.*anla[sş]am|payment.*confus|nereye.*[oö]de|where.*pay|fazla.*[cç]ek|overcharge)\b", re.IGNORECASE),
    ],
    RiskFlag.CHARGEBACK_MENTION: [
        re.compile(r"\b(chargeback|itiraz|dispute|banka.*iade|bank.*refund|kart.*iade|card.*dispute)\b", re.IGNORECASE),
    ],
    RiskFlag.REFUND_DISPUTE: [
        re.compile(r"\b(iade.*iste|refund.*request|param[ıi].*geri|money\s*back|iade.*yap[ıi]lmad|refund.*not.*processed)\b", re.IGNORECASE),
    ],
    RiskFlag.HARASSMENT_HATE: [
        re.compile(r"\b(taciz|harassment|tehdit|threat|k[uü]f[uü]r|profanity|ırk[cç]|racist)\b", re.IGNORECASE),
    ],
    RiskFlag.FRAUD_SIGNAL: [
        re.compile(r"\b(sahte|fake|doland[ıi]r|fraud|scam|ka[cç]ak|illegal)\b", re.IGNORECASE),
    ],
    RiskFlag.GROUP_BOOKING: [
        re.compile(r"\b(grup|group|(\d{2,})\s*(ki[sş]i|person|people|pax))\b", re.IGNORECASE),
    ],
    RiskFlag.SPECIAL_EVENT: [
        re.compile(r"\b(d[oö][gğ]um\s*g[uü]n[uü]|birthday|balayı|honeymoon|y[ıi]ld[oö]n[uü]m[uü]|anniversary|evlilik\s*teklifi|proposal|organizasyon|event)\b", re.IGNORECASE),
    ],
    RiskFlag.ALLERGY_ALERT: [
        re.compile(r"\b(alerji|allergy|allergic|gl[uü]ten|lakto|lactose|f[ıi]st[ıi]k|peanut|yumurta\s*alerji|egg\s*allergy|[cç][oö]lyak|celiac)\b", re.IGNORECASE),
    ],
    RiskFlag.ACCESSIBILITY_NEED: [
        re.compile(r"\b(engelli|disabled|tekerlekli\s*sandalye|wheelchair|eri[sş]ilebilir|accessible|asans[oö]r|elevator)\b", re.IGNORECASE),
    ],
    RiskFlag.VIP_REQUEST: [
        re.compile(r"\b(vip|[oö]zel\s*kar[sş][ıi]lama|special\s*welcome|s[uü]rpriz|surprise|[oö]zel\s*istek|special\s*request)\b", re.IGNORECASE),
    ],
    RiskFlag.LOST_ITEM: [
        re.compile(r"\b(kay[ıi]p|lost|unuttum|forgot|b[ıi]rakt[ıi]m|left\s*behind|e[sş]ya|belongings|item)\b", re.IGNORECASE),
    ],
}
```

> **Note**: Not every RiskFlag needs a pattern. System-level flags like `TOOL_UNAVAILABLE`, `TOOL_ERROR_REPEAT`, `DATA_INCONSISTENCY`, `RATE_MAPPING_MISSING`, `CAPACITY_LIMIT`, `OVERBOOK_RISK`, `POLICY_MISSING`, `PII_OVERREQUEST`, `NO_SHOW_RISK`, `TEMPLATE_MISSING`, `LANGUAGE_UNSUPPORTED`, `RESERVATION_ID_MISSING`, `DATE_INVALID`, `CURRENCY_CONVERSION_REQUEST` are only set by the LLM or system logic, not detected from user text.

### 1.2 Implement `detect_risk_flags_from_message`

```python
def detect_risk_flags_from_message(user_message: str) -> list[RiskFlag]:
    """
    Scan user message text for risk flag patterns.
    Returns a list of detected RiskFlag values.
    """
    detected: list[RiskFlag] = []
    for flag, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(user_message):
                detected.append(flag)
                break  # One match per flag is enough
    return detected
```

### 1.3 Implement `detect_risk_flags_from_internal_json`

```python
def detect_risk_flags_from_internal_json(internal_json: InternalJSON) -> list[RiskFlag]:
    """
    Extract risk flags reported by the LLM in INTERNAL_JSON.
    Validates each flag against the RiskFlag enum.
    """
    detected: list[RiskFlag] = []
    for flag_str in internal_json.risk_flags:
        try:
            flag = RiskFlag(flag_str)
            detected.append(flag)
        except ValueError:
            # Unknown flag — log warning but don't crash
            pass
    return detected
```

### 1.4 Implement the combined `detect_all_risk_flags`

```python
def detect_all_risk_flags(
    user_message: str,
    internal_json: InternalJSON,
) -> list[RiskFlag]:
    """
    Merge risk flags from both sources, deduplicate, return unique list.
    """
    from_message = detect_risk_flags_from_message(user_message)
    from_llm = detect_risk_flags_from_internal_json(internal_json)
    # Merge and deduplicate while preserving order
    seen: set[RiskFlag] = set()
    merged: list[RiskFlag] = []
    for flag in from_llm + from_message:
        if flag not in seen:
            seen.add(flag)
            merged.append(flag)
    return merged
```

---

## Step 2: Implement Escalation Engine

### File: `src/velox/escalation/engine.py`

```python
"""Escalation engine — maps risk flags to escalation matrix, selects actions."""

import hashlib
import yaml
from pathlib import Path

from velox.config.constants import EscalationLevel, Role, TicketPriority
from velox.config.settings import settings
from velox.models.escalation import EscalationMatrixEntry, EscalationResult
```

### 2.1 Load and parse the escalation matrix

```python
# Level ordering for comparison
LEVEL_ORDER: dict[EscalationLevel, int] = {
    EscalationLevel.L0: 0,
    EscalationLevel.L1: 1,
    EscalationLevel.L2: 2,
    EscalationLevel.L3: 3,
}

PRIORITY_ORDER: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


class EscalationEngine:
    """Loads escalation matrix and evaluates risk flags."""

    def __init__(self) -> None:
        self._matrix: dict[str, EscalationMatrixEntry] = {}

    def load_matrix(self, path: str | None = None) -> None:
        """
        Load escalation matrix from YAML file.
        Path defaults to settings.escalation_matrix_path.
        """
        matrix_path = Path(path or settings.escalation_matrix_path)
        with open(matrix_path) as f:
            raw_entries = yaml.safe_load(f)

        self._matrix = {}
        for entry_data in raw_entries:
            entry = EscalationMatrixEntry(
                risk_flag=entry_data["risk_flag"],
                level=EscalationLevel(entry_data["level"]),
                route_to_role=Role(entry_data["route_to_role"]),
                priority=TicketPriority(entry_data["priority"]),
                action=entry_data.get("action", []),
                notify_channel=entry_data.get("notify_channel", "panel"),
                user_message_style=entry_data.get("user_message_style", "calm_premium"),
                reason_hint=entry_data.get("reason_hint", ""),
            )
            self._matrix[entry.risk_flag] = entry
```

**Important**: The YAML file uses a list format (items start with `- risk_flag:`). The `yaml.safe_load` will return a list of dicts. Parse each item into an `EscalationMatrixEntry` and index by `risk_flag`.

### 2.2 Implement `evaluate` method

```python
    def evaluate(
        self,
        risk_flags: list[str],
        intent: str,
        reference_id: str,
        conversation_id: str,
    ) -> EscalationResult:
        """
        Given detected risk flags, find matching matrix entries,
        select the highest level, aggregate actions, and generate dedupe key.

        Args:
            risk_flags: List of detected risk flag strings
            intent: Current conversation intent (for dedupe key)
            reference_id: Hold ID, reservation ID, or phone hash (for dedupe key)
            conversation_id: UUID of the conversation

        Returns:
            EscalationResult with level, role, actions, dedupe_key, etc.
        """
        if not risk_flags:
            return EscalationResult()

        matched_entries: list[EscalationMatrixEntry] = []
        for flag in risk_flags:
            if flag in self._matrix:
                matched_entries.append(self._matrix[flag])

        if not matched_entries:
            return EscalationResult(risk_flags_matched=risk_flags)

        # Select the highest level entry
        # If same level, select by highest priority
        best = max(
            matched_entries,
            key=lambda e: (LEVEL_ORDER[e.level], PRIORITY_ORDER.get(e.priority, 0)),
        )

        # Aggregate all unique actions from all matched entries
        all_actions: list[str] = []
        seen_actions: set[str] = set()
        for entry in matched_entries:
            for action in entry.action:
                if action not in seen_actions:
                    seen_actions.add(action)
                    all_actions.append(action)

        # Generate dedupe key
        # Format: "<highest_risk_flag>|<intent>|<reference_id>"
        dedupe_key = self._generate_dedupe_key(
            risk_flag=best.risk_flag,
            intent=intent,
            reference_id=reference_id,
        )

        # SLA hint based on level
        sla_map = {"L0": "low", "L1": "medium", "L2": "high", "L3": "critical"}

        return EscalationResult(
            level=best.level,
            route_to_role=best.route_to_role,
            dedupe_key=dedupe_key,
            reason=best.reason_hint,
            sla_hint=sla_map.get(best.level, "low"),
            actions=all_actions,
            risk_flags_matched=risk_flags,
        )
```

### 2.3 Implement dedupe key generation

```python
    @staticmethod
    def _generate_dedupe_key(risk_flag: str, intent: str, reference_id: str) -> str:
        """
        Generate a deterministic dedupe key for ticket deduplication.
        Format: "<risk_flag>|<intent>|<reference_id>"
        This ensures the same risk+intent+reference combination
        does not create duplicate tickets.
        """
        raw = f"{risk_flag}|{intent}|{reference_id}"
        return raw
```

### 2.4 Implement `check_dedupe` method

```python
    @staticmethod
    async def check_dedupe(dedupe_key: str, db_pool) -> bool:
        """
        Check if an open/in-progress ticket with this dedupe_key already exists.
        Returns True if a duplicate exists (skip ticket creation).

        Uses the unique index: idx_tickets_dedupe ON tickets(dedupe_key)
        WHERE dedupe_key IS NOT NULL AND status NOT IN ('RESOLVED', 'CLOSED')
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM tickets
                WHERE dedupe_key = $1
                AND status NOT IN ('RESOLVED', 'CLOSED')
            )
        """
        async with db_pool.acquire() as conn:
            return await conn.fetchval(query, dedupe_key)
```

### 2.5 Implement `execute_actions` method

```python
    @staticmethod
    async def execute_actions(
        result: EscalationResult,
        conversation_id: str,
        hotel_id: int,
        phone_hash: str,
        transcript_summary: str,
        tools: dict,  # {"handoff": handoff_tool, "notify": notify_tool}
        db_pool,
    ) -> dict:
        """
        Execute the escalation actions (create ticket, send notification).
        Checks dedupe before creating tickets.

        Returns dict with results of each action taken.
        """
        action_results: dict = {}

        if not result.actions:
            return action_results

        # Check dedupe before creating ticket
        ticket_exists = False
        if result.dedupe_key:
            ticket_exists = await EscalationEngine.check_dedupe(result.dedupe_key, db_pool)

        for action in result.actions:
            if action == "handoff.create_ticket" and not ticket_exists:
                ticket_result = await tools["handoff"].create_ticket(
                    hotel_id=hotel_id,
                    conversation_id=conversation_id,
                    reason=result.reason,
                    transcript_summary=transcript_summary,
                    priority=result.sla_hint,
                    assigned_to_role=result.route_to_role,
                    dedupe_key=result.dedupe_key,
                )
                action_results["ticket"] = ticket_result

            elif action == "notify.send":
                notify_result = await tools["notify"].send(
                    hotel_id=hotel_id,
                    to_role=result.route_to_role,
                    channel="panel",
                    message=f"[{result.level}] {result.reason}",
                    metadata={
                        "conversation_id": conversation_id,
                        "risk_flags": result.risk_flags_matched,
                        "dedupe_key": result.dedupe_key,
                    },
                )
                action_results["notification"] = notify_result

        return action_results
```

---

## Step 3: Update `__init__.py`

### File: `src/velox/escalation/__init__.py`

```python
from velox.escalation.risk_detector import detect_all_risk_flags
from velox.escalation.engine import EscalationEngine

__all__ = ["detect_all_risk_flags", "EscalationEngine"]
```

---

## Step 4: Initialize Escalation Engine at Startup

### File: `src/velox/main.py`

In the `lifespan` function, add escalation engine initialization:

```python
from velox.escalation.engine import EscalationEngine

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ... existing startup code ...

    # Load escalation matrix
    escalation_engine = EscalationEngine()
    escalation_engine.load_matrix()
    app.state.escalation_engine = escalation_engine

    yield
    # ... existing shutdown code ...
```

---

## Step 5: Integrate into Message Processing Pipeline

### File: `src/velox/core/pipeline.py` (create or modify)

After the LLM generates a response and it is parsed into `LLMResponse` (with `user_message` + `internal_json`), the escalation engine must run. Add this as a post-processing step.

```python
async def post_process_escalation(
    user_message_text: str,
    llm_response: LLMResponse,
    conversation: Conversation,
    escalation_engine: EscalationEngine,
    tools: dict,
    db_pool,
) -> EscalationResult:
    """
    Run after every LLM response to check for escalation needs.

    Steps:
    1. Detect risk flags from INTERNAL_JSON + user message patterns
    2. Evaluate against escalation matrix
    3. Execute actions (ticket + notification) if needed
    4. Update conversation risk_flags in DB
    5. Return EscalationResult for logging
    """
    from velox.escalation.risk_detector import detect_all_risk_flags

    # Step 1: Detect all risk flags
    risk_flags = detect_all_risk_flags(
        user_message=user_message_text,
        internal_json=llm_response.internal_json,
    )

    if not risk_flags:
        return EscalationResult()

    # Step 2: Evaluate against matrix
    reference_id = (
        conversation.entities_json.get("hold_id")
        or conversation.entities_json.get("reservation_id")
        or conversation.phone_hash
    )

    result = escalation_engine.evaluate(
        risk_flags=[f.value for f in risk_flags],
        intent=llm_response.internal_json.intent,
        reference_id=reference_id,
        conversation_id=str(conversation.id),
    )

    # Step 3: Execute actions
    if result.actions:
        # Build transcript summary from last N messages
        transcript_summary = _build_transcript_summary(conversation.messages[-5:])

        await escalation_engine.execute_actions(
            result=result,
            conversation_id=str(conversation.id),
            hotel_id=conversation.hotel_id,
            phone_hash=conversation.phone_hash,
            transcript_summary=transcript_summary,
            tools=tools,
            db_pool=db_pool,
        )

    # Step 4: Update conversation risk_flags in DB
    await _update_conversation_risk_flags(
        conversation_id=str(conversation.id),
        risk_flags=[f.value for f in risk_flags],
        db_pool=db_pool,
    )

    return result


def _build_transcript_summary(messages: list) -> str:
    """Build a short summary of recent messages for ticket context."""
    lines = []
    for msg in messages:
        role = msg.role.upper()
        content = msg.content[:200]  # Truncate long messages
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)


async def _update_conversation_risk_flags(
    conversation_id: str,
    risk_flags: list[str],
    db_pool,
) -> None:
    """Append new risk flags to the conversation record."""
    query = """
        UPDATE conversations
        SET risk_flags = array_cat(
            risk_flags,
            $2::text[]
        ),
        updated_at = now()
        WHERE id = $1
    """
    # Avoid duplicating flags already stored
    deduped_query = """
        UPDATE conversations
        SET risk_flags = (
            SELECT array_agg(DISTINCT flag)
            FROM unnest(array_cat(risk_flags, $2::text[])) AS flag
        ),
        updated_at = now()
        WHERE id = $1
    """
    async with db_pool.acquire() as conn:
        await conn.execute(deduped_query, conversation_id, risk_flags)
```

---

## Step 6: Wire Into the Main Webhook Handler

### File: `src/velox/api/routes/whatsapp_webhook.py` (modify the message processing function)

In the message handler, after calling the LLM and parsing the response, add:

```python
# After getting llm_response (LLMResponse):
escalation_result = await post_process_escalation(
    user_message_text=incoming_message.text,
    llm_response=llm_response,
    conversation=conversation,
    escalation_engine=request.app.state.escalation_engine,
    tools={"handoff": handoff_tool, "notify": notify_tool},
    db_pool=request.app.state.db_pool,
)

# Log escalation result if non-trivial
if escalation_result.level != EscalationLevel.L0 or escalation_result.risk_flags_matched:
    logger.info(
        "escalation_check",
        conversation_id=str(conversation.id),
        level=escalation_result.level,
        flags=escalation_result.risk_flags_matched,
        actions=escalation_result.actions,
    )
```

---

## Validation Checklist

After implementation, verify the following:

1. **Risk detection from INTERNAL_JSON**: When the LLM returns `risk_flags: ["LEGAL_REQUEST"]` in INTERNAL_JSON, `detect_risk_flags_from_internal_json` returns `[RiskFlag.LEGAL_REQUEST]`.

2. **Risk detection from user message**: When user sends "avukatimla gorusecegim" (I'll talk to my lawyer), `detect_risk_flags_from_message` returns `[RiskFlag.LEGAL_REQUEST]`.

3. **Merged detection**: Both sources are merged and deduplicated.

4. **Matrix matching**: `LEGAL_REQUEST` maps to L3, ADMIN, high priority, actions = `[handoff.create_ticket, notify.send]`.

5. **Level selection**: If multiple flags (e.g., `LEGAL_REQUEST` L3 + `ANGRY_COMPLAINT` L2), the highest level (L3) wins.

6. **Dedupe**: If a ticket with the same dedupe_key already exists (status = OPEN or IN_PROGRESS), a new ticket is NOT created.

7. **Action execution**: `handoff.create_ticket` is called with correct parameters. `notify.send` is called with panel channel.

8. **Conversation updated**: `conversations.risk_flags` column is updated with newly detected flags.

9. **Pipeline integration**: Every incoming message goes through escalation check after LLM response.

---

## File Summary

| File | Action |
|------|--------|
| `src/velox/escalation/risk_detector.py` | **Create** |
| `src/velox/escalation/engine.py` | **Create** |
| `src/velox/escalation/__init__.py` | **Modify** (add exports) |
| `src/velox/main.py` | **Modify** (add engine init in lifespan) |
| `src/velox/core/pipeline.py` | **Create or Modify** (add post_process_escalation) |
| `src/velox/api/routes/whatsapp_webhook.py` | **Modify** (wire escalation into handler) |

## Expected Outcome
- Risk flags are detected from both LLM output and user message patterns
- Escalation matrix is loaded from YAML at startup
- Highest escalation level is selected when multiple flags present
- Ticket creation is deduplicated per conversation+intent+reference
- Notifications are sent to the correct role via the correct channel
- The entire flow runs automatically after every LLM response in the webhook pipeline
