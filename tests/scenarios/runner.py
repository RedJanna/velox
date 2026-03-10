"""Scenario runner for high-level conversational flow testing."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from velox.config.constants import ConversationState
from velox.core.intent_engine import detect_intent
from velox.core.state_machine import next_state


class ScenarioProcessor(Protocol):
    """Callable interface for processing one scenario step."""

    async def __call__(self, user_message: str, current_state: ConversationState) -> dict[str, Any]:
        """Process message and return intent/state/tool/reply/risk_flags payload."""


@dataclass
class ScenarioStepResult:
    """Result of a single scenario step."""

    index: int
    passed: bool
    user_message: str = ""
    errors: list[str] = field(default_factory=list)
    response: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Overall scenario run result."""

    code: str
    name: str
    category: str
    passed: bool
    steps: list[ScenarioStepResult]
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0

    def __post_init__(self) -> None:
        self.total_steps = len(self.steps)
        self.passed_steps = sum(1 for s in self.steps if s.passed)
        self.failed_steps = self.total_steps - self.passed_steps


class ScenarioRunner:
    """Run scenario test cases against an emulated pipeline."""

    def __init__(self, processor: ScenarioProcessor | None = None) -> None:
        self._processor = processor or self._default_processor

    async def run_scenario(self, scenario: dict[str, Any]) -> ScenarioResult:
        """Run a scenario dict and validate each step expectation."""
        # Processor'u sifirla (multi-turn conversation gecmisini temizle)
        if hasattr(self._processor, "reset"):
            self._processor.reset()

        state = ConversationState.GREETING
        results: list[ScenarioStepResult] = []

        for index, step in enumerate(scenario.get("steps", []), start=1):
            user_msg = str(step.get("user", ""))
            response = await self._processor(user_msg, state)
            state = ConversationState(response["state"])
            errors: list[str] = []

            # QC1: Intent check
            expected_intent = step.get("expect_intent")
            if expected_intent and response.get("intent") != expected_intent:
                errors.append(
                    f"[QC1] intent mismatch: expected={expected_intent} actual={response.get('intent')}"
                )

            # QC2: State check
            expected_state = step.get("expect_state")
            if expected_state and response.get("state") != expected_state:
                errors.append(
                    f"[QC2] state mismatch: expected={expected_state} actual={response.get('state')}"
                )

            # QC3: Tool calls check
            expected_tool_calls = step.get("expect_tool_calls", [])
            actual_tool_calls = response.get("tool_calls", [])
            if expected_tool_calls and actual_tool_calls != expected_tool_calls:
                errors.append(
                    f"[QC3] tool_calls mismatch: expected={expected_tool_calls} actual={actual_tool_calls}"
                )

            # QC4: Reply contains check
            reply = str(response.get("reply", "")).lower()

            expected_terms = [str(t).lower() for t in step.get("expect_reply_contains", [])]
            for term in expected_terms:
                if term not in reply:
                    errors.append(f"[QC4] reply missing expected term: '{term}'")

            # QC5: Reply must NOT contain check
            forbidden_terms = [str(t).lower() for t in step.get("expect_reply_must_not", [])]
            for term in forbidden_terms:
                if term in reply:
                    errors.append(f"[QC5] reply contains forbidden term: '{term}'")

            # QC6: Risk flags check
            expected_flags = step.get("expect_risk_flags", [])
            actual_flags = response.get("risk_flags", [])
            for flag in expected_flags:
                if flag not in actual_flags:
                    errors.append(f"[QC6] missing expected risk_flag: {flag}")

            results.append(
                ScenarioStepResult(
                    index=index,
                    passed=not errors,
                    user_message=user_msg,
                    errors=errors,
                    response=response,
                )
            )

        return ScenarioResult(
            code=str(scenario.get("code", "")),
            name=str(scenario.get("name", "")),
            category=str(scenario.get("category", "")),
            passed=all(item.passed for item in results),
            steps=results,
        )

    async def _default_processor(self, user_message: str, current_state: ConversationState) -> dict[str, Any]:
        """Very small deterministic processor used for CI scenario tests."""
        intent = detect_intent(user_message).value
        lowered = user_message.lower()
        tool_calls: list[str] = []
        risk_flags: list[str] = []

        if "admin onay" in lowered:
            state = next_state(ConversationState.PENDING_APPROVAL, "admin_approved").value
            reply = "Rezervasyonunuz kesinlesti."
        elif "evet" in lowered or "onay" in lowered:
            state = next_state(ConversationState.NEEDS_CONFIRMATION, "user_confirmed").value
            tool_calls = ["stay_create_hold"] if "restoran" not in lowered else ["restaurant_create_hold"]
            reply = "Talebiniz onaya gonderildi."
        elif "fiyat" in lowered or "teklif" in lowered:
            state = next_state(ConversationState.READY_FOR_TOOL, "tool_called").value
            tool_calls = ["booking_quote"] if "restoran" not in lowered else ["restaurant_availability"]
            reply = "Teklif ve musaitlik bilgisi hazirlaniyor."
        elif any(token in lowered for token in ["temmuz", "agustos", "saat", "kisi", "2 yetiskin"]):
            state = next_state(ConversationState.NEEDS_VERIFICATION, "slots_filled").value
            tool_calls = ["booking_availability"] if "restoran" not in lowered else ["restaurant_availability"]
            reply = "Musaitlik kontrolu yapiliyor."
        elif current_state == ConversationState.GREETING:
            state = next_state(current_state, "message_received").value
            reply = "Hos geldiniz, tarih ve kisi sayisini paylasabilir misiniz?"
        else:
            state = next_state(ConversationState.INTENT_DETECTED, "missing_slots").value
            reply = "Tarih ve kisi bilgilerini netlestirelim."

        if "restoran" in lowered:
            intent = "restaurant_booking_create"

        return {
            "intent": intent,
            "state": state,
            "tool_calls": tool_calls,
            "risk_flags": risk_flags,
            "reply": reply,
        }
