#!/usr/bin/env python3
"""Gercek konusma kayitlarindan (DB export / JSON) senaryo YAML olusturur.

Kullanim:
    # Tek konusma dosyasindan
    python scripts/conversation_to_scenario.py --input conversation_export.json

    # Klasordeki tum konusmalardan
    python scripts/conversation_to_scenario.py --input-dir data/training_logs/

Bu script su kaynaklardan senaryo uretebilir:
    1. Admin panelden export edilen konusma JSON'lari
    2. Trainer script'in olusturdugu training_log JSON'lari
    3. CRM log'dan filtrelenmis sorunlu konusmalar

JSON formati (her konusma):
{
    "conversation_id": "conv_123",
    "messages": [
        {"role": "guest", "content": "Merhaba, oda var mi?"},
        {"role": "assistant", "content": "Hos geldiniz..."},
        ...
    ],
    "flags": ["escalated", "unknown_question"],
    "admin_notes": "Musafir sezon disi tarih sordu, sistem yanlis cevap verdi"
}
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from velox.core.intent_engine import detect_intent  # noqa: E402

SCENARIOS_DIR = project_root / "data" / "scenarios"


def _next_scenario_code() -> str:
    """Find next available scenario code."""
    existing = sorted(SCENARIOS_DIR.glob("S*.yaml"))
    if not existing:
        return "S048"
    last = existing[-1].stem.split("_")[0]
    num = int(last.replace("S", "")) + 1
    return f"S{num:03d}"


def _slugify(text: str) -> str:
    """Create filesystem-safe slug."""
    slug = text.lower().strip()[:40]
    for old, new in [(" ", "_"), ("?", ""), ("!", ""), ("ı", "i"), ("ö", "o"),
                     ("ü", "u"), ("ş", "s"), ("ç", "c"), ("ğ", "g")]:
        slug = slug.replace(old, new)
    return slug


def conversation_to_scenario(
    conversation: dict[str, Any],
    code: str,
) -> str:
    """Convert a conversation record to scenario YAML."""
    messages = conversation.get("messages", [])
    flags = conversation.get("flags", [])
    admin_notes = conversation.get("admin_notes", "")
    conv_id = conversation.get("conversation_id", "unknown")

    guest_messages = [m for m in messages if m.get("role") == "guest"]

    if not guest_messages:
        return ""

    first_msg = guest_messages[0]["content"]
    intent = detect_intent(first_msg).value
    slug = _slugify(first_msg)

    # Kategori tahmini
    category = "general"
    lowered = first_msg.lower()
    if any(w in lowered for w in ["oda", "rezervasyon", "konaklama"]):
        category = "stay"
    elif any(w in lowered for w in ["restoran", "yemek", "masa"]):
        category = "restaurant"
    elif any(w in lowered for w in ["transfer", "havaliman"]):
        category = "transfer"

    # Flag'lardan risk_flags cikar
    risk_flags: list[str] = []
    if "escalated" in flags:
        risk_flags.append("ANGRY_COMPLAINT")
    if "unknown_question" in flags:
        risk_flags.append("TEMPLATE_MISSING")

    lines: list[str] = []
    lines.append(f'code: "{code}"')
    lines.append(f'name: "Live - {first_msg[:50]}"')
    lines.append(f'description: "Canli konusmadan uretildi. Kaynak: {conv_id}. Not: {admin_notes[:80]}"')
    lines.append(f'category: "{category}"')
    lines.append('language: "tr"')
    lines.append(f'tags: ["live_feedback", "{category}"]')
    lines.append(f'source: "conversation_{conv_id}"')
    lines.append("")
    lines.append("steps:")

    for msg in messages:
        if msg["role"] == "guest":
            intent_val = detect_intent(msg["content"]).value
            lines.append(f'  - user: "{msg["content"][:200]}"')
            lines.append(f'    expect_intent: "{intent_val}"')
            lines.append('    expect_state: "INTENT_DETECTED"')
            lines.append("    expect_tool_calls: []")
            lines.append("    expect_reply_contains: []")
            lines.append("    expect_reply_must_not: []")
            if risk_flags:
                flags_str = ", ".join(f'"{f}"' for f in risk_flags)
                lines.append(f"    expect_risk_flags: [{flags_str}]")
            else:
                lines.append("    expect_risk_flags: []")
            lines.append(f'    note: "DUZENLEME GEREKLI — admin tarafindan expect alanlari doldurulmali"')
            lines.append("")

    return "\n".join(lines)


def process_file(input_path: Path) -> list[str]:
    """Process a single JSON file, return generated scenario codes."""
    with open(input_path, encoding="utf-8") as fh:
        data = json.load(fh)

    # Tek konusma veya liste olabilir
    conversations = data if isinstance(data, list) else [data]

    generated: list[str] = []

    for conv in conversations:
        # Sadece sorunlu konusmalari isle
        flags = conv.get("flags", [])
        rating = conv.get("rating", 5)

        has_problem = (
            "escalated" in flags
            or "unknown_question" in flags
            or "template_gap" in flags
            or "policy_gap" in flags
            or rating <= 3
        )

        if not has_problem:
            continue

        code = _next_scenario_code()
        yaml_content = conversation_to_scenario(conv, code)

        if not yaml_content:
            continue

        slug = _slugify(conv.get("messages", [{}])[0].get("content", "unknown"))
        filepath = SCENARIOS_DIR / f"{code}_{slug}.yaml"
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(yaml_content)

        generated.append(code)
        print(f"  ✅ {code} olusturuldu: {filepath.name}")

    return generated


def main() -> int:
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Konusma kayitlarindan senaryo olustur")
    parser.add_argument("--input", type=Path, help="Tek JSON dosyasi")
    parser.add_argument("--input-dir", type=Path, help="JSON dosyalari klasoru")
    args = parser.parse_args()

    if not args.input and not args.input_dir:
        print("Kullanim: --input dosya.json veya --input-dir klasor/")
        return 1

    all_generated: list[str] = []

    if args.input:
        all_generated.extend(process_file(args.input))

    if args.input_dir:
        for json_file in sorted(args.input_dir.glob("*.json")):
            all_generated.extend(process_file(json_file))

    print(f"\n  Toplam {len(all_generated)} yeni senaryo olusturuldu.")
    if all_generated:
        print(f"  Kodlar: {', '.join(all_generated)}")
        print(f"\n  NOT: Olusturulan senaryolarda 'DUZENLEME GEREKLI' isareti var.")
        print(f"  Admin olarak expect_reply_contains ve expect_reply_must_not alanlari doldurulmali.")
        print(f"\n  Sonraki adim: python scripts/eval_cycle.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
