"""Escalation matrix loader — loads YAML and parses EscalationMatrixEntry list."""

from pathlib import Path

import structlog
import yaml

from velox.config.settings import settings
from velox.models.escalation import EscalationMatrixEntry

logger = structlog.get_logger(__name__)

_matrix: list[EscalationMatrixEntry] = []
_matrix_by_flag: dict[str, EscalationMatrixEntry] = {}


def load_escalation_matrix() -> list[EscalationMatrixEntry]:
    """Load the escalation matrix from YAML file into in-memory caches."""
    global _matrix, _matrix_by_flag
    _matrix.clear()
    _matrix_by_flag.clear()

    matrix_path = Path(settings.escalation_matrix_path)
    if not matrix_path.exists():
        logger.warning("escalation_matrix_not_found", path=str(matrix_path))
        return _matrix

    try:
        with matrix_path.open(encoding="utf-8") as file_obj:
            raw_list = yaml.safe_load(file_obj)

        if not isinstance(raw_list, list):
            logger.error("escalation_matrix_not_list", path=str(matrix_path))
            return _matrix

        for entry_dict in raw_list:
            try:
                entry = EscalationMatrixEntry(**entry_dict)
                _matrix.append(entry)
                _matrix_by_flag[entry.risk_flag] = entry
            except Exception:
                logger.exception("escalation_matrix_entry_parse_failed", entry=entry_dict)

        logger.info("escalation_matrix_loaded", count=len(_matrix), path=str(matrix_path))
    except Exception:
        logger.exception("escalation_matrix_load_failed", path=str(matrix_path))

    return _matrix


def get_entry_by_flag(risk_flag: str) -> EscalationMatrixEntry | None:
    """Look up escalation entry by risk flag name."""
    return _matrix_by_flag.get(risk_flag)


def get_all_entries() -> list[EscalationMatrixEntry]:
    """Get all cached escalation matrix entries."""
    return _matrix.copy()


def get_highest_entry(risk_flags: list[str]) -> EscalationMatrixEntry | None:
    """Return highest-ranked entry by level then priority for matched risk flags."""
    level_order = {"L3": 4, "L2": 3, "L1": 2, "L0": 1}
    priority_order = {"high": 3, "medium": 2, "low": 1}

    matched: list[EscalationMatrixEntry] = []
    for flag in risk_flags:
        entry = _matrix_by_flag.get(flag)
        if entry is not None:
            matched.append(entry)

    if not matched:
        return None

    return max(
        matched,
        key=lambda entry: (
            level_order.get(entry.level.value, 0),
            priority_order.get(entry.priority.value, 0),
        ),
    )


def reload_matrix() -> list[EscalationMatrixEntry]:
    """Reload the escalation matrix from disk."""
    logger.info("escalation_matrix_reloading")
    return load_escalation_matrix()
