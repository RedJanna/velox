"""OpenAI async client wrapper for chat completions and function calling."""

import asyncio
import time
from typing import Any, cast

import orjson
import structlog
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from velox.config.constants import TOOL_RETRY_BACKOFF_SECONDS
from velox.config.settings import Settings, settings
from velox.utils.metrics import record_structured_output_repair_outcome

logger = structlog.get_logger(__name__)

LLM_TIMEOUT_SECONDS = 30.0
PRIMARY_RETRY_COUNT = 2
FALLBACK_RETRY_COUNT = 2

# Models that do NOT support the legacy `temperature` parameter or `max_tokens`.
# They require `max_completion_tokens` and only accept temperature=1.
_FIXED_TEMPERATURE_MODEL_PREFIXES = ("o1", "o3", "gpt-5")

_STRUCTURED_OUTPUT_REPAIR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "user_message": {"type": "string"},
        "internal_json": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "language": {"type": "string"},
                "intent": {"type": "string"},
                "state": {"type": "string"},
                "entities": {"type": "object", "additionalProperties": True},
                "required_questions": {"type": "array", "items": {"type": "string"}},
                "tool_calls": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
                "notifications": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
                "handoff": {"type": "object", "additionalProperties": True},
                "risk_flags": {"type": "array", "items": {"type": "string"}},
                "escalation": {"type": "object", "additionalProperties": True},
                "next_step": {"type": "string"},
            },
            "required": [
                "language",
                "intent",
                "state",
                "entities",
                "required_questions",
                "tool_calls",
                "notifications",
                "handoff",
                "risk_flags",
                "escalation",
                "next_step",
            ],
        },
    },
    "required": ["user_message", "internal_json"],
}
_STRUCTURED_OUTPUT_REPAIR_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "velox_structured_output_repair",
        "strict": True,
        "schema": _STRUCTURED_OUTPUT_REPAIR_SCHEMA,
    },
}


def _extract_message_content(message: dict[str, Any]) -> str:
    """Normalize OpenAI message content into plain text."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text)
        return "\n".join(parts)
    return ""



class LLMUnavailableError(RuntimeError):
    """Raised when both primary and fallback models are unavailable."""


class LLMClient:
    """OpenAI client with retry, fallback model, and token usage logging."""

    def __init__(self, app_settings: Settings) -> None:
        self.client = AsyncOpenAI(api_key=app_settings.openai_api_key)
        self.primary_model = app_settings.openai_model
        self.fallback_model = app_settings.openai_fallback_model
        self.max_tokens = app_settings.openai_max_tokens
        self.temperature = app_settings.openai_temperature

    async def close(self) -> None:
        """Close underlying client resources."""
        await self.client.close()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> dict[str, Any]:
        """Send chat completion request with retry and fallback model."""
        preferred_model = model or self.primary_model
        if preferred_model != self.primary_model:
            return await self._request_with_retry(
                messages=messages,
                tools=tools,
                model_name=preferred_model,
                response_format=response_format,
                tool_choice=tool_choice,
                parallel_tool_calls=parallel_tool_calls,
            )

        try:
            return await self._request_with_retry(
                messages=messages,
                tools=tools,
                model_name=self.primary_model,
                response_format=response_format,
                tool_choice=tool_choice,
                parallel_tool_calls=parallel_tool_calls,
            )
        except LLMUnavailableError:
            logger.warning("llm_fallback_start", from_model=self.primary_model, to_model=self.fallback_model)
            return await self._request_with_retry(
                messages=messages,
                tools=tools,
                model_name=self.fallback_model,
                response_format=response_format,
                tool_choice=tool_choice,
                parallel_tool_calls=parallel_tool_calls,
            )

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        trace_context: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Chat with function calling and return content plus tool calls."""
        response = await self.chat_completion(
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            parallel_tool_calls=False if tools else None,
        )
        choices = response.get("choices", [])
        if not choices:
            return "", []

        message = choices[0].get("message", {})
        content = _extract_message_content(message)
        raw_tool_calls = message.get("tool_calls") or []

        tool_calls: list[dict[str, Any]] = []
        for call in raw_tool_calls:
            function_data = call.get("function", {})
            tool_calls.append(
                {
                    "id": call.get("id"),
                    "type": call.get("type", "function"),
                    "name": function_data.get("name"),
                    "arguments": function_data.get("arguments"),
                }
            )
        log_payload = {
            "raw_tool_call_names": [str(call.get("name") or "") for call in tool_calls],
            "raw_tool_call_count": len(tool_calls),
            "content_length": len(content),
            "has_internal_json_marker": "INTERNAL_JSON" in content,
        }
        if trace_context:
            log_payload.update(trace_context)
        logger.info("llm_tool_iteration_response", **log_payload)
        return content, tool_calls

    async def repair_structured_output(
        self,
        *,
        raw_content: str,
        language: str,
        parser_error_reason: str,
        current_intent: str | None = None,
        current_state: str | None = None,
        current_entities: dict[str, Any] | None = None,
        executed_calls: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        """Run a strict-schema repair pass for malformed assistant output."""
        record_structured_output_repair_outcome("attempted")
        fallback_state = str(current_state or "").strip() or "NEEDS_VERIFICATION"
        if fallback_state == "GREETING":
            fallback_state = "NEEDS_VERIFICATION"

        repair_hints = {
            "language": str(language or "tr"),
            "parser_error_reason": str(parser_error_reason or "unknown"),
            "fallback_intent": str(current_intent or "other"),
            "fallback_state": fallback_state,
            "fallback_entities": current_entities if isinstance(current_entities, dict) else {},
            "executed_tool_names": [
                str(item.get("name") or "").strip()
                for item in executed_calls or []
                if isinstance(item, dict) and str(item.get("name") or "").strip()
            ],
        }
        repair_messages = [
            {
                "role": "system",
                "content": (
                    "You repair malformed Velox assistant output into a strict JSON object. "
                    "Do not invent hotel facts, prices, availability, policies, or tool results. "
                    "Use only the raw assistant output and fallback hints below. "
                    "Preserve the guest-facing wording when possible. "
                    "If a field is missing, use the fallback hint or an empty safe default. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "FALLBACK_HINTS:\n"
                    f"{orjson.dumps(repair_hints).decode()}\n\n"
                    "RAW_ASSISTANT_OUTPUT:\n"
                    f"{raw_content}"
                ),
            },
        ]
        try:
            response = await self.chat_completion(
                messages=repair_messages,
                response_format=_STRUCTURED_OUTPUT_REPAIR_FORMAT,
            )
        except LLMUnavailableError:
            record_structured_output_repair_outcome("unavailable")
            logger.warning("llm_structured_output_repair_unavailable")
            return None

        choices = response.get("choices", [])
        if not choices:
            record_structured_output_repair_outcome("empty_choices")
            return None
        message = choices[0].get("message", {})
        content = _extract_message_content(message).strip()
        if not content:
            record_structured_output_repair_outcome("empty_content")
            return None
        try:
            payload = orjson.loads(content)
        except orjson.JSONDecodeError:
            record_structured_output_repair_outcome("invalid_json")
            logger.warning("llm_structured_output_repair_invalid_json", content_preview=content[:200])
            return None
        if not isinstance(payload, dict):
            record_structured_output_repair_outcome("invalid_payload")
            return None
        record_structured_output_repair_outcome("returned_payload")
        return cast(dict[str, Any], payload)

    async def run_tool_call_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_iterations: int = 5,
        trace_context: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Run iterative tool-calling loop until final content or max iterations."""
        working_messages = [dict(message) for message in messages]
        iteration = 0
        last_content = ""
        executed_calls: list[dict[str, Any]] = []

        loop_start_payload = {"max_iterations": max_iterations, "message_count": len(messages)}
        if trace_context:
            loop_start_payload.update(trace_context)
        logger.info("llm_tool_loop_started", **loop_start_payload)

        while iteration < max_iterations:
            iteration += 1
            content, tool_calls = await self.chat_with_tools(
                messages=working_messages,
                tools=tools,
                trace_context={
                    "iteration": iteration,
                    **(trace_context or {}),
                },
            )
            last_content = content or last_content

            if not tool_calls:
                completion_payload = {
                    "iteration": iteration,
                    "executed_call_count": len(executed_calls),
                    "executed_call_names": [str(call.get("name") or "") for call in executed_calls],
                    "content_length": len(content),
                }
                if trace_context:
                    completion_payload.update(trace_context)
                logger.info("llm_tool_loop_completed", **completion_payload)
                return content, executed_calls

            for tool_call in tool_calls:
                tool_name = str(tool_call.get("name") or "")
                tool_args = tool_call.get("arguments")
                tool_result = await tool_executor(tool_name, tool_args)
                executed_calls.append({"name": tool_name, "arguments": tool_args, "result": tool_result})
                execution_payload = {
                    "iteration": iteration,
                    "tool_name": tool_name,
                    "executed_call_count": len(executed_calls),
                }
                if trace_context:
                    execution_payload.update(trace_context)
                logger.info("llm_tool_call_executed", **execution_payload)

                working_messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": [
                            {
                                "id": tool_call.get("id"),
                                "type": "function",
                                "function": {"name": tool_name, "arguments": tool_args},
                            }
                        ],
                    }
                )
                working_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_name,
                        "content": tool_result if isinstance(tool_result, str) else str(tool_result),
                    }
                )

        warning_payload = {"max_iterations": max_iterations, "executed_call_count": len(executed_calls)}
        if trace_context:
            warning_payload.update(trace_context)
        logger.warning("llm_tool_loop_max_iterations_reached", **warning_payload)
        return last_content, executed_calls

    async def _request_with_retry(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model_name: str,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> dict[str, Any]:
        """Execute chat completion request with retry policy and structured logging."""
        max_attempts = PRIMARY_RETRY_COUNT + 1 if model_name == self.primary_model else FALLBACK_RETRY_COUNT + 1
        last_error: Exception | None = None

        # Build call kwargs; newer models (o1, o3, gpt-5.*) do not support
        # legacy `max_tokens` or custom `temperature`.
        is_fixed_temp = any(model_name.startswith(p) for p in _FIXED_TEMPERATURE_MODEL_PREFIXES)
        call_kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "timeout": LLM_TIMEOUT_SECONDS,
        }
        if tools:
            call_kwargs["tools"] = tools
        if response_format:
            call_kwargs["response_format"] = response_format
        if tool_choice is not None and tools:
            call_kwargs["tool_choice"] = tool_choice
        if parallel_tool_calls is not None and tools:
            call_kwargs["parallel_tool_calls"] = parallel_tool_calls
        if is_fixed_temp:
            call_kwargs["max_completion_tokens"] = self.max_tokens
        else:
            call_kwargs["max_tokens"] = self.max_tokens
            call_kwargs["temperature"] = self.temperature

        for attempt in range(1, max_attempts + 1):
            start = time.perf_counter()
            try:
                response = await self.client.chat.completions.create(**call_kwargs)
                response_dict = response.model_dump()
                usage = response_dict.get("usage", {})
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.info(
                    "llm_call_ok",
                    service="openai",
                    model=model_name,
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )
                return cast(dict[str, Any], response_dict)
            except (RateLimitError, APITimeoutError, APIConnectionError) as error:
                last_error = error
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.warning(
                    "llm_call_retryable_error",
                    service="openai",
                    model=model_name,
                    error_type=type(error).__name__,
                    error_detail=str(error)[:500],
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                )
                if attempt < max_attempts:
                    backoff_index = min(attempt - 1, len(TOOL_RETRY_BACKOFF_SECONDS) - 1)
                    await asyncio.sleep(TOOL_RETRY_BACKOFF_SECONDS[backoff_index])
                continue
            except Exception as error:
                last_error = error
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.warning(
                    "llm_call_non_retryable_error",
                    service="openai",
                    model=model_name,
                    error_type=type(error).__name__,
                    error_detail=str(error)[:500],
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                )
                break

        raise LLMUnavailableError(f"Model unavailable: {model_name}") from last_error


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(settings)
    return _llm_client


async def close_llm_client() -> None:
    """Close singleton LLM client."""
    global _llm_client
    if _llm_client is not None:
        await _llm_client.close()
        _llm_client = None
