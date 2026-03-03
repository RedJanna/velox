"""Parse LLM output into USER_MESSAGE and INTERNAL_JSON."""

import re
from typing import Any

import orjson
import structlog
from pydantic import ValidationError

from velox.models.conversation import InternalJSON, LLMResponse

logger = structlog.get_logger(__name__)

JSON_BLOCK_PATTERN = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
INTERNAL_JSON_PATTERN = re.compile(r"INTERNAL_JSON\s*:\s*(\{.*\})", re.DOTALL | re.IGNORECASE)
USER_MESSAGE_PATTERN = re.compile(r"USER_MESSAGE\s*:\s*(.+?)(?:\nINTERNAL_JSON\s*:|$)", re.DOTALL | re.IGNORECASE)


class ResponseParser:
    """Parses model raw text into structured Velox response object."""

    @staticmethod
    def parse(raw_content: str) -> LLMResponse:
        """Parse LLM response using layered strategies with safe fallback."""
        text = raw_content.strip()

        user_message = ResponseParser._extract_user_message(text)

        internal_data = ResponseParser._try_parse_json_block(text)
        if internal_data is None:
            internal_data = ResponseParser._try_parse_internal_marker(text)
        if internal_data is None:
            internal_data = ResponseParser._try_parse_whole_json(text)
        if internal_data is None:
            internal_data = {}

        internal_json = ResponseParser.validate_internal_json(internal_data)
        if not user_message:
            user_message = ResponseParser._fallback_user_message(text, internal_json)

        return LLMResponse(user_message=user_message, internal_json=internal_json)

    @staticmethod
    def validate_internal_json(data: dict[str, Any]) -> InternalJSON:
        """Validate/coerce INTERNAL_JSON to model defaults on failure."""
        try:
            return InternalJSON.model_validate(data)
        except ValidationError:
            logger.warning("llm_internal_json_invalid", error_type="ValidationError")
            return InternalJSON()

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
        """Try explicit USER_MESSAGE field extraction."""
        match = USER_MESSAGE_PATTERN.search(text)
        if not match:
            return ""
        return match.group(1).strip()

    @staticmethod
    def _try_parse_json_block(text: str) -> dict[str, Any] | None:
        """Parse first ```json block as INTERNAL_JSON candidate."""
        match = JSON_BLOCK_PATTERN.search(text)
        if not match:
            return None
        return ResponseParser._loads_json(match.group(1))

    @staticmethod
    def _try_parse_internal_marker(text: str) -> dict[str, Any] | None:
        """Parse content after INTERNAL_JSON marker."""
        match = INTERNAL_JSON_PATTERN.search(text)
        if not match:
            return None
        return ResponseParser._loads_json(match.group(1))

    @staticmethod
    def _try_parse_whole_json(text: str) -> dict[str, Any] | None:
        """Parse entire response as JSON object."""
        return ResponseParser._loads_json(text)

    @staticmethod
    def _loads_json(value: str) -> dict[str, Any] | None:
        """Load a JSON object safely."""
        try:
            loaded = orjson.loads(value)
        except orjson.JSONDecodeError:
            return None
        if not isinstance(loaded, dict):
            return None
        if "internal_json" in loaded and isinstance(loaded.get("internal_json"), dict):
            return loaded["internal_json"]
        return loaded

    @staticmethod
    def _fallback_user_message(text: str, internal_json: InternalJSON) -> str:
        """Get a safe user message when explicit USER_MESSAGE is missing."""
        if text and not text.startswith("{"):
            return text
        next_step = internal_json.next_step.strip()
        if next_step:
            return next_step
        return "Talebinizi aldim. En kisa surede yardimci olacagim."
