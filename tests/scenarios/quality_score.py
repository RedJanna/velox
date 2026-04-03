"""Weighted quality scoring for scenario evaluation runs."""

from __future__ import annotations

from tests.scenarios.runner import ScenarioResult

_SEVERITY_WEIGHTS = {
    "CRITICAL": 3.0,
    "HIGH": 2.0,
    "MEDIUM": 1.0,
}


def scenario_severity(code: str) -> str:
    """Map scenario code ranges to severity buckets."""
    num = int(code.replace("S", "").replace("s", ""))
    if num >= 41:
        return "CRITICAL"
    if num >= 31:
        return "MEDIUM"
    return "HIGH"


def compute_quality_score(results: list[ScenarioResult]) -> dict[str, float | int]:
    """Compute weighted quality score from step-level pass/fail results."""
    if not results:
        return {
            "score": 0.0,
            "weighted_passed_steps": 0,
            "weighted_total_steps": 0,
            "critical_pass_rate": 0.0,
        }

    weighted_total = 0.0
    weighted_passed = 0.0
    critical_total = 0
    critical_passed = 0

    for result in results:
        severity = scenario_severity(result.code)
        weight = _SEVERITY_WEIGHTS.get(severity, 1.0)
        weighted_total += result.total_steps * weight
        weighted_passed += result.passed_steps * weight
        if severity == "CRITICAL":
            critical_total += result.total_steps
            critical_passed += result.passed_steps

    score = round((weighted_passed / weighted_total) * 100, 2) if weighted_total > 0 else 0.0
    critical_pass_rate = round((critical_passed / critical_total) * 100, 2) if critical_total > 0 else 0.0
    return {
        "score": score,
        "weighted_passed_steps": int(round(weighted_passed)),
        "weighted_total_steps": int(round(weighted_total)),
        "critical_pass_rate": critical_pass_rate,
    }
