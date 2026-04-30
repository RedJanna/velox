"""Tests for the stateless admin response preview flow."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from velox.api.middleware.auth import TokenData
from velox.api.routes import admin_response_preview
from velox.config.constants import Role
from velox.core.response_preview import (
    PreviewToolExecutor,
    ResponsePreviewResult,
    build_response_preview_messages,
    filter_preview_tool_definitions,
    generate_response_preview,
)
from velox.llm.function_registry import get_tool_definitions
from velox.models.conversation import InternalJSON


class DummyPromptBuilder:
    """Minimal prompt builder that exposes hotel context without conversation history."""

    def build_system_prompt(self, hotel_id: int) -> str:
        return f"HOTEL_CONTEXT hotel_id={hotel_id}; name=Preview Hotel"


class DummyLLMClient:
    """LLM fake that records the messages passed to the response-preview flow."""

    primary_model = "gpt-test"

    def __init__(
        self,
        *,
        raw_content: str | None = None,
        translation_payload: dict[str, str] | None = None,
    ) -> None:
        self.messages: list[dict[str, Any]] = []
        self.translation_messages: list[dict[str, Any]] = []
        self.tools: list[dict[str, Any]] = []
        self.raw_content = raw_content
        self.translation_payload = translation_payload or {
            "source_language": "en",
            "target_language": "tr",
            "translated_reply": "Kassandra Oludeniz için otel verilerindeki bilgileri paylaşabilirim.",
        }

    async def run_tool_call_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_iterations: int,
        trace_context: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        _ = (tool_executor, max_iterations, trace_context)
        self.messages = messages
        self.tools = tools
        if self.raw_content is not None:
            return self.raw_content, []
        return (
            'USER_MESSAGE: Kassandra Oludeniz için müsait otel bilgilerini paylaşabilirim.\n'
            'INTERNAL_JSON: {"language":"tr","intent":"faq_info","state":"INTENT_DETECTED",'
            '"entities":{},"required_questions":[],"tool_calls":[],"notifications":[],'
            '"handoff":{"needed":false},"risk_flags":[],'
            '"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"answer_sent"}',
            [],
        )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> dict[str, Any]:
        _ = (tools, model, response_format, tool_choice, parallel_tool_calls)
        self.translation_messages = messages
        return {"choices": [{"message": {"content": json.dumps(self.translation_payload)}}]}

    async def repair_structured_output(self, **kwargs: Any) -> dict[str, Any] | None:
        _ = kwargs
        return None


class RecordingDispatcher:
    """Tool dispatcher fake that records normalized read-only calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((name, kwargs))
        return {"ok": True, "hotel_id": kwargs.get("hotel_id")}


def _message_text(messages: list[dict[str, Any]]) -> str:
    return "\n".join(str(message.get("content") or "") for message in messages)


def test_build_response_preview_messages_contains_only_single_question() -> None:
    messages = build_response_preview_messages(
        hotel_id=1,
        question="  Do you have airport transfer?  ",
        language="en",
        response_style="concise",
        prompt_builder=DummyPromptBuilder(),  # type: ignore[arg-type]
        current_date="2026-04-30",
    )

    assert [message["role"] for message in messages] == ["system", "system", "user", "system"]
    assert messages[2]["content"] == "Do you have airport transfer?"
    joined = _message_text(messages).lower()
    assert "previous messages" in joined
    assert "not chat lab" in joined
    assert "response_language_request: en" in joined
    assert "response_style_request: concise" in joined
    assert "british english" in joined
    assert "conversation_id" not in joined


def test_preview_tool_definitions_are_read_only() -> None:
    tool_names = [
        item["function"]["name"]
        for item in filter_preview_tool_definitions(get_tool_definitions())
    ]

    assert "faq_lookup" in tool_names
    assert "hotel_info_lookup" in tool_names
    assert "stay_create_hold" not in tool_names
    assert "handoff_create_ticket" not in tool_names
    assert "crm_log" not in tool_names


@pytest.mark.asyncio
async def test_preview_tool_executor_blocks_side_effects_and_enforces_hotel_scope() -> None:
    dispatcher = RecordingDispatcher()
    executor = PreviewToolExecutor(dispatcher=dispatcher, hotel_id=7)  # type: ignore[arg-type]

    await executor("faq_lookup", {"hotel_id": 999, "query": "pool", "language": "EN"})
    await executor("stay_create_hold", {"hotel_id": 999, "guest_name": "Ada Lovelace"})

    assert dispatcher.calls == [("faq_lookup", {"hotel_id": 7, "query": "pool", "language": "EN"})]
    assert executor.tool_calls[0].blocked is False
    assert executor.tool_calls[0].arguments["hotel_id"] == 7
    assert executor.tool_calls[1].blocked is True
    assert executor.tool_calls[1].arguments["guest_name"] == "[redacted]"


@pytest.mark.asyncio
async def test_generate_response_preview_does_not_persist_or_create_history() -> None:
    llm_client = DummyLLMClient()

    result = await generate_response_preview(
        hotel_id=1,
        question="Is breakfast included?",
        language="en",
        response_style="warm",
        dispatcher=None,
        llm_client=llm_client,  # type: ignore[arg-type]
        prompt_builder=DummyPromptBuilder(),  # type: ignore[arg-type]
    )

    assert result.requested_language == "en"
    assert result.response_style == "warm"
    assert result.history_used is False
    assert result.history_created is False
    assert result.persisted is False
    assert result.created_records == []
    assert result.internal_json.notifications == []
    assert result.internal_json.entities["response_preview"]["history_used"] is False
    assert result.internal_json.entities["response_preview"]["history_created"] is False
    assert [message["role"] for message in llm_client.messages] == ["system", "system", "user", "system"]


@pytest.mark.asyncio
async def test_non_turkish_preview_returns_admin_translation_without_history() -> None:
    llm_client = DummyLLMClient(
        raw_content=(
            "USER_MESSAGE: Breakfast is served in the restaurant area according to the hotel data.\n"
            'INTERNAL_JSON: {"language":"en","intent":"faq_info","state":"INTENT_DETECTED",'
            '"entities":{},"required_questions":[],"tool_calls":[],"notifications":[],'
            '"handoff":{"needed":false},"risk_flags":[],'
            '"escalation":{"level":"L0","route_to_role":"NONE"},"next_step":"answer_sent"}'
        ),
        translation_payload={
            "source_language": "en",
            "target_language": "tr",
            "translated_reply": "Otel verilerine göre kahvaltı restoran alanında servis edilir.",
        },
    )

    result = await generate_response_preview(
        hotel_id=1,
        question="What time is breakfast?",
        language="en",
        response_style="professional",
        dispatcher=None,
        llm_client=llm_client,  # type: ignore[arg-type]
        prompt_builder=DummyPromptBuilder(),  # type: ignore[arg-type]
    )

    assert result.translation.available is True
    assert result.translation.source_language == "en"
    assert result.translation.target_language == "tr"
    assert "kahvaltı" in result.translation.translated_reply.lower()
    assert result.history_created is False
    assert result.internal_json.entities["response_preview"]["admin_translation"] == {
        "available": True,
        "source_language": "en",
        "target_language": "tr",
        "history_used": False,
        "history_created": False,
        "persisted": False,
    }
    translation_prompt = _message_text(llm_client.translation_messages).lower()
    assert "conversation history" in translation_prompt
    assert "british english" in translation_prompt
    assert "what time is breakfast" not in translation_prompt


@pytest.mark.asyncio
async def test_admin_response_preview_route_delegates_without_session_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_generate_response_preview(**kwargs: Any) -> ResponsePreviewResult:
        captured.update(kwargs)
        return ResponsePreviewResult(
            hotel_id=21966,
            question_chars=11,
            reply="Pool hours are available in the hotel data.",
            internal_json=InternalJSON(
                language="en",
                intent="faq_info",
                state="INTENT_DETECTED",
                entities={},
                next_step="answer_sent",
            ),
            model="gpt-test",
            duration_ms=12,
        )

    monkeypatch.setattr(admin_response_preview, "generate_response_preview", fake_generate_response_preview)
    payload = admin_response_preview.ResponsePreviewGenerateRequest(
        hotel_id=21966,
        question="Pool hours?",
        language="en",
        response_style="concise",
    )
    user = TokenData(
        user_id=1,
        hotel_id=21966,
        username="ops",
        role=Role.OPS,
        permissions={"conversations:read"},
    )
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(tool_dispatcher="dispatcher")))

    result = await admin_response_preview.generate_admin_response_preview(
        payload,
        request,  # type: ignore[arg-type]
        user,
    )

    assert result.history_created is False
    assert captured["hotel_id"] == 21966
    assert captured["question"] == "Pool hours?"
    assert captured["language"] == "en"
    assert captured["response_style"] == "concise"
    assert captured["dispatcher"] == "dispatcher"


def test_response_preview_request_normalizes_invalid_controls() -> None:
    payload = admin_response_preview.ResponsePreviewGenerateRequest(
        hotel_id=21966,
        question="Breakfast?",
        language="pirate",
        response_style="extra-long",
    )

    assert payload.language == "auto"
    assert payload.response_style == "professional"
