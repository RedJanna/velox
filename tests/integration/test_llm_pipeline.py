"""Integration tests for LLM client tool-calling pipeline with mocked OpenAI."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock

import pytest

from velox.config.settings import settings
from velox.llm.client import LLMClient


class _FakeOpenAIResponse:
    """Simple response wrapper exposing model_dump like openai SDK objects."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self) -> dict[str, Any]:
        return self._payload


@pytest.mark.asyncio
async def test_user_greeting_returns_greeting_message(mock_openai: AsyncMock) -> None:
    """Greeting message should pass through chat_with_tools content path."""
    mock_openai.chat.completions.create.return_value = _FakeOpenAIResponse(
        {"choices": [{"message": {"content": "Merhaba, hos geldiniz!", "tool_calls": []}}], "usage": {}}
    )
    client = LLMClient(settings)
    client.client = mock_openai
    content, calls = await client.chat_with_tools(messages=[{"role": "user", "content": "Merhaba"}], tools=[])
    assert "Merhaba" in content
    assert calls == []


@pytest.mark.asyncio
async def test_availability_question_emits_booking_tool_call(mock_openai: AsyncMock) -> None:
    """Tool-calling response should expose booking availability call metadata."""
    mock_openai.chat.completions.create.return_value = _FakeOpenAIResponse(
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "tc1",
                                "type": "function",
                                "function": {
                                    "name": "booking_availability",
                                    "arguments": '{"hotel_id":21966,"adults":2}',
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {},
        }
    )
    client = LLMClient(settings)
    client.client = mock_openai
    _, calls = await client.chat_with_tools(messages=[{"role": "user", "content": "Müsaitlik?"}], tools=[{}])
    assert len(calls) == 1
    assert calls[0]["name"] == "booking_availability"


@pytest.mark.asyncio
async def test_tool_result_is_followed_by_formatted_user_response(mock_openai: AsyncMock) -> None:
    """Tool loop should call executor once then return final assistant content."""
    mock_openai.chat.completions.create.side_effect = [
        _FakeOpenAIResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "tc1",
                                    "type": "function",
                                    "function": {"name": "booking_availability", "arguments": '{"adults":2}'},
                                }
                            ],
                        }
                    }
                ],
                "usage": {},
            }
        ),
        _FakeOpenAIResponse(
            {"choices": [{"message": {"content": "Uygun odalar bulundu.", "tool_calls": []}}], "usage": {}}
        ),
    ]
    tool_executor: Callable[[str, Any], Awaitable[Any]] = AsyncMock(return_value='{"available":true}')
    client = LLMClient(settings)
    client.client = mock_openai
    content, executed = await client.run_tool_call_loop(
        messages=[{"role": "user", "content": "15-18 Temmuz 2 kisi"}],
        tools=[{}],
        tool_executor=tool_executor,
    )
    assert "Uygun odalar" in content
    assert len(executed) == 1
    assert executed[0]["name"] == "booking_availability"


@pytest.mark.asyncio
async def test_multi_turn_flow_greeting_to_hold_with_tool_calls(mock_openai: AsyncMock) -> None:
    """Multi-turn style loop should execute availability->quote->hold tool chain."""
    mock_openai.chat.completions.create.side_effect = [
        _FakeOpenAIResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "tc-a",
                                    "type": "function",
                                    "function": {"name": "booking_availability", "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ],
                "usage": {},
            }
        ),
        _FakeOpenAIResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {"id": "tc-b", "type": "function", "function": {"name": "booking_quote", "arguments": "{}"}}
                            ],
                        }
                    }
                ],
                "usage": {},
            }
        ),
        _FakeOpenAIResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {"id": "tc-c", "type": "function", "function": {"name": "stay_create_hold", "arguments": "{}"}}
                            ],
                        }
                    }
                ],
                "usage": {},
            }
        ),
        _FakeOpenAIResponse(
            {"choices": [{"message": {"content": "Hold olusturuldu, onay bekleniyor.", "tool_calls": []}}], "usage": {}}
        ),
    ]
    tool_executor = AsyncMock(return_value='{"ok":true}')
    client = LLMClient(settings)
    client.client = mock_openai
    content, executed = await client.run_tool_call_loop(
        messages=[{"role": "user", "content": "Merhaba"}],
        tools=[{}],
        tool_executor=tool_executor,
        max_iterations=6,
    )
    assert "onay bekleniyor" in content
    assert [item["name"] for item in executed] == [
        "booking_availability",
        "booking_quote",
        "stay_create_hold",
    ]
