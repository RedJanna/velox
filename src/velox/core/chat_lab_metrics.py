"""Chat Lab feedback metrics aggregation service."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import structlog
import yaml

from velox.config.settings import settings
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)


def compute_feedback_metrics() -> dict[str, Any]:
    """Scan all feedback YAML files and return aggregated metrics.

    Returns a dictionary with:
    - total_feedback: total number of feedback records
    - rating_distribution: {1: count, 2: count, ...}
    - category_distribution: {category_key: count, ...}
    - tag_distribution: {tag: count, ...}
    - language_distribution: {language: count, ...}
    - approval_rate: ratio of rating-5 records to total
    - rejection_rate: ratio of rating 1-2 records to total
    - avg_rating: mean rating across all records
    - good_vs_bad: {good_feedback: count, bad_feedback: count}
    """
    feedback_root = get_project_root(__file__) / settings.chat_lab_feedback_dir
    if not feedback_root.exists():
        return _empty_metrics()

    records = _load_all_feedback_records(feedback_root)
    if not records:
        return _empty_metrics()

    total = len(records)
    rating_counter: Counter[int] = Counter()
    category_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    language_counter: Counter[str] = Counter()
    good_count = 0
    bad_count = 0
    rating_sum = 0

    for record in records:
        rating = record.get("rating")
        if not isinstance(rating, int):
            continue

        rating_counter[rating] += 1
        rating_sum += rating

        category = record.get("category", "")
        if category:
            category_counter[str(category)] += 1

        tags = record.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                tag_counter[str(tag)] += 1

        language = record.get("language", "")
        if language:
            language_counter[str(language)] += 1

        storage_group = record.get("storage_group", "")
        if storage_group == "good_feedback":
            good_count += 1
        else:
            bad_count += 1

    return {
        "total_feedbacks": total,
        "rating_distribution": dict(sorted(rating_counter.items())),
        "category_distribution": dict(category_counter.most_common(20)),
        "tag_distribution": dict(tag_counter.most_common(30)),
        "language_distribution": dict(language_counter.most_common(15)),
        "approval_rate": round(rating_counter.get(5, 0) / total, 4) if total else 0,
        "rejection_rate": round((rating_counter.get(1, 0) + rating_counter.get(2, 0)) / total, 4) if total else 0,
        "avg_rating": round(rating_sum / total, 2) if total else 0,
        "good_count": good_count,
        "bad_count": bad_count,
    }


def _load_all_feedback_records(feedback_root: Path) -> list[dict[str, Any]]:
    """Recursively load all .yaml feedback files."""
    records: list[dict[str, Any]] = []
    for yaml_path in feedback_root.rglob("*.yaml"):
        if yaml_path.name.startswith("report_"):
            continue
        try:
            with yaml_path.open(encoding="utf-8") as file_obj:
                data = yaml.safe_load(file_obj)
            if isinstance(data, dict) and "rating" in data:
                records.append(data)
        except Exception:
            logger.debug("chat_lab_metrics_skip_file", path=str(yaml_path))
    return records


def _empty_metrics() -> dict[str, Any]:
    return {
        "total_feedbacks": 0,
        "rating_distribution": {},
        "category_distribution": {},
        "tag_distribution": {},
        "language_distribution": {},
        "approval_rate": 0,
        "rejection_rate": 0,
        "avg_rating": 0,
        "good_count": 0,
        "bad_count": 0,
    }
