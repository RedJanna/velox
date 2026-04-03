"""Eval report generator — console + JSON output."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tests.scenarios.quality_score import compute_quality_score, scenario_severity
from tests.scenarios.runner import ScenarioResult

REPORTS_DIR = Path(__file__).resolve().parents[2] / "data" / "eval_reports"


def _severity_for_scenario(code: str) -> str:
    """Determine severity based on scenario code range."""
    return scenario_severity(code)


def generate_console_report(results: list[ScenarioResult], mode: str = "full") -> str:
    """Generate human-readable console report."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    quality = compute_quality_score(results)

    lines: list[str] = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("         VELOX EVAL RAPORU")
    lines.append(f"         {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"         Mod: {mode}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Toplam senaryo:  {total}")
    lines.append(f"  Gecen:           {passed}  ({_pct(passed, total)})")
    lines.append(f"  Kalan:           {failed}  ({_pct(failed, total)})")
    lines.append(f"  Kalite skoru:    {quality['score']} / 100")
    lines.append(f"  Kritik pass:     %{quality['critical_pass_rate']}")
    lines.append("")

    # Category breakdown
    categories: dict[str, list[ScenarioResult]] = {}
    for r in results:
        cat = r.category or "other"
        categories.setdefault(cat, []).append(r)

    lines.append("  --- KATEGORI BAZLI ---")
    for cat, cat_results in sorted(categories.items()):
        cat_pass = sum(1 for r in cat_results if r.passed)
        cat_total = len(cat_results)
        bar = _progress_bar(cat_pass, cat_total)
        lines.append(f"  {cat:<15} {cat_pass}/{cat_total}  {bar}")
    lines.append("")

    # Failed scenarios detail
    failed_results = [r for r in results if not r.passed]
    if failed_results:
        lines.append("  --- BASARISIZ SENARYOLAR ---")
        lines.append("")
        for r in failed_results:
            severity = _severity_for_scenario(r.code)
            lines.append(f"  {r.code} [{severity}] {r.name}")
            for step in r.steps:
                if not step.passed:
                    lines.append(f"    Adim {step.index}: \"{step.user_message[:60]}\"")
                    for err in step.errors:
                        lines.append(f"      - {err}")
            lines.append("")
    else:
        lines.append("  TUM SENARYOLAR GECTI!")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def generate_json_report(
    results: list[ScenarioResult],
    mode: str = "full",
    app_version: str = "dev",
) -> dict[str, Any]:
    """Generate machine-readable JSON report."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    quality = compute_quality_score(results)

    failures: list[dict[str, Any]] = []
    for r in results:
        if r.passed:
            continue
        failed_steps: list[dict[str, Any]] = []
        for step in r.steps:
            if not step.passed:
                failed_steps.append({
                    "step_index": step.index,
                    "user_message": step.user_message,
                    "errors": step.errors,
                    "actual_response": {
                        "intent": step.response.get("intent"),
                        "state": step.response.get("state"),
                        "tool_calls": step.response.get("tool_calls", []),
                        "risk_flags": step.response.get("risk_flags", []),
                        "reply_preview": str(step.response.get("reply", ""))[:200],
                    },
                })
        failures.append({
            "scenario_code": r.code,
            "scenario_name": r.name,
            "category": r.category,
            "severity": _severity_for_scenario(r.code),
            "total_steps": r.total_steps,
            "passed_steps": r.passed_steps,
            "failed_steps": failed_steps,
        })

    return {
        "run_id": f"EVAL-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": mode,
        "app_version": app_version,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{_pct(passed, total)}",
            "quality_score": quality["score"],
            "critical_pass_rate": quality["critical_pass_rate"],
            "weighted_passed_steps": quality["weighted_passed_steps"],
            "weighted_total_steps": quality["weighted_total_steps"],
        },
        "failures": failures,
    }


def save_json_report(report: dict[str, Any], directory: Path = REPORTS_DIR) -> Path:
    """Save JSON report to file. Returns file path."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{report['run_id']}.json"
    filepath = directory / filename
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return filepath


def _pct(part: int, total: int) -> str:
    """Calculate percentage string."""
    if total == 0:
        return "0%"
    return f"{part * 100 // total}%"


def _progress_bar(passed: int, total: int, width: int = 10) -> str:
    """Generate a simple text progress bar."""
    if total == 0:
        return ""
    filled = passed * width // total
    return "█" * filled + "░" * (width - filled)
