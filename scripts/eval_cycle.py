#!/usr/bin/env python3
"""Velox Eval Dongusu — tek komutla: eval calistir + rapor olustur + fix prompt hazirla.

Kullanim:
    python scripts/eval_cycle.py
    python scripts/eval_cycle.py --mode fast
    python scripts/eval_cycle.py --mode fast --real   # Gercek LLM pipeline

Bu script su 3 adimi sirayla yapar:
    1. Eval pipeline'i calistirir (47 senaryo)
    2. JSON raporu kaydeder
    3. Basarisiz senaryolar varsa fix prompt olusturur

Cikti olarak 2 dosya uretir:
    - data/eval_reports/EVAL-{tarih}.json     (makine icin)
    - data/eval_reports/EVAL-{tarih}_FIX.txt  (Codex'e kopyala-yapistir icin)
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Proje kokunu sys.path'e ekle
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from tests.scenarios.eval_pipeline import run_eval  # noqa: E402
from tests.scenarios.report import (  # noqa: E402
    generate_console_report,
    generate_json_report,
    save_json_report,
)
from scripts.generate_fix_prompt import generate_prompt, load_report  # noqa: E402

REPORTS_DIR = project_root / "data" / "eval_reports"


async def eval_cycle(mode: str = "full", use_real: bool = False) -> int:
    """Run full eval cycle: test → report → fix prompt."""

    # Gercek pipeline kullanilacaksa processor olustur
    processor = None
    if use_real:
        from tests.scenarios.real_processor import RealPipelineProcessor

        processor = RealPipelineProcessor()

    processor_label = "REAL LLM" if use_real else "mock"

    # ── Adim 1: Eval calistir ──
    print("\n" + "=" * 60)
    print(f"  ADIM 1/3: Eval calistiriliyor (processor: {processor_label})...")
    print("=" * 60)

    results = await run_eval(mode=mode, processor=processor)

    if not results:
        print("  Hicbir senaryo bulunamadi!")
        return 1

    # Console raporu goster
    console_report = generate_console_report(results, mode=mode)
    print(console_report)

    # ── Adim 2: JSON rapor kaydet ──
    print("=" * 60)
    print("  ADIM 2/3: JSON rapor kaydediliyor...")
    print("=" * 60)

    json_report = generate_json_report(results, mode=mode)
    report_path = save_json_report(json_report, REPORTS_DIR)
    print(f"  Kaydedildi: {report_path}")

    # ── Adim 3: Fix prompt olustur ──
    all_passed = all(r.passed for r in results)

    if all_passed:
        print("\n" + "=" * 60)
        print("  TUM SENARYOLAR GECTI!")
        print("  Fix prompt olusturmaya gerek yok.")
        print("=" * 60 + "\n")
        return 0

    print("\n" + "=" * 60)
    print("  ADIM 3/3: Fix prompt olusturuluyor...")
    print("=" * 60)

    report_data = load_report(report_path)
    fix_prompt = generate_prompt(report_data)

    fix_path = report_path.with_name(report_path.stem + "_FIX.txt")
    with open(fix_path, "w", encoding="utf-8") as fh:
        fh.write(fix_prompt)

    failed_count = sum(1 for r in results if not r.passed)
    total_count = len(results)
    passed_count = total_count - failed_count

    print(f"\n  Fix prompt kaydedildi: {fix_path}")
    print(f"\n  Sonuc: {passed_count}/{total_count} gecti, {failed_count} basarisiz")
    print(f"\n  Simdi ne yapacaksin:")
    print(f"    1. {fix_path} dosyasini ac")
    print(f"    2. Icindeki metni Codex'e kopyala-yapistir")
    print(f"    3. Codex duzeltmeleri yapsın")
    print(f"    4. Tekrar calistir: python scripts/eval_cycle.py")
    print(f"    5. %95+ olana kadar tekrarla")
    print("=" * 60 + "\n")

    return 1


def main() -> int:
    """Entry point."""
    mode = "full"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    use_real = "--real" in sys.argv

    return asyncio.run(eval_cycle(mode=mode, use_real=use_real))


if __name__ == "__main__":
    sys.exit(main())
