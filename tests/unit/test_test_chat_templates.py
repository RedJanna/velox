"""Unit tests for Chat Lab template creation and sending."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from velox.api.routes import test_chat
from velox.api.routes.test_chat_ui import TEST_CHAT_HTML
from velox.api.routes.test_chat_ui_assets import TEST_CHAT_SCRIPT
from velox.models.hotel_profile import HotelProfile, LocalizedText


class _FakeAcquire:
    def __init__(self, conn) -> None:
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakePool:
    def __init__(self, conn) -> None:
        self._conn = conn

    def acquire(self):
        return _FakeAcquire(self._conn)


class _FakeConnection:
    def __init__(self, conversation_id) -> None:
        self._conversation_id = conversation_id

    async def fetchrow(self, query, *args):
        _ = args
        if "FROM conversations" in query:
            return {
                "id": self._conversation_id,
                "phone_display": "905551112233",
                "hotel_id": 21966,
            }
        return None

    async def fetchval(self, query, *args):
        _ = args
        if "SELECT content FROM messages" in query:
            return "Misafir gec cikis sordu"
        return None


class _FakeConversationRepository:
    def __init__(self) -> None:
        self.messages = []

    async def add_message(self, message):
        message.id = uuid4()
        self.messages.append(message)
        return message


class _FakeWhatsAppClient:
    def __init__(self) -> None:
        self.sent = []

    async def send_text_message(self, *, to: str, body: str, force: bool = False):
        self.sent.append({"to": to, "body": body, "force": force})
        return {"messages": [{"id": "wamid.template"}]}


def _request_with_json(payload: dict, pool) -> SimpleNamespace:
    async def _json():
        return payload

    app = SimpleNamespace(state=SimpleNamespace(db_pool=pool))
    return SimpleNamespace(app=app, json=_json)


@pytest.mark.asyncio
async def test_create_chat_template_returns_created_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": "late_checkout_info_tr",
        "title": "Geç Check-out Bilgilendirme",
        "intent": "late_checkout",
        "state": "INFO",
        "language": "tr",
        "template": "Merhaba {name}",
    }
    monkeypatch.setattr(test_chat, "create_template_definition", lambda **kwargs: created)

    body = test_chat.ChatTemplateCreateRequest(
        title="Geç Check-out Bilgilendirme",
        intent="late_checkout",
        state="INFO",
        language="tr",
        template="Merhaba {name}",
    )
    response = await test_chat.create_chat_template(body)

    assert response["status"] == "created"
    assert response["template"]["id"] == "late_checkout_info_tr"
    assert response["template"]["title"] == "Geç Check-out Bilgilendirme"


@pytest.mark.asyncio
async def test_send_message_to_conversation_supports_template_id(monkeypatch: pytest.MonkeyPatch) -> None:
    conversation_id = uuid4()
    fake_repo = _FakeConversationRepository()
    fake_whatsapp = _FakeWhatsAppClient()
    fake_template = SimpleNamespace(
        id="late_checkout_info_tr",
        title="Geç Check-out Bilgilendirme",
        language="tr",
        template="Merhaba {name}, {hotel_name} icin gec cikis talebinizi aldik. Tarih: {date}",
    )
    fake_profile = HotelProfile(
        hotel_id=21966,
        hotel_name=LocalizedText(tr="Kassandra", en="Kassandra"),
    )

    async def _fake_resolve_assets_for_message(hotel_id, attachment_ids):
        _ = (hotel_id, attachment_ids)
        return []

    async def _fake_send_with_session_reopen_fallback(**kwargs):
        return await kwargs["send_operation"]()

    monkeypatch.setattr(test_chat, "ConversationRepository", lambda: fake_repo)
    monkeypatch.setattr(test_chat, "find_template_by_id", lambda template_id: fake_template if template_id == fake_template.id else None)
    monkeypatch.setattr(test_chat, "get_profile", lambda hotel_id: fake_profile if hotel_id == 21966 else None)
    monkeypatch.setattr(test_chat, "load_all_profiles", lambda: {21966: fake_profile})
    monkeypatch.setattr(test_chat.attachment_service, "resolve_assets_for_message", _fake_resolve_assets_for_message)
    monkeypatch.setattr("velox.adapters.whatsapp.client.get_whatsapp_client", lambda: fake_whatsapp)
    monkeypatch.setattr(test_chat, "_send_with_session_reopen_fallback", _fake_send_with_session_reopen_fallback)

    request = _request_with_json(
        {
            "conversation_id": str(conversation_id),
            "template_id": "late_checkout_info_tr",
        },
        _FakePool(_FakeConnection(conversation_id)),
    )
    response = await test_chat.send_message_to_conversation(request)

    assert response["status"] == "sent"
    assert response["template_id"] == "late_checkout_info_tr"
    assert response["template_title"] == "Geç Check-out Bilgilendirme"
    assert fake_repo.messages
    assert fake_repo.messages[0].internal_json["template_id"] == "late_checkout_info_tr"


def test_chat_lab_template_ui_exposes_create_dialog_and_send_action() -> None:
    assert 'id="template-create-btn"' in TEST_CHAT_HTML
    assert 'id="template-dialog"' in TEST_CHAT_HTML
    assert 'id="template-send-btn"' in TEST_CHAT_HTML
    assert "function openTemplateDialog()" in TEST_CHAT_SCRIPT
    assert "function sendSelectedTemplate()" in TEST_CHAT_SCRIPT
