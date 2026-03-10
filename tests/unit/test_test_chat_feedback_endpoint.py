"""Unit tests for Chat Lab feedback endpoint."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from velox.api.routes import test_chat
from velox.core.chat_lab_feedback import FeedbackMessageNotFoundError
from velox.models.chat_lab_feedback import ChatLabFeedbackRequest, ChatLabFeedbackResponse


class _FakeFeedbackService:
    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        _ = payload
        return ChatLabFeedbackResponse(
            status="scenario_created",
            rating=3,
            rating_label="Eksik Bilgi",
            corrected_reply="Duzeltilmis cevap",
            selected_model="gpt-5",
            scenario_code="S048",
            scenario_path="C:\\Users\\gonen\\Desktop\\velox\\DIKKAT\\velox\\data\\scenarios\\S048_test.yaml",
        )


class _MissingMessageFeedbackService:
    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        _ = payload
        raise FeedbackMessageNotFoundError("The selected assistant reply could not be found.")


def _request_with_db() -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=object())))


@pytest.mark.asyncio
async def test_feedback_endpoint_returns_service_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _FakeFeedbackService)

    response = await test_chat.test_chat_feedback(
        body=ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id=uuid4(),
            rating=3,
            correction="Dogru bilgi",
        ),
        request=_request_with_db(),
    )

    assert response.status == "scenario_created"
    assert response.selected_model == "gpt-5"
    assert response.scenario_code == "S048"


@pytest.mark.asyncio
async def test_feedback_endpoint_maps_missing_message_to_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _MissingMessageFeedbackService)

    with pytest.raises(HTTPException) as exc:
        await test_chat.test_chat_feedback(
            body=ChatLabFeedbackRequest(
                phone="test_user_123",
                assistant_message_id=uuid4(),
                rating=1,
                correction="Dogru bilgi",
            ),
            request=_request_with_db(),
        )

    assert exc.value.status_code == 404
