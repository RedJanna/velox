"""OpenAI async client wrapper for chat completions and function calling."""

import asyncio
import time
from typing import Any

import structlog
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from velox.config.constants import TOOL_RETRY_BACKOFF_SECONDS
from velox.config.settings import Settings, settings

logger = structlog.get_logger(__name__)

LLM_TIMEOUT_SECONDS = 30.0
PRIMARY_RETRY_COUNT = 2
FALLBACK_RETRY_COUNT = 2

# Models that do NOT support the legacy `temperature` parameter or `max_tokens`.
# They require `max_completion_tokens` and only accept temperature=1.
_FIXED_TEMPERATURE_MODEL_PREFIXES = ("o1", "o3", "gpt-5")



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
    ) -> dict[str, Any]:
        """Send chat completion request with retry and fallback model."""
        preferred_model = model or self.primary_model
        if preferred_model != self.primary_model:
            return await self._request_with_retry(messages=messages, tools=tools, model_name=preferred_model)

        try:
            return await self._request_with_retry(messages=messages, tools=tools, model_name=self.primary_model)
        except LLMUnavailableError:
            logger.warning("llm_fallback_start", from_model=self.primary_model, to_model=self.fallback_model)
            return await self._request_with_retry(messages=messages, tools=tools, model_name=self.fallback_model)

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Chat with function calling and return content plus tool calls."""
        response = await self.chat_completion(messages=messages, tools=tools)
        choices = response.get("choices", [])
        if not choices:
            return "", []

        message = choices[0].get("message", {})
        content = str(message.get("content") or "")
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
        return content, tool_calls

    async def run_tool_call_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_iterations: int = 5,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Run iterative tool-calling loop until final content or max iterations."""
        working_messages = [dict(message) for message in messages]
        iteration = 0
        last_content = ""
        executed_calls: list[dict[str, Any]] = []

        while iteration < max_iterations:
            iteration += 1
            content, tool_calls = await self.chat_with_tools(messages=working_messages, tools=tools)
            last_content = content or last_content

            if not tool_calls:
                return content, executed_calls

            for tool_call in tool_calls:
                tool_name = str(tool_call.get("name") or "")
                tool_args = tool_call.get("arguments")
                tool_result = await tool_executor(tool_name, tool_args)
                executed_calls.append({"name": tool_name, "arguments": tool_args, "result": tool_result})

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

        logger.warning("llm_tool_loop_max_iterations_reached", max_iterations=max_iterations)
        return last_content, executed_calls

    async def _request_with_retry(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model_name: str,
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
                return response_dict
            except (RateLimitError, APITimeoutError, APIConnectionError) as error:
                last_error = error
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.warning(
                    "llm_call_retryable_error",
                    service="openai",
                    model=model_name,
                    error_type=type(error).__name__,
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
