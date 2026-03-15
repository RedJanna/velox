"""Aggregate Chat Lab bad-feedback reports."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
import yaml

from velox.config.settings import settings
from velox.llm.client import get_llm_client
from velox.models.chat_lab_feedback import (
    ChatLabRecommendation,
    ChatLabReportRequest,
    ChatLabReportResponse,
)
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)

_REPORT_SCHEMA_VERSION = "chat_lab_report.v1"
_REPORT_WRITE_LOCK = asyncio.Lock()


class ChatLabReportError(RuntimeError):
    """Raised when Chat Lab aggregate report generation fails."""


class ChatLabReportService:
    """Generate aggregate reports from saved bad-feedback files."""

    def __init__(
        self,
        feedback_root: Path | None = None,
        llm_client: Any | None = None,
    ) -> None:
        project_root = get_project_root(__file__)
        self._feedback_root = feedback_root or (project_root / settings.chat_lab_feedback_dir)
        self._reports_root = self._feedback_root / "reports"
        self._llm_client = llm_client

    async def generate_report(self, payload: ChatLabReportRequest) -> ChatLabReportResponse:
        """Generate one aggregate report for the selected feedback date range."""
        date_from = _ensure_aware(payload.date_from)
        date_to = _ensure_aware(payload.date_to)

        self._reports_root.mkdir(parents=True, exist_ok=True)
        feedback_root = self._feedback_root / "bad_feedback"
        records = _load_feedback_records(feedback_root, date_from, date_to)
        if not records:
            return ChatLabReportResponse(
                status="no_feedback",
                summary="Secilen tarih araliginda kotu feedback kaydi bulunamadi.",
                recommendation_count=0,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
                recommendations=[],
            )

        clusters = _cluster_feedback(records)
        selected_model = await self._select_best_model()
        llm_payload = await self._build_llm_report(records, clusters, selected_model)

        if llm_payload is None:
            summary = _fallback_summary(records, clusters)
            recommendations = _fallback_recommendations(clusters)
        else:
            summary = str(llm_payload.get("summary") or _fallback_summary(records, clusters)).strip()
            recommendations = _coerce_recommendations(llm_payload.get("recommendations"), clusters)
            if not recommendations:
                recommendations = _fallback_recommendations(clusters)

        report_id = datetime.now(UTC).strftime("rpt_%Y%m%d_%H%M%S_%f")
        report_path = self._reports_root / f"report_{report_id}.yaml"
        report_payload = {
            "schema_version": _REPORT_SCHEMA_VERSION,
            "report_id": report_id,
            "created_at": datetime.now(UTC).isoformat(),
            "selected_model": selected_model,
            "period": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
            "summary": summary,
            "feedback_count": len(records),
            "cluster_count": len(clusters),
            "clusters": [
                {
                    "cluster_id": cluster["cluster_id"],
                    "category": cluster["category"],
                    "duplicate_count": cluster["duplicate_count"],
                    "tags": cluster["tags"],
                    "sample_input": cluster["sample_input"],
                    "sample_output": cluster["sample_output"],
                    "gold_standard": cluster["gold_standard"],
                    "root_cause_hint": cluster["root_cause_type"],
                    "files": [_display_path(path) for path in cluster["files"]],
                }
                for cluster in clusters
            ],
            "recommendations": [item.model_dump(mode="json") for item in recommendations],
        }

        async with _REPORT_WRITE_LOCK:
            _write_yaml_file(report_path, report_payload)

        logger.info(
            "chat_lab_report_generated",
            report_id=report_id,
            feedback_count=len(records),
            cluster_count=len(clusters),
            path=str(report_path),
        )
        return ChatLabReportResponse(
            status="generated",
            report_id=report_id,
            report_path=_display_path(report_path),
            selected_model=selected_model,
            summary=summary,
            recommendation_count=len(recommendations),
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
            recommendations=recommendations,
        )

    async def _select_best_model(self) -> str:
        client = self._llm_client or get_llm_client()
        try:
            models_page = await client.client.models.list()
        except Exception:
            logger.exception("chat_lab_report_model_list_failed")
            return str(getattr(client, "primary_model", "gpt-4o"))

        candidates = [
            str(model.id)
            for model in getattr(models_page, "data", [])
            if isinstance(getattr(model, "id", None), str)
            and (
                str(model.id).startswith("gpt")
                or str(model.id).startswith("o1")
                or str(model.id).startswith("o3")
            )
        ]
        if not candidates:
            return str(getattr(client, "primary_model", "gpt-4o"))
        return max(candidates, key=_model_rank)

    async def _build_llm_report(
        self,
        records: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
        selected_model: str,
    ) -> dict[str, Any] | None:
        client = self._llm_client or get_llm_client()
        if not getattr(client, "client", None):
            return None

        prompt_payload = {
            "feedback_count": len(records),
            "cluster_count": len(clusters),
            "clusters": [
                {
                    "category": cluster["category"],
                    "duplicate_count": cluster["duplicate_count"],
                    "tags": cluster["tags"],
                    "sample_input": cluster["sample_input"],
                    "sample_output": cluster["sample_output"],
                    "gold_standard": cluster["gold_standard"],
                    "root_cause_hint": cluster["root_cause_type"],
                }
                for cluster in clusters[:8]
            ],
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "Sen bir kalite raporu uretiyorsun. Sadece verilen feedback kayitlarini kullan. "
                    "JSON disinda hicbir sey donme. Cikti sozu su sekilde olsun: "
                    '{"summary":"...","recommendations":[{"target_file":"...","reason":"...",'
                    '"risk":"...","conflict_check":"...","test_suggestion":"...",'
                    '"root_cause_type":"prompt|template|hotel_profile|tool_output|state_machine|policy|formatting|unknown",'
                    '"confidence":"high|medium|low","kassandra_profile_change_required":false,'
                    '"scenario_creation_recommended":false,"duplicate_count":1}]}.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(prompt_payload, ensure_ascii=False),
            },
        ]
        try:
            response = await client.chat_completion(messages=messages, model=selected_model)
        except Exception:
            logger.exception("chat_lab_report_generation_failed", model=selected_model)
            return None

        content = str(response.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        if not content:
            return None
        try:
            return _parse_json_payload(content)
        except ValueError:
            logger.warning("chat_lab_report_invalid_json", model=selected_model)
            return None


def _load_feedback_records(root: Path, date_from: datetime, date_to: datetime) -> list[dict[str, Any]]:
    if not root.exists():
        return []

    records: list[dict[str, Any]] = []
    for file_path in sorted(root.rglob("*.yaml")):
        try:
            with file_path.open(encoding="utf-8") as file_obj:
                data = yaml.safe_load(file_obj) or {}
        except Exception:
            logger.warning("chat_lab_report_read_failed", path=str(file_path))
            continue

        if not isinstance(data, dict):
            continue
        created_at = _parse_datetime(data.get("created_at") or data.get("timestamp"))
        if created_at is None or created_at < date_from or created_at > date_to:
            continue

        data["__file_path"] = file_path
        data["__created_at"] = created_at
        records.append(data)
    return records


def _cluster_feedback(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: dict[str, dict[str, Any]] = {}
    for record in records:
        category = str(record.get("category") or "uncategorized")
        normalized_input = _normalize_cluster_text(record.get("input"))
        normalized_output = _normalize_cluster_text(record.get("output"))
        normalized_gold = _normalize_cluster_text(record.get("gold_standard"))
        cluster_key = hashlib.sha256(
            f"{category}|{normalized_input}|{normalized_output}|{normalized_gold}".encode()
        ).hexdigest()[:12]
        cluster = clusters.get(cluster_key)
        if cluster is None:
            cluster = {
                "cluster_id": cluster_key,
                "category": category,
                "duplicate_count": 0,
                "tags": [],
                "ratings": [],
                "sample_input": str(record.get("input") or ""),
                "sample_output": str(record.get("output") or ""),
                "gold_standard": str(record.get("gold_standard") or ""),
                "root_cause_type": _infer_root_cause(record),
                "files": [],
                "latest_created_at": record["__created_at"],
            }
            clusters[cluster_key] = cluster

        cluster["duplicate_count"] += 1
        cluster["ratings"].append(int(record.get("rating") or 0))
        cluster["files"].append(record["__file_path"])
        cluster["latest_created_at"] = max(cluster["latest_created_at"], record["__created_at"])
        for tag in record.get("tags") or []:
            if isinstance(tag, str) and tag not in cluster["tags"]:
                cluster["tags"].append(tag)

    return sorted(
        clusters.values(),
        key=lambda item: (-int(item["duplicate_count"]), item["latest_created_at"]),
        reverse=False,
    )


def _fallback_summary(records: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> str:
    category_counts = Counter(str(record.get("category") or "uncategorized") for record in records)
    top_categories = ", ".join(f"{name}:{count}" for name, count in category_counts.most_common(3))
    return (
        f"{len(records)} kotu feedback kaydi {len(clusters)} tekrar kumesine ayrildi. "
        f"En sik kategoriler: {top_categories or 'kategori yok'}."
    )


def _fallback_recommendations(clusters: list[dict[str, Any]]) -> list[ChatLabRecommendation]:
    recommendations: list[ChatLabRecommendation] = []
    for cluster in clusters[:5]:
        root_cause_type = str(cluster["root_cause_type"])
        duplicate_count = int(cluster["duplicate_count"])
        recommendations.append(
            ChatLabRecommendation(
                target_file=_suggest_target_file(root_cause_type),
                reason=(
                    f"{cluster['category']} kategorisinde {duplicate_count} tekrar var. "
                    f"Ornek cikti: {str(cluster['sample_output'])[:180]}"
                ),
                risk=_risk_summary(cluster["category"], duplicate_count),
                conflict_check=_conflict_check(root_cause_type, duplicate_count),
                test_suggestion=_test_suggestion(cluster["category"]),
                root_cause_type=root_cause_type,
                confidence=_confidence_for_cluster(cluster),
                kassandra_profile_change_required=root_cause_type == "hotel_profile",
                scenario_creation_recommended=duplicate_count >= 2,
                duplicate_count=duplicate_count,
            )
        )
    return recommendations


def _coerce_recommendations(
    raw_items: Any,
    clusters: list[dict[str, Any]],
) -> list[ChatLabRecommendation]:
    if not isinstance(raw_items, list):
        return []

    recommendations: list[ChatLabRecommendation] = []
    for index, item in enumerate(raw_items[:6]):
        cluster = clusters[min(index, len(clusters) - 1)] if clusters else None
        if not isinstance(item, dict):
            continue

        root_cause_type = str(item.get("root_cause_type") or (cluster["root_cause_type"] if cluster else "unknown"))
        duplicate_count = int(item.get("duplicate_count") or (cluster["duplicate_count"] if cluster else 1))
        confidence = str(item.get("confidence") or _confidence_for_cluster(cluster or {"duplicate_count": 1}))
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"

        recommendations.append(
            ChatLabRecommendation(
                target_file=str(item.get("target_file") or _suggest_target_file(root_cause_type)),
                reason=str(item.get("reason") or ""),
                risk=str(item.get("risk") or _risk_summary(cluster["category"], duplicate_count) if cluster else ""),
                conflict_check=str(
                    item.get("conflict_check")
                    or _conflict_check(root_cause_type, duplicate_count)
                ),
                test_suggestion=str(
                    item.get("test_suggestion")
                    or _test_suggestion(cluster["category"] if cluster else "")
                ),
                root_cause_type=root_cause_type,
                confidence=confidence,
                kassandra_profile_change_required=bool(
                    item.get("kassandra_profile_change_required") or root_cause_type == "hotel_profile"
                ),
                scenario_creation_recommended=bool(
                    item.get("scenario_creation_recommended") or duplicate_count >= 2
                ),
                duplicate_count=max(1, duplicate_count),
            )
        )
    return recommendations


def _parse_json_payload(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Report content must be a JSON object.")
    return parsed


def _parse_datetime(raw_value: Any) -> datetime | None:
    if not isinstance(raw_value, str) or not raw_value:
        return None
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return None
    return _ensure_aware(parsed)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_cluster_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text[:160]


def _infer_root_cause(record: dict[str, Any]) -> str:
    category = str(record.get("category") or "")
    tags = {str(tag) for tag in record.get("tags") or []}
    if "hotel_profile_celiskisi" in tags:
        return "hotel_profile"
    if "tool_output_celiskisi" in tags or "guncel_olmayan_bilgi" in tags:
        return "tool_output"
    if category in {"format_ihlali", "gevezelik"} or "format_ihlali" in tags:
        return "formatting"
    if category in {"ton_politika_ihlali"} or "politika_ihlali" in tags:
        return "policy"
    if category in {"baglam_kopuklugu", "mantik_celiskisi"}:
        return "state_machine"
    if category in {"intent_iskalama", "tekrar_loop"}:
        return "template"
    if category in {"uydurma_bilgi", "yanlis_bilgi", "alakasiz_yanit"}:
        return "prompt"
    return "unknown"


def _suggest_target_file(root_cause_type: str) -> str:
    if root_cause_type == "hotel_profile":
        return "data/hotel_profiles/kassandra_oludeniz.yaml"
    if root_cause_type == "tool_output":
        return "src/velox/tools/"
    if root_cause_type == "state_machine":
        return "src/velox/core/"
    if root_cause_type == "policy":
        return "docs/master_prompt_v2.md"
    if root_cause_type == "formatting":
        return "data/templates/"
    if root_cause_type == "template":
        return "data/templates/"
    if root_cause_type == "prompt":
        return "docs/master_prompt_v2.md"
    return "src/velox/core/"


def _risk_summary(category: str, duplicate_count: int) -> str:
    if duplicate_count >= 3:
        return f"{category} hatasi tekrarli oldugu icin regresyon riski yuksek."
    if duplicate_count == 2:
        return f"{category} hatasi yeniden uretilmis; orta seviye regresyon riski var."
    return f"{category} icin tekil hata kaydi var; degisiklik oncesi conflict kontrolu gerekli."


def _conflict_check(root_cause_type: str, duplicate_count: int) -> str:
    if duplicate_count >= 3:
        return (
            f"{root_cause_type} katmaninda ayni davranisi yoneten mevcut kural, template veya hotel profile "
            "satirlariyla duplicate/celiski taramasi yapilmali."
        )
    return f"{root_cause_type} katmaninda benzer kural veya mevcut patch varsa once o kayitlarla karsilastir."


def _test_suggestion(category: str) -> str:
    return (
        f"{category} icin ayni niyetle yeni unit testi ve en az bir Chat Lab regresyon transkripti eklenmeli."
    )


def _confidence_for_cluster(cluster: dict[str, Any]) -> str:
    duplicate_count = int(cluster.get("duplicate_count") or 1)
    if duplicate_count >= 3:
        return "high"
    if duplicate_count == 2:
        return "medium"
    return "low"


def _model_rank(model_name: str) -> tuple[int, int, int, str]:
    lowered = model_name.lower()
    base_score = 0
    if lowered.startswith("gpt-5"):
        base_score = 500
    elif lowered.startswith("gpt-4.1"):
        base_score = 410
    elif lowered.startswith("gpt-4o"):
        base_score = 400
    elif lowered.startswith("o3"):
        base_score = 350
    elif lowered.startswith("o1"):
        base_score = 300
    elif lowered.startswith("gpt"):
        base_score = 200

    penalty = 0
    if "mini" in lowered:
        penalty -= 40
    if "nano" in lowered:
        penalty -= 60
    if "preview" in lowered:
        penalty -= 10

    version_digits = [int(part) for part in re.findall(r"\d+", lowered)]
    version_score = sum(version_digits[:3])
    return (base_score + penalty, version_score, len(model_name), model_name)


def _display_path(path: Path) -> str:
    raw_path = str(path)
    if raw_path.startswith("/mnt/") and len(raw_path) > 6:
        drive = raw_path[5].upper()
        remainder = raw_path[6:].replace("/", "\\")
        return f"{drive}:{remainder}"
    return raw_path


def _write_yaml_file(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file_obj:
        yaml.safe_dump(payload, file_obj, allow_unicode=True, sort_keys=False, width=1000)
