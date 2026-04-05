"""Lightweight in-process metrics registry with Prometheus text rendering."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Final

_PROMETHEUS_CONTENT_TYPE: Final[str] = "text/plain; version=0.0.4; charset=utf-8"

_lock = Lock()
_counter_help: dict[str, str] = {}
_counter_values: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)


def prometheus_content_type() -> str:
    """Return the Prometheus exposition content type."""
    return _PROMETHEUS_CONTENT_TYPE


def increment_counter(
    name: str,
    description: str,
    *,
    labels: dict[str, str] | None = None,
    amount: float = 1.0,
) -> None:
    """Increment a named counter with optional labels."""
    normalized_labels = tuple(sorted((labels or {}).items()))
    with _lock:
        _counter_help.setdefault(name, description)
        _counter_values[(name, normalized_labels)] += amount


def render_metrics() -> str:
    """Render all metrics in Prometheus text exposition format."""
    lines: list[str] = []
    with _lock:
        metric_names = sorted(_counter_help)
        values_snapshot = dict(_counter_values)
    for metric_name in metric_names:
        lines.append(f"# HELP {metric_name} {_counter_help[metric_name]}")
        lines.append(f"# TYPE {metric_name} counter")
        matching_series = sorted(
            (
                label_items,
                values_snapshot[(name, label_items)],
            )
            for name, label_items in values_snapshot
            if name == metric_name
        )
        if not matching_series:
            lines.append(f"{metric_name} 0.0")
            continue
        for label_items, value in matching_series:
            label_text = _format_labels(label_items)
            lines.append(f"{metric_name}{label_text} {value}")
    return "\n".join(lines) + "\n"


def reset_metrics() -> None:
    """Reset all in-process metric state for tests."""
    with _lock:
        _counter_help.clear()
        _counter_values.clear()


def record_prompt_truncation(component: str) -> None:
    """Record a prompt truncation event."""
    increment_counter(
        "velox_llm_prompt_truncations_total",
        "Count of prompt truncation events in the LLM runtime.",
        labels={"component": component},
    )


def record_structured_output_parser_error(reason: str) -> None:
    """Record a structured-output parser failure."""
    increment_counter(
        "velox_llm_structured_output_parser_errors_total",
        "Count of structured-output parser failures by reason.",
        labels={"reason": reason or "unknown"},
    )


def record_structured_output_repair_outcome(outcome: str) -> None:
    """Record a structured-output repair attempt outcome."""
    increment_counter(
        "velox_llm_structured_output_repair_total",
        "Count of structured-output repair attempts by outcome.",
        labels={"outcome": outcome or "unknown"},
    )


def record_structured_output_fallback(reason: str) -> None:
    """Record use of the generic structured-output fallback path."""
    increment_counter(
        "velox_llm_structured_output_fallback_total",
        "Count of structured-output fallback responses by parser reason.",
        labels={"reason": reason or "unknown"},
    )


def record_intent_domain_guard(reason: str, from_intent: str, to_intent: str) -> None:
    """Record application of a deterministic cross-domain intent guard."""
    increment_counter(
        "velox_llm_intent_domain_guard_total",
        "Count of deterministic intent-domain guard applications by reason and remapped intents.",
        labels={
            "reason": reason or "unknown",
            "from_intent": from_intent or "unknown",
            "to_intent": to_intent or "unknown",
        },
    )


def _format_labels(label_items: tuple[tuple[str, str], ...]) -> str:
    """Format label key/value pairs for Prometheus output."""
    if not label_items:
        return ""
    pairs = [f'{key}="{_escape_label_value(value)}"' for key, value in label_items]
    return "{" + ",".join(pairs) + "}"


def _escape_label_value(value: str) -> str:
    """Escape label values according to Prometheus text rules."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
