"""Scenario runner for high-level conversational flow testing."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from velox.config.constants import ConversationState
from velox.core.intent_engine import detect_intent
from velox.core.state_machine import next_state


class ScenarioProcessor(Protocol):
    """Callable interface for processing one scenario step."""

    async def __call__(self, user_message: str, current_state: ConversationState) -> dict[str, Any]:
        """Process message and return intent/state/tool/reply payload."""


@dataclass
class ScenarioStepResult:
    """Result of a single scenario step."""

    index: int
    passed: bool
    errors: list[str] = field(default_factory=list)
    response: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Overall scenario run result."""

    code: str
    name: str
    passed: bool
    steps: list[ScenarioStepResult]


class ScenarioRunner:
    """Run scenario test cases against an emulated pipeline."""

    def __init__(self, processor: ScenarioProcessor | None = None) -> None:
        self._processor = processor or self._default_processor

    async def run_scenario(self, scenario: dict[str, Any]) -> ScenarioResult:
        """Run a scenario dict and validate each step expectation."""
        state = ConversationState.GREETING
        results: list[ScenarioStepResult] = []

        for index, step in enumerate(scenario.get("steps", []), start=1):
            response = await self._processor(str(step.get("user", "")), state)
            state = ConversationState(response["state"])
            errors: list[str] = []

            expected_intent = step.get("expect_intent")
            if expected_intent and response.get("intent") != expected_intent:
                errors.append(f"intent mismatch: expected={expected_intent} actual={response.get('intent')}")

            expected_state = step.get("expect_state")
            if expected_state and response.get("state") != expected_state:
                errors.append(f"state mismatch: expected={expected_state} actual={response.get('state')}")

            expected_tool_calls = step.get("expect_tool_calls", [])
            actual_tool_calls = response.get("tool_calls", [])
            if expected_tool_calls and actual_tool_calls != expected_tool_calls:
                errors.append(
                    f"tool_calls mismatch: expected={expected_tool_calls} actual={actual_tool_calls}"
                )

            expected_terms = [str(term).lower() for term in step.get("expect_reply_contains", [])]
            reply = str(response.get("reply", "")).lower()
            for term in expected_terms:
                if term not in reply:
                    errors.append(f"reply missing expected term: {term}")

            results.append(
                ScenarioStepResult(
                    index=index,
                    passed=not errors,
                    errors=errors,
                    response=response,
                )
            )

        return ScenarioResult(
            code=str(scenario.get("code", "")),
            name=str(scenario.get("name", "")),
            passed=all(item.passed for item in results),
            steps=results,
        )

    async def _default_processor(self, user_message: str, current_state: ConversationState) -> dict[str, Any]:
        """Very small deterministic processor used for CI scenario tests."""
        intent = detect_intent(user_message).value
        lowered = user_message.lower()
        tool_calls: list[str] = []

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
            "reply": reply,
        }
