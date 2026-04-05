"""Parse LLM output into USER_MESSAGE and INTERNAL_JSON."""

import re
from typing import Any, cast

import orjson
import structlog
from pydantic import ValidationError

from velox.config.constants import ConversationState, Intent
from velox.models.conversation import InternalJSON, LLMResponse
from velox.utils.metrics import record_structured_output_parser_error

logger = structlog.get_logger(__name__)

JSON_BLOCK_PATTERN = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
# Handle markdown bold/stars around the marker: **INTERNAL_JSON:** or *INTERNAL_JSON:* etc.
INTERNAL_JSON_PATTERN = re.compile(
    r"\*{0,2}INTERNAL_JSON\*{0,2}\s*:?\s*\*{0,2}",
    re.IGNORECASE,
)
USER_MESSAGE_PATTERN = re.compile(
    r"USER_MESSAGE\s*:\s*(.+?)(?:\n\*{0,2}INTERNAL_JSON|$)",
    re.DOTALL | re.IGNORECASE,
)
STRUCTURED_OUTPUT_ERROR_KEY = "response_parser"
_CANONICAL_INTENTS = {intent.value for intent in Intent}
_CANONICAL_STATES = {state.value for state in ConversationState}
_PASSTHROUGH_STATES = {"ANSWERED"}
_STATE_ALIASES = {
    "awaiting_request": ConversationState.NEEDS_VERIFICATION.value,
    "collecting_missing_field": ConversationState.NEEDS_VERIFICATION.value,
    "collecting_missing_fields": ConversationState.NEEDS_VERIFICATION.value,
    "awaiting_room_preference": ConversationState.NEEDS_VERIFICATION.value,
}
_INTENT_ALIASES = {
    "check_availability": Intent.STAY_AVAILABILITY.value,
}


class StructuredOutputError(Exception):
    """Base error for malformed or missing INTERNAL_JSON payloads."""

    reason = "unknown"


class MissingStructuredOutputError(StructuredOutputError):
    """Raised when the model returns no parseable INTERNAL_JSON payload."""

    reason = "missing_internal_json"


class InvalidStructuredOutputError(StructuredOutputError):
    """Raised when INTERNAL_JSON exists but fails schema validation."""

    reason = "invalid_internal_json"


class ResponseParser:
    """Parses model raw text into structured Velox response object."""

    @staticmethod
    def parse(raw_content: str) -> LLMResponse:
        """Parse LLM response using layered strategies with explicit parser error metadata."""
        text = raw_content.strip()
        user_message = ResponseParser._extract_user_message(text)
        internal_json: InternalJSON

        try:
            internal_data = ResponseParser._extract_internal_data(text)
            internal_json = ResponseParser.validate_internal_json(internal_data)
        except StructuredOutputError as exc:
            record_structured_output_parser_error(exc.reason)
            logger.warning(
                "llm_structured_output_parse_failed",
                reason=exc.reason,
            )
            internal_json = ResponseParser._build_parser_error_internal_json(exc.reason)
        if not user_message:
            user_message = ResponseParser._fallback_user_message(text, internal_json)

        return LLMResponse(user_message=user_message, internal_json=internal_json)

    @staticmethod
    def validate_internal_json(data: dict[str, Any]) -> InternalJSON:
        """Validate/coerce INTERNAL_JSON and raise explicit parser errors on failure."""
        normalized_data = ResponseParser._normalize_internal_data(data)
        try:
            return InternalJSON.model_validate(normalized_data)
        except ValidationError:
            raise InvalidStructuredOutputError from None

    @staticmethod
    def extract_parser_error(internal_json: InternalJSON) -> str:
        """Return parser error reason when INTERNAL_JSON was synthesized after a parse failure."""
        entities = internal_json.entities if isinstance(internal_json.entities, dict) else {}
        parser_meta = entities.get(STRUCTURED_OUTPUT_ERROR_KEY)
        if not isinstance(parser_meta, dict):
            return ""
        return str(parser_meta.get("reason") or "").strip()

    @staticmethod
    def extract_tool_calls(internal_json: InternalJSON) -> list[dict[str, Any]]:
        """Extract normalized tool calls list from INTERNAL_JSON."""
        normalized: list[dict[str, Any]] = []
        for item in internal_json.tool_calls:
            if not isinstance(item, dict):
                continue
            tool_name = item.get("tool") or item.get("name")
            if not isinstance(tool_name, str) or not tool_name:
                continue
            args = item.get("args") if isinstance(item.get("args"), dict) else item.get("arguments")
            if not isinstance(args, dict):
                args = {}
            normalized.append({"name": tool_name, "arguments": args})
        return normalized

    @staticmethod
    def _extract_user_message(text: str) -> str:
        """Try explicit USER_MESSAGE field extraction.

        Falls back to grabbing everything before the INTERNAL_JSON marker
        when the LLM does not emit an explicit ``USER_MESSAGE:`` label.
        """
        match = USER_MESSAGE_PATTERN.search(text)
        if match:
            return match.group(1).strip()

        # Fallback: split on INTERNAL_JSON marker (with optional markdown bold)
        split = re.split(
            r"\n\s*\*{0,2}INTERNAL_JSON\*{0,2}\s*:?\s*\*{0,2}",
            text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )
        if len(split) >= 2 and split[0].strip():
            return split[0].strip()

        return ""

    @staticmethod
    def _try_parse_json_block(text: str) -> dict[str, Any] | None:
        """Parse first ```json block as INTERNAL_JSON candidate."""
        match = JSON_BLOCK_PATTERN.search(text)
        if not match:
            return None
        json_candidate = ResponseParser._extract_balanced_json_object(match.group(1))
        if json_candidate is None:
            return None
        return ResponseParser._loads_json(json_candidate)

    @staticmethod
    def _try_parse_internal_marker(text: str) -> dict[str, Any] | None:
        """Parse content after INTERNAL_JSON marker."""
        match = INTERNAL_JSON_PATTERN.search(text)
        if not match:
            return None
        json_candidate = ResponseParser._extract_balanced_json_object(text[match.end() :])
        if json_candidate is None:
            return None
        return ResponseParser._loads_json(json_candidate)

    @staticmethod
    def _try_parse_whole_json(text: str) -> dict[str, Any] | None:
        """Parse entire response as JSON object."""
        json_candidate = ResponseParser._extract_balanced_json_object(text)
        if json_candidate is None:
            return None
        return ResponseParser._loads_json(json_candidate)

    @staticmethod
    def _extract_internal_data(text: str) -> dict[str, Any]:
        """Extract INTERNAL_JSON or raise a dedicated parser error."""
        internal_data = ResponseParser._try_parse_json_block(text)
        if internal_data is None:
            internal_data = ResponseParser._try_parse_internal_marker(text)
        if internal_data is None:
            internal_data = ResponseParser._try_parse_whole_json(text)
        if internal_data is None:
            raise MissingStructuredOutputError
        return internal_data

    @staticmethod
    def _loads_json(value: str) -> dict[str, Any] | None:
        """Load a JSON object safely."""
        try:
            loaded = orjson.loads(value)
        except orjson.JSONDecodeError:
            return None
        if not isinstance(loaded, dict):
            return None
        internal_json = loaded.get("internal_json")
        if isinstance(internal_json, dict):
            return cast(dict[str, Any], internal_json)
        return cast(dict[str, Any], loaded)

    @staticmethod
    def _extract_balanced_json_object(text: str) -> str | None:
        """Extract the first balanced JSON object from arbitrary text."""
        start_index = text.find("{")
        if start_index == -1:
            return None

        depth = 0
        in_string = False
        escaped = False

        for index in range(start_index, len(text)):
            char = text[index]

            if escaped:
                escaped = False
                continue

            if char == "\\" and in_string:
                escaped = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start_index : index + 1]

        return None

    @staticmethod
    def _normalize_string_list(value: Any) -> list[str]:
        """Normalize list-like values into stripped string arrays."""
        if not isinstance(value, list):
            return []
        normalized: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text:
                normalized.append(text)
        return normalized

    @staticmethod
    def _normalize_intent_value(value: Any, tool_calls: list[dict[str, Any]] | None = None) -> str:
        """Map legacy or drifted intents back onto the canonical runtime contract."""
        intent = str(value or "").strip().lower()
        if not intent:
            return ""
        if intent in _CANONICAL_INTENTS:
            return intent
        if intent in _INTENT_ALIASES:
            return _INTENT_ALIASES[intent]
        if intent.endswith("_request"):
            compact = intent.removesuffix("_request")
            if compact in _CANONICAL_INTENTS:
                return compact

        tool_names = [
            str(item.get("tool") or item.get("name") or "").strip().lower()
            for item in (tool_calls or [])
            if isinstance(item, dict)
        ]
        if "booking_availability" in tool_names:
            return Intent.STAY_AVAILABILITY.value
        if "booking_quote" in tool_names:
            return Intent.STAY_QUOTE.value
        if "stay_create_hold" in tool_names:
            return Intent.STAY_BOOKING_CREATE.value
        if any(name.startswith("restaurant_") for name in tool_names):
            if any("availability" in name for name in tool_names):
                return Intent.RESTAURANT_AVAILABILITY.value
            return Intent.RESTAURANT_BOOKING_CREATE.value
        if any(name.startswith("transfer_") for name in tool_names):
            if any("booking" in name for name in tool_names):
                return Intent.TRANSFER_BOOKING_CREATE.value
            return Intent.TRANSFER_INFO.value
        if any(name.startswith("room_service_") for name in tool_names):
            return Intent.ROOM_SERVICE_ORDER.value

        if "greet" in intent or "hello" in intent:
            return Intent.GREETING.value
        if "restaurant" in intent and ("reservation" in intent or "booking" in intent):
            return Intent.RESTAURANT_BOOKING_CREATE.value
        if "restaurant" in intent and "availability" in intent:
            return Intent.RESTAURANT_AVAILABILITY.value
        if "transfer" in intent and ("reservation" in intent or "booking" in intent):
            return Intent.TRANSFER_BOOKING_CREATE.value
        if "transfer" in intent:
            return Intent.TRANSFER_INFO.value
        if "availability" in intent:
            return Intent.STAY_AVAILABILITY.value
        if "quote" in intent or "price" in intent:
            return Intent.STAY_QUOTE.value
        return Intent.OTHER.value

    @staticmethod
    def _normalize_state_value(value: Any) -> str:
        """Map legacy or drifted state values onto the canonical state set."""
        state = str(value or "").strip()
        if not state:
            return ""
        lowered = state.lower()
        if lowered in _STATE_ALIASES:
            return _STATE_ALIASES[lowered]
        upper_state = state.upper()
        if upper_state in _CANONICAL_STATES or upper_state in _PASSTHROUGH_STATES:
            return upper_state
        if lowered.startswith("awaiting_") or lowered.startswith("collecting_") or lowered.startswith("missing_"):
            return ConversationState.NEEDS_VERIFICATION.value
        if "confirm" in lowered:
            return ConversationState.NEEDS_CONFIRMATION.value
        if "approval" in lowered:
            return ConversationState.PENDING_APPROVAL.value
        if "payment" in lowered:
            return ConversationState.PENDING_PAYMENT.value
        if "handoff" in lowered or "human" in lowered:
            return ConversationState.HANDOFF.value
        if "closed" in lowered:
            return ConversationState.CLOSED.value
        if "tool" in lowered or "processing" in lowered or "running" in lowered:
            return ConversationState.TOOL_RUNNING.value
        return ConversationState.NEEDS_VERIFICATION.value

    @staticmethod
    def _normalize_object_list(value: Any) -> list[dict[str, Any]]:
        """Normalize list-like values into object arrays."""
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _normalize_handoff(value: Any) -> dict[str, Any]:
        """Normalize handoff payload into a predictable object."""
        if isinstance(value, dict):
            return {
                "needed": bool(value.get("needed")),
                **{key: item for key, item in value.items() if key != "needed"},
            }
        if isinstance(value, bool):
            return {"needed": value}
        return {"needed": False}

    @staticmethod
    def _normalize_escalation(value: Any) -> dict[str, Any]:
        """Normalize escalation payload into a predictable object."""
        if isinstance(value, dict):
            normalized = dict(value)
            normalized["level"] = str(normalized.get("level") or "L0")
            normalized["route_to_role"] = str(normalized.get("route_to_role") or "NONE")
            return normalized
        return {"level": "L0", "route_to_role": "NONE"}

    @staticmethod
    def _normalize_internal_data(data: dict[str, Any]) -> dict[str, Any]:
        """Coerce common LLM schema slips into the expected INTERNAL_JSON shape."""
        normalized = dict(data)
        normalized["language"] = str(normalized.get("language") or "tr")
        normalized["entities"] = normalized.get("entities") if isinstance(normalized.get("entities"), dict) else {}
        normalized["required_questions"] = ResponseParser._normalize_string_list(normalized.get("required_questions"))
        normalized["tool_calls"] = ResponseParser._normalize_object_list(normalized.get("tool_calls"))
        normalized["intent"] = ResponseParser._normalize_intent_value(
            normalized.get("intent"),
            normalized["tool_calls"],
        )
        normalized["state"] = ResponseParser._normalize_state_value(normalized.get("state"))
        normalized["notifications"] = ResponseParser._normalize_object_list(normalized.get("notifications"))
        normalized["handoff"] = ResponseParser._normalize_handoff(normalized.get("handoff"))
        normalized["risk_flags"] = ResponseParser._normalize_string_list(normalized.get("risk_flags"))
        normalized["escalation"] = ResponseParser._normalize_escalation(normalized.get("escalation"))
        normalized["next_step"] = str(normalized.get("next_step") or "")
        return normalized

    @staticmethod
    def _build_parser_error_internal_json(reason: str) -> InternalJSON:
        """Create explicit parser error metadata instead of silently defaulting to an empty payload."""
        return InternalJSON(
            entities={
                STRUCTURED_OUTPUT_ERROR_KEY: {
                    "reason": reason,
                    "applied": True,
                }
            },
            risk_flags=["STRUCTURED_OUTPUT_ERROR"],
            next_step="recover_from_structured_output_error",
        )

    @staticmethod
    def _fallback_user_message(text: str, internal_json: InternalJSON) -> str:
        """Get a safe user message when explicit USER_MESSAGE is missing."""
        if text and not text.startswith("{"):
            return text
        next_step = internal_json.next_step.strip()
        if next_step:
            return next_step
        return "Talebinizi aldim. En kisa surede yardimci olacagim."
