"""Unit tests for Chat Lab feedback service."""

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import yaml
from pydantic import ValidationError

from velox.core.chat_lab_feedback import ChatLabFeedbackService
from velox.models.chat_lab_feedback import ChatLabFeedbackRequest
from velox.models.conversation import Conversation, Message


class _FakeConversationRepository:
    def __init__(self, conversation: Conversation, messages: list[Message]) -> None:
        self._conversation = conversation
        self._messages = messages

    async def get_active_by_phone(self, hotel_id: int, phone_hash: str) -> Conversation | None:
        _ = (hotel_id, phone_hash)
        return self._conversation

    async def get_messages(self, conversation_id, limit: int = 500, offset: int = 0) -> list[Message]:
        _ = (conversation_id, limit, offset)
        return self._messages


class _FakeModelsAPI:
    async def list(self) -> SimpleNamespace:
        return SimpleNamespace(
            data=[
                SimpleNamespace(id="gpt-4o-mini"),
                SimpleNamespace(id="gpt-4o"),
                SimpleNamespace(id="gpt-5"),
            ]
        )


class _FakeLLMClient:
    def __init__(self) -> None:
        self.client = SimpleNamespace(models=_FakeModelsAPI())
        self.primary_model = "gpt-4o-mini"

    async def chat_completion(self, messages, tools=None, model=None) -> dict:
        _ = (messages, tools, model)
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            "Erken giris talebinizi not aldim. "
                            "Musaitlik kesinlestiginde size net bilgi verebilirim."
                        )
                    }
                }
            ]
        }


def _template_file(directory: Path) -> Path:
    template_path = directory / "_TEMPLATE.yaml"
    template_path.write_text(
        (
            'code: "S000"\n'
            'name: "Template"\n'
            'description: "Template"\n'
            'category: "general"\n'
            'language: "tr"\n'
            "tags: []\n"
            "steps: []\n"
        ),
        encoding="utf-8",
    )
    return template_path


@pytest.mark.asyncio
async def test_feedback_service_generates_scenario_with_best_model(tmp_path: Path) -> None:
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir()
    template_path = _template_file(scenarios_dir)

    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        phone_display="test_user_123",
        language="tr",
    )
    assistant_message_id = uuid4()
    messages = [
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role="user",
            content="Yarin sabah otele erken girebilir miyim?",
            created_at=datetime(2026, 3, 10, 10, 0, tzinfo=UTC),
        ),
        Message(
            id=assistant_message_id,
            conversation_id=conversation.id,
            role="assistant",
            content="Evet, erken giris her zaman garanti edilir.",
            internal_json={
                "intent": "early_checkin_request",
                "state": "INTENT_DETECTED",
                "risk_flags": [],
                "tool_calls": [],
            },
            created_at=datetime(2026, 3, 10, 10, 0, 1, tzinfo=UTC),
        ),
    ]
    service = ChatLabFeedbackService(
        repository=_FakeConversationRepository(conversation, messages),
        llm_client=_FakeLLMClient(),
        scenarios_dir=scenarios_dir,
        template_path=template_path,
    )

    response = await service.submit_feedback(
        ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=assistant_message_id,
            rating=3,
            correction="Erken giris musaitlige gore teyit edilir; garanti verilemez.",
        )
    )

    assert response.status == "scenario_created"
    assert response.selected_model == "gpt-5"
    assert response.scenario_code == "S048"
    assert response.corrected_reply is not None

    scenario_files = sorted(scenarios_dir.glob("S*.yaml"))
    assert len(scenario_files) == 1
    scenario_data = yaml.safe_load(scenario_files[0].read_text(encoding="utf-8"))
    assert scenario_data["code"] == "S048"
    assert scenario_data["category"] == "guest_ops"
    assert scenario_data["feedback"]["selected_model"] == "gpt-5"
    assert scenario_data["steps"][0]["expect_intent"] == "early_checkin_request"
    assert scenario_data["steps"][0]["expect_reply_contains"]


@pytest.mark.asyncio
async def test_feedback_service_acknowledges_perfect_rating_without_file_write(tmp_path: Path) -> None:
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir()
    template_path = _template_file(scenarios_dir)

    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        phone_display="test_user_123",
        language="tr",
    )
    service = ChatLabFeedbackService(
        repository=_FakeConversationRepository(conversation, []),
        llm_client=_FakeLLMClient(),
        scenarios_dir=scenarios_dir,
        template_path=template_path,
    )

    response = await service.submit_feedback(
        ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=uuid4(),
            rating=5,
        )
    )

    assert response.status == "acknowledged"
    assert response.scenario_code is None
    assert list(scenarios_dir.glob("S*.yaml")) == []


def test_feedback_request_requires_correction_for_low_ratings() -> None:
    with pytest.raises(ValidationError):
        ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=uuid4(),
            rating=2,
            correction="   ",
        )
