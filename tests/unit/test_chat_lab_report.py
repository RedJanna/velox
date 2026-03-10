"""Unit tests for Chat Lab aggregate report generation."""

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from velox.core.chat_lab_report import ChatLabReportService
from velox.models.chat_lab_feedback import ChatLabReportRequest


class _FakeModelsAPI:
    async def list(self) -> SimpleNamespace:
        return SimpleNamespace(
            data=[
                SimpleNamespace(id="gpt-4o"),
                SimpleNamespace(id="gpt-5"),
                SimpleNamespace(id="gpt-4o-mini"),
            ]
        )


class _FakeLLMClient:
    def __init__(self) -> None:
        self.client = SimpleNamespace(models=_FakeModelsAPI())
        self.primary_model = "gpt-4o"

    async def chat_completion(self, messages, tools=None, model=None) -> dict:
        _ = (messages, tools, model)
        return {
            "choices": [
                {
                    "message": {
                        "content": """
{
  "summary": "2 feedback kaydi tek cluster altinda toplandi.",
  "recommendations": [
    {
      "target_file": "data/hotel_profiles/kassandra_oludeniz.yaml",
      "reason": "Hotel profile ile cevap arasinda tekrar eden celiski var.",
      "risk": "Ayni hata tekrarli oldugu icin yuksek risk.",
      "conflict_check": "Mevcut hotel profile satirlari ve prompt uzerinden duplicate kontrolu yapin.",
      "test_suggestion": "Ayni intent icin regresyon testi ekleyin.",
      "root_cause_type": "hotel_profile",
      "confidence": "high",
      "kassandra_profile_change_required": true,
      "scenario_creation_recommended": false,
      "duplicate_count": 2
    }
  ]
}
""".strip()
                    }
                }
            ]
        }


def _write_feedback_file(base_dir: Path, name: str, created_at: str) -> None:
    target = base_dir / "bad_feedback" / "rating_2" / "yanlis_bilgi" / "2026-03"
    target.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "chat_lab_feedback.v1",
        "feedback_id": name,
        "created_at": created_at,
        "rating": 2,
        "category": "yanlis_bilgi",
        "tags": ["hotel_profile_celiskisi"],
        "input": "Restoran menusu guncel mi?",
        "output": "Evet, tum fiyatlar kesindir.",
        "gold_standard": "Once hangi menunun soruldugu netlestirilmeli.",
    }
    (target / f"{name}.yaml").write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


@pytest.mark.asyncio
async def test_report_service_generates_yaml_report_with_best_model(tmp_path: Path) -> None:
    feedback_root = tmp_path / "chat_lab_feedback"
    _write_feedback_file(feedback_root, "fb_001", "2026-03-10T10:00:00+00:00")
    _write_feedback_file(feedback_root, "fb_002", "2026-03-10T10:05:00+00:00")
    service = ChatLabReportService(feedback_root=feedback_root, llm_client=_FakeLLMClient())

    response = await service.generate_report(
        ChatLabReportRequest(
            date_from=datetime(2026, 3, 10, 0, 0, tzinfo=UTC),
            date_to=datetime(2026, 3, 10, 23, 59, tzinfo=UTC),
        )
    )

    assert response.status == "generated"
    assert response.selected_model == "gpt-5"
    assert response.recommendation_count == 1
    assert response.recommendations[0].root_cause_type == "hotel_profile"

    report_files = sorted((feedback_root / "reports").glob("report_*.yaml"))
    assert len(report_files) == 1
    payload = yaml.safe_load(report_files[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "chat_lab_report.v1"
    assert payload["selected_model"] == "gpt-5"
    assert payload["recommendations"][0]["duplicate_count"] == 2


@pytest.mark.asyncio
async def test_report_service_returns_no_feedback_when_range_is_empty(tmp_path: Path) -> None:
    service = ChatLabReportService(feedback_root=tmp_path / "chat_lab_feedback", llm_client=_FakeLLMClient())

    response = await service.generate_report(
        ChatLabReportRequest(
            date_from=datetime(2026, 3, 1, 0, 0, tzinfo=UTC),
            date_to=datetime(2026, 3, 2, 0, 0, tzinfo=UTC),
        )
    )

    assert response.status == "no_feedback"
    assert response.recommendation_count == 0
