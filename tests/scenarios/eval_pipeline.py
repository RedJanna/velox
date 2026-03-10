"""Velox Eval Pipeline — 47 senaryoyu yukle, calistir, raporla.

Kullanim:
    # Tum senaryolar (default processor — mock)
    python -m tests.scenarios.eval_pipeline

    # Gercek LLM pipeline ile (OpenAI API key gerekir)
    python -m tests.scenarios.eval_pipeline --real

    # Sadece belirli kategori
    python -m tests.scenarios.eval_pipeline --category stay

    # Sadece belirli senaryolar
    python -m tests.scenarios.eval_pipeline --codes S001 S009 S041

    # Hizli mod (kritik 10 senaryo)
    python -m tests.scenarios.eval_pipeline --mode fast

    # Kombinasyon: hizli mod + gercek pipeline + JSON kaydet
    python -m tests.scenarios.eval_pipeline --mode fast --real --save-json
"""

import argparse
import asyncio
import sys
from typing import Any

from tests.scenarios.loader import load_all_scenarios, scenario_to_runner_format
from tests.scenarios.report import (
    generate_console_report,
    generate_json_report,
    save_json_report,
)
from tests.scenarios.runner import ScenarioResult, ScenarioRunner


# Hizli mod icin kritik senaryo listesi (testing_qa.md'den)
FAST_MODE_CODES = [
    "S001",  # Stay availability (happy path)
    "S003",  # Stay full flow (E2E)
    "S009",  # Group booking (handoff)
    "S017",  # Restaurant allergy (risk flag)
    "S021",  # Transfer oversize (sprinter)
    "S029",  # Honeymoon (special event)
    "S032",  # FAQ parking (ai_note trap)
    "S036",  # Angry complaint (escalation)
    "S041",  # Invalid date (edge case)
    "S046",  # PII leak (security)
]


async def run_eval(
    category: str | None = None,
    codes: list[str] | None = None,
    mode: str = "full",
    processor: Any | None = None,
) -> list[ScenarioResult]:
    """Load scenarios, run them, return results."""
    if mode == "fast":
        codes = FAST_MODE_CODES

    scenarios = load_all_scenarios(category=category, codes=codes)

    if not scenarios:
        print("Hicbir senaryo bulunamadi!")
        return []

    runner = ScenarioRunner(processor=processor)
    results: list[ScenarioResult] = []

    for scenario in scenarios:
        runner_format = scenario_to_runner_format(scenario)
        # category bilgisini runner_format'a ekle
        runner_format["category"] = scenario.get("category", "")
        result = await runner.run_scenario(runner_format)
        results.append(result)

    return results


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Velox Eval Pipeline — Senaryo bazli kalite kontrol",
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "mid", "full"],
        default="full",
        help="Test modu: fast (kritik 10), mid (kategori bazli), full (47 senaryo)",
    )
    parser.add_argument(
        "--category",
        choices=["stay", "restaurant", "transfer", "guest_ops", "general", "edge_case", "escalation"],
        default=None,
        help="Sadece belirli kategoriyi calistir",
    )
    parser.add_argument(
        "--codes",
        nargs="+",
        default=None,
        help="Sadece belirli senaryo kodlarini calistir (ornek: S001 S009)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        default=False,
        help="Gercek LLM pipeline kullan (OpenAI API key gerektirir)",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        default=False,
        help="JSON raporu data/eval_reports/ altina kaydet",
    )
    parser.add_argument(
        "--app-version",
        default="dev",
        help="Uygulama versiyonu (raporda gosterilir)",
    )
    return parser.parse_args()


async def main() -> int:
    """Entry point for eval pipeline."""
    args = parse_args()

    # Gercek pipeline kullanilacaksa processor olustur
    processor = None
    if args.real:
        from tests.scenarios.real_processor import RealPipelineProcessor

        processor = RealPipelineProcessor()
        print(f"\n  Velox Eval Pipeline baslatiliyor (mod: {args.mode}, processor: REAL LLM)...\n")
    else:
        print(f"\n  Velox Eval Pipeline baslatiliyor (mod: {args.mode}, processor: mock)...\n")

    results = await run_eval(
        category=args.category,
        codes=args.codes,
        mode=args.mode,
        processor=processor,
    )

    if not results:
        return 1

    # Console raporu
    console_report = generate_console_report(results, mode=args.mode)
    print(console_report)

    # JSON rapor
    if args.save_json:
        json_report = generate_json_report(
            results,
            mode=args.mode,
            app_version=args.app_version,
        )
        filepath = save_json_report(json_report)
        print(f"  JSON rapor kaydedildi: {filepath}\n")

    # Exit code: 0 = hepsi gecti, 1 = en az biri kaldi
    all_passed = all(r.passed for r in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
