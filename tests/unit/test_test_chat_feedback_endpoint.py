"""Unit tests for Chat Lab feedback, import, and report endpoints."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from velox.api.routes import test_chat
from velox.core.chat_lab_feedback import FeedbackMessageNotFoundError
from velox.models.chat_lab_feedback import (
    ChatLabCatalogResponse,
    ChatLabFeedbackRequest,
    ChatLabFeedbackResponse,
    ChatLabImportFileItem,
    ChatLabImportListResponse,
    ChatLabImportRequest,
    ChatLabImportResponse,
    ChatLabMessageView,
    ChatLabParticipantOption,
    ChatLabRecommendation,
    ChatLabReportRequest,
    ChatLabReportResponse,
    FeedbackOptionItem,
    FeedbackScaleItem,
)


class _FakeFeedbackService:
    async def get_catalog(self) -> ChatLabCatalogResponse:
        return ChatLabCatalogResponse(
            scales=[
                FeedbackScaleItem(
                    rating=1,
                    label="Yanlis",
                    summary="Hatali",
                    tooltip="Yanlis bilgi",
                    correction_required=True,
                )
            ],
            categories=[
                FeedbackOptionItem(
                    key="yanlis_bilgi",
                    label="Yanlis Bilgi",
                    description="Yanlis bilgi",
                    tooltip="Yanlis bilgi",
                )
            ],
            tags=[],
            default_report_start="2026-03-01T00:00:00+00:00",
            default_report_end="2026-03-10T00:00:00+00:00",
        )

    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        _ = payload
        return ChatLabFeedbackResponse(
            status="saved",
            feedback_id="fb_001",
            rating=3,
            rating_label="Eksik Bilgi",
            storage_group="bad_feedback",
            category="yanlis_bilgi",
            tags=["eksik_bilgi"],
            storage_path="C:\\temp\\fb_001.yaml",
            source_type="live_test_chat",
            approved_example=False,
        )

    async def list_import_files(self) -> ChatLabImportListResponse:
        return ChatLabImportListResponse(
            items=[
                ChatLabImportFileItem(
                    filename="905332227788__alpha.json",
                    modified_at="2026-03-10T10:00:00+00:00",
                    size_bytes=128,
                )
            ]
        )

    async def load_import(self, payload: ChatLabImportRequest) -> ChatLabImportResponse:
        _ = payload
        return ChatLabImportResponse(
            status="ready",
            source_type="imported_real",
            file_name="905332227788__alpha.json",
            conversation_id="conv-1",
            source_label="905332227788__alpha.json",
            messages=[
                ChatLabMessageView(
                    id="m1",
                    role="assistant",
                    content="Merhaba",
                    created_at="2026-03-10T10:00:00+00:00",
                )
            ],
            participants=[
                ChatLabParticipantOption(
                    phone="905332227788",
                    label="Musteri",
                    suggested_role="user",
                )
            ],
            metadata={"language": "tr"},
        )


class _MissingMessageFeedbackService:
    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        _ = payload
        raise FeedbackMessageNotFoundError("The selected assistant reply could not be found.")


class _CrashedFeedbackService:
    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        _ = payload
        raise RuntimeError("disk write failed")


class _FakeReportService:
    async def generate_report(self, payload: ChatLabReportRequest) -> ChatLabReportResponse:
        _ = payload
        return ChatLabReportResponse(
            status="generated",
            report_id="rpt_001",
            report_path="C:\\temp\\report.yaml",
            selected_model="gpt-5",
            summary="2 feedback 1 cluster",
            recommendation_count=1,
            date_from="2026-03-01T00:00:00+00:00",
            date_to="2026-03-10T00:00:00+00:00",
            recommendations=[
                ChatLabRecommendation(
                    target_file="data/hotel_profiles/kassandra_oludeniz.yaml",
                    reason="Hotel profile celiskisi",
                    risk="Yuksek",
                    conflict_check="Kontrol et",
                    test_suggestion="Senaryo testi ekle",
                    root_cause_type="hotel_profile",
                    confidence="high",
                    kassandra_profile_change_required=True,
                    scenario_creation_recommended=False,
                    duplicate_count=2,
                )
            ],
        )


def _request_with_db(pool: object | None = object()) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=pool)))


@pytest.mark.asyncio
async def test_feedback_catalog_endpoint_returns_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _FakeFeedbackService)

    response = await test_chat.get_feedback_catalog()

    assert response.categories[0].key == "yanlis_bilgi"
    assert response.default_report_start == "2026-03-01T00:00:00+00:00"


@pytest.mark.asyncio
async def test_feedback_endpoint_returns_saved_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _FakeFeedbackService)

    response = await test_chat.test_chat_feedback(
        body=ChatLabFeedbackRequest(
            phone="test_user_123",
            assistant_message_id="msg-1",
            rating=3,
            category="yanlis_bilgi",
            gold_standard="Dogru bilgi",
        ),
        request=_request_with_db(),
    )

    assert response.status == "saved"
    assert response.storage_group == "bad_feedback"
    assert response.storage_path.endswith("fb_001.yaml")


@pytest.mark.asyncio
async def test_import_feedback_endpoint_does_not_require_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _FakeFeedbackService)

    response = await test_chat.test_chat_feedback(
        body=ChatLabFeedbackRequest(
            source_type="imported_real",
            phone="test_user_123",
            assistant_message_id="m1",
            rating=2,
            category="yanlis_bilgi",
            gold_standard="Dogru bilgi",
            import_file="905332227788__alpha.json",
        ),
        request=_request_with_db(pool=None),
    )

    assert response.status == "saved"


@pytest.mark.asyncio
async def test_feedback_endpoint_maps_missing_message_to_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _MissingMessageFeedbackService)

    with pytest.raises(HTTPException) as exc:
        await test_chat.test_chat_feedback(
            body=ChatLabFeedbackRequest(
                phone="test_user_123",
                assistant_message_id="missing",
                rating=1,
                category="yanlis_bilgi",
                gold_standard="Dogru bilgi",
            ),
            request=_request_with_db(),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_import_list_and_load_endpoints_return_service_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _FakeFeedbackService)

    files_response = await test_chat.list_chat_import_files()
    load_response = await test_chat.load_chat_import(ChatLabImportRequest(filename="905332227788__alpha.json"))

    assert files_response.items[0].filename == "905332227788__alpha.json"
    assert load_response.status == "ready"
    assert load_response.source_type == "imported_real"


@pytest.mark.asyncio
async def test_feedback_endpoint_surfaces_unexpected_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_chat, "ChatLabFeedbackService", _CrashedFeedbackService)

    with pytest.raises(HTTPException) as exc:
        await test_chat.test_chat_feedback(
            body=ChatLabFeedbackRequest(
                phone="test_user_123",
                assistant_message_id="msg-1",
                rating=3,
                category="eksik_bilgi",
                gold_standard="Dogru bilgi",
            ),
            request=_request_with_db(),
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Beklenmeyen feedback hatasi: disk write failed"


@pytest.mark.asyncio
async def test_report_endpoint_returns_generated_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(test_chat, "ChatLabReportService", _FakeReportService)

    response = await test_chat.generate_chat_lab_report(
        ChatLabReportRequest(
            date_from=datetime(2026, 3, 1, tzinfo=UTC),
            date_to=datetime(2026, 3, 10, tzinfo=UTC),
        )
    )

    assert response.status == "generated"
    assert response.selected_model == "gpt-5"
    assert response.recommendations[0].root_cause_type == "hotel_profile"
