"""Tests for scenario quality scoring engine."""

from tests.scenarios.quality_score import compute_quality_score
from tests.scenarios.runner import ScenarioResult, ScenarioStepResult


def _result(code: str, passed_steps: int, failed_steps: int) -> ScenarioResult:
    steps = []
    for idx in range(passed_steps):
        steps.append(ScenarioStepResult(index=idx + 1, passed=True))
    for idx in range(failed_steps):
        steps.append(ScenarioStepResult(index=passed_steps + idx + 1, passed=False, errors=["fail"]))
    return ScenarioResult(
        code=code,
        name=code,
        category="test",
        passed=failed_steps == 0,
        steps=steps,
    )


def test_compute_quality_score_weights_critical_scenarios_higher() -> None:
    results = [
        _result("S010", passed_steps=2, failed_steps=0),  # HIGH
        _result("S045", passed_steps=0, failed_steps=2),  # CRITICAL
    ]
    quality = compute_quality_score(results)
    assert quality["weighted_total_steps"] == 10
    assert quality["weighted_passed_steps"] == 4
    assert quality["score"] == 40.0
    assert quality["critical_pass_rate"] == 0.0
