"""Unit tests for Chat Lab feedback and import services."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from pydantic import ValidationError

from velox.core.chat_lab_feedback import ChatLabFeedbackService
from velox.models.chat_lab_feedback import ChatLabFeedbackRequest, ChatLabImportRequest
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


def _build_service(
    tmp_path: Path,
    conversation: Conversation,
    messages: list[Message],
) -> ChatLabFeedbackService:
    return ChatLabFeedbackService(
        repository=_FakeConversationRepository(conversation, messages),
        feedback_root=tmp_path / "chat_lab_feedback",
        imports_root=tmp_path / "chat_lab_imports",
    )


def _conversation_with_messages() -> tuple[Conversation, list[Message], str]:
    conversation = Conversation(
        id=uuid4(),
        hotel_id=21966,
        phone_hash="hash",
        phone_display="test_user_123",
        language="tr",
    )
    assistant_uuid = uuid4()
    messages = [
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role="user",
            content="Restoran menusu nedir?",
            created_at=datetime(2026, 3, 10, 10, 0, tzinfo=UTC),
        ),
        Message(
            id=assistant_uuid,
            conversation_id=conversation.id,
            role="assistant",
            content="Menuyu daha sonra paylasirim.",
            internal_json={
                "intent": "faq_menu",
                "state": "NEEDS_VERIFICATION",
                "risk_flags": [],
                "tool_calls": [{"name": "faq.lookup_menu"}],
            },
            created_at=datetime(2026, 3, 10, 10, 1, tzinfo=UTC),
        ),
    ]
    return conversation, messages, str(assistant_uuid)


@pytest.mark.asyncio
async def test_feedback_service_saves_bad_feedback_to_rating_category_path(tmp_path: Path) -> None:
    conversation, messages, assistant_id = _conversation_with_messages()
    service = _build_service(tmp_path, conversation, messages)

    response = await service.submit_feedback(
        ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=assistant_id,
            rating=2,
            category="yanlis_bilgi",
            tags=["eksik_bilgi", "tool_output_celiskisi"],
            gold_standard="Menunun guncel fiyati icin once hangi bolum soruldugu netlestirilmelidir.",
            notes="Admin notu",
        )
    )

    assert response.status == "saved"
    assert response.storage_group == "bad_feedback"
    assert response.category == "yanlis_bilgi"
    saved_files = sorted((tmp_path / "chat_lab_feedback").rglob("*.yaml"))
    assert len(saved_files) == 1
    assert "rating_2" in str(saved_files[0])
    assert "yanlis_bilgi" in str(saved_files[0])

    payload = yaml.safe_load(saved_files[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "chat_lab_feedback.v1"
    assert payload["input"] == "Restoran menusu nedir?"
    assert payload["output"] == "Menuyu daha sonra paylasirim."
    assert payload["tags"] == ["eksik_bilgi", "tool_output_celiskisi"]


@pytest.mark.asyncio
async def test_feedback_catalog_includes_eksik_bilgi_category(tmp_path: Path) -> None:
    conversation, messages, _assistant_id = _conversation_with_messages()
    service = _build_service(tmp_path, conversation, messages)

    response = await service.get_catalog()

    assert any(item.key == "eksik_bilgi" for item in response.categories)


@pytest.mark.asyncio
async def test_feedback_service_saves_non_approved_five_rating_under_reviewed(tmp_path: Path) -> None:
    conversation, messages, assistant_id = _conversation_with_messages()
    service = _build_service(tmp_path, conversation, messages)

    response = await service.submit_feedback(
        ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=assistant_id,
            rating=5,
            approved_example=False,
            notes="Dogru cevap",
        )
    )

    assert response.status == "saved"
    assert response.storage_group == "good_feedback"
    assert response.approved_example is False
    saved_files = sorted((tmp_path / "chat_lab_feedback").rglob("*.yaml"))
    assert len(saved_files) == 1
    assert "good_feedback" in str(saved_files[0])
    assert "reviewed" in str(saved_files[0])


@pytest.mark.asyncio
async def test_list_import_files_only_returns_json(tmp_path: Path) -> None:
    conversation, messages, _assistant_id = _conversation_with_messages()
    service = _build_service(tmp_path, conversation, messages)
    imports_root = tmp_path / "chat_lab_imports"
    imports_root.mkdir()
    (imports_root / "alpha.json").write_text('{"messages":[]}', encoding="utf-8")
    (imports_root / "ignore.txt").write_text("x", encoding="utf-8")

    response = await service.list_import_files()

    assert [item.filename for item in response.items] == ["alpha.json"]


@pytest.mark.asyncio
async def test_load_import_requires_role_mapping_when_roles_missing(tmp_path: Path) -> None:
    conversation, messages, _assistant_id = _conversation_with_messages()
    service = _build_service(tmp_path, conversation, messages)
    imports_root = tmp_path / "chat_lab_imports"
    imports_root.mkdir()
    (imports_root / "905332227788__sample.json").write_text(
        json.dumps(
            {
                "schema_version": "chat_lab_import.v1",
                "source_type": "imported_test",
                "participants": [
                    {"phone": "905332227788", "label": "Musteri"},
                    {"phone": "velox_bot", "label": "Asistan"},
                ],
                "messages": [
                    {
                        "id": "m1",
                        "from": "905332227788",
                        "content": "Merhaba",
                        "timestamp": "2026-03-10T10:00:00+00:00",
                    },
                    {
                        "id": "m2",
                        "from": "velox_bot",
                        "content": "Merhaba",
                        "timestamp": "2026-03-10T10:01:00+00:00",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    response = await service.load_import(ChatLabImportRequest(filename="905332227788__sample.json"))

    assert response.status == "role_mapping_required"
    assert response.source_type == "imported_test"
    assert [item.phone for item in response.participants] == ["905332227788", "velox_bot"]


@pytest.mark.asyncio
async def test_load_import_returns_ready_when_role_mapping_supplied(tmp_path: Path) -> None:
    conversation, messages, _assistant_id = _conversation_with_messages()
    service = _build_service(tmp_path, conversation, messages)
    imports_root = tmp_path / "chat_lab_imports"
    imports_root.mkdir()
    (imports_root / "sample.json").write_text(
        """
{
  "schema_version": "chat_lab_import.v1",
  "source_type": "imported_real",
  "messages": [
    {
      "id": "m1",
      "from": "905332227788",
      "content": "Merhaba",
      "timestamp": "2026-03-10T10:00:00+00:00"
    },
    {
      "id": "m2",
      "from": "velox_bot",
      "content": "Hos geldiniz",
      "timestamp": "2026-03-10T10:01:00+00:00",
      "internal_json": {"intent": "greeting"}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    response = await service.load_import(
        ChatLabImportRequest(
            filename="sample.json",
            role_mapping={
                "905332227788": "user",
                "velox_bot": "assistant",
            },
        )
    )

    assert response.status == "ready"
    assert response.source_type == "imported_real"
    assert [message.role for message in response.messages] == ["user", "assistant"]
    assert response.messages[1].internal_json == {"intent": "greeting"}


def test_feedback_request_requires_gold_standard_and_category_for_low_ratings() -> None:
    with pytest.raises(ValidationError):
        ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=str(uuid4()),
            rating=2,
            gold_standard="   ",
        )
