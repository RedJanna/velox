#!/usr/bin/env python3
"""Eval raporundan Codex-ready fix prompt olusturur.

Kullanim:
    # Once eval calistir ve JSON kaydet
    python scripts/run_eval.py --save-json

    # Sonra fix prompt olustur
    python scripts/generate_fix_prompt.py

    # Belirli bir rapor dosyasindan
    python scripts/generate_fix_prompt.py --report data/eval_reports/EVAL-20260310-143000.json

    # Ciktiyi dosyaya kaydet (Codex'e kopyala-yapistir icin)
    python scripts/generate_fix_prompt.py --output fix_prompt.txt
"""

import argparse
import json
import sys
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parents[1] / "data" / "eval_reports"
SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "data" / "scenarios"


def find_latest_report(directory: Path) -> Path | None:
    """Find most recent eval report JSON."""
    reports = sorted(directory.glob("EVAL-*.json"), reverse=True)
    return reports[0] if reports else None


def load_report(filepath: Path) -> dict:
    """Load JSON report."""
    with open(filepath, encoding="utf-8") as fh:
        return json.load(fh)


def load_scenario_yaml(code: str) -> str:
    """Load raw YAML content for a scenario code."""
    for yaml_file in SCENARIOS_DIR.glob(f"{code}_*.yaml"):
        with open(yaml_file, encoding="utf-8") as fh:
            return fh.read()
    return ""


def generate_prompt(report: dict) -> str:
    """Generate Codex-ready fix prompt from eval report."""
    failures = report.get("failures", [])

    if not failures:
        return "Tum senaryolar gecti! Duzeltme gerekmiyor."

    lines: list[str] = []

    # Header
    lines.append("# VELOX EVAL DUZELTME TALIMATI")
    lines.append("")
    lines.append("Asagidaki eval raporunda bazi senaryolar basarisiz oldu.")
    lines.append("Her basarisiz senaryo icin:")
    lines.append("1. Hatanin kaynagini bul (prompt mu, template mi, tool mu, policy mi?)")
    lines.append("2. Ilgili dosyayi duzelt")
    lines.append("3. Duzeltmenin baska senaryolari bozmadiginden emin ol")
    lines.append("")
    lines.append(f"Toplam basarisiz: {len(failures)} senaryo")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Each failure
    for i, failure in enumerate(failures, 1):
        code = failure["scenario_code"]
        name = failure["scenario_name"]
        category = failure["category"]
        severity = failure["severity"]

        lines.append(f"## Hata {i}: {code} — {name}")
        lines.append(f"Kategori: {category} | Onem: {severity}")
        lines.append("")

        # Show failed steps
        for step in failure.get("failed_steps", []):
            step_idx = step["step_index"]
            user_msg = step["user_message"]
            lines.append(f"### Adim {step_idx}")
            lines.append(f"Misafir mesaji: \"{user_msg}\"")
            lines.append("")
            lines.append("Hatalar:")
            for err in step["errors"]:
                lines.append(f"  - {err}")
            lines.append("")

            actual = step.get("actual_response", {})
            lines.append("Sistemin verdigi gercek cevap:")
            lines.append(f"  intent:     {actual.get('intent')}")
            lines.append(f"  state:      {actual.get('state')}")
            lines.append(f"  tool_calls: {actual.get('tool_calls')}")
            lines.append(f"  risk_flags: {actual.get('risk_flags')}")
            lines.append(f"  reply:      \"{actual.get('reply_preview', '')}\"")
            lines.append("")

        # Show expected scenario YAML
        scenario_yaml = load_scenario_yaml(code)
        if scenario_yaml:
            lines.append("### Beklenen Senaryo (YAML)")
            lines.append("```yaml")
            lines.append(scenario_yaml.strip())
            lines.append("```")
            lines.append("")

        # Categorize the fix
        lines.append("### Olasi Duzeltme Alanlari")
        for step in failure.get("failed_steps", []):
            for err in step["errors"]:
                if "[QC1]" in err:
                    lines.append("- [ ] Intent algilama: `src/velox/core/intent_engine.py`")
                elif "[QC2]" in err:
                    lines.append("- [ ] State gecisi: `src/velox/core/state_machine.py`")
                elif "[QC3]" in err:
                    lines.append("- [ ] Tool cagirma: `src/velox/llm/function_registry.py`")
                elif "[QC4]" in err:
                    lines.append("- [ ] Yanit icerigi: `src/velox/llm/prompt_builder.py` veya template")
                elif "[QC5]" in err:
                    lines.append("- [ ] Yasakli icerik: `src/velox/llm/prompt_builder.py` veya template")
                elif "[QC6]" in err:
                    lines.append("- [ ] Risk flag: `src/velox/escalation/risk_detector.py`")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Footer
    lines.append("## ONEMLI KURALLAR")
    lines.append("- Duzeltme yaparken baska senaryolari bozma")
    lines.append("- Fiyat her zaman EUR (€) cinsinden goster")
    lines.append("- Hotel profile'da olmayan bilgi uydurma (halusin)")
    lines.append("- Kodlama standartlari: velox/skills/coding_standards.md")
    lines.append("- Hata yonetimi: velox/skills/error_handling.md")
    lines.append("- Guvenlik: velox/skills/security_privacy.md")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Eval raporundan Codex fix prompt olustur")
    parser.add_argument("--report", type=Path, default=None, help="Belirli bir rapor dosyasi")
    parser.add_argument("--output", type=Path, default=None, help="Prompt'u dosyaya kaydet")
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()

    if args.report:
        report_path = args.report
    else:
        report_path = find_latest_report(REPORTS_DIR)

    if not report_path or not report_path.exists():
        print("Eval raporu bulunamadi! Once calistirin: python scripts/run_eval.py --save-json")
        return 1

    report = load_report(report_path)
    prompt = generate_prompt(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(prompt)
        print(f"Fix prompt kaydedildi: {args.output}")
    else:
        print(prompt)

    return 0


if __name__ == "__main__":
    sys.exit(main())
