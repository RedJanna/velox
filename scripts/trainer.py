#!/usr/bin/env python3
"""Velox Interactive Trainer — Musteri gibi soru sor, puanla, ogret.

Kullanim:
    python scripts/trainer.py

Akis:
    1. Sen musteri gibi mesaj yazarsin
    2. Gercek LLM pipeline cevap verir
    3. Sen puanlarsin (1-5)
    4. Puan dusukse (1-3): dogru cevabi yazarsin
    5. Otomatik olarak yeni senaryo YAML uretilir
    6. data/scenarios/ klasorune kaydedilir
    7. Cikista ozet rapor gosterilir
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# Proje kokunu sys.path'e ekle
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from velox.config.constants import ConversationState  # noqa: E402
from velox.config.settings import settings  # noqa: E402
from velox.core.intent_engine import detect_intent  # noqa: E402
from velox.models.conversation import Conversation, Message  # noqa: E402

SCENARIOS_DIR = project_root / "data" / "scenarios"
TRAINING_LOG_DIR = project_root / "data" / "training_logs"


def _next_scenario_code() -> str:
    """Find next available scenario code (S048, S049, etc.)."""
    existing = sorted(SCENARIOS_DIR.glob("S*.yaml"))
    if not existing:
        return "S048"
    last = existing[-1].stem.split("_")[0]
    num = int(last.replace("S", "")) + 1
    return f"S{num:03d}"


def _slugify(text: str) -> str:
    """Create filesystem-safe slug from text."""
    slug = text.lower().strip()
    slug = slug.replace(" ", "_").replace("?", "").replace("!", "")
    slug = slug.replace("ı", "i").replace("ö", "o").replace("ü", "u")
    slug = slug.replace("ş", "s").replace("ç", "c").replace("ğ", "g")
    return slug[:40]


def _detect_category(user_message: str) -> str:
    """Detect scenario category from user message."""
    lowered = user_message.lower()
    if any(w in lowered for w in ["oda", "rezervasyon", "konaklama", "room", "book"]):
        return "stay"
    if any(w in lowered for w in ["restoran", "yemek", "masa", "kahvalti", "restaurant"]):
        return "restaurant"
    if any(w in lowered for w in ["transfer", "havalimani", "airport"]):
        return "transfer"
    if any(w in lowered for w in ["check-in", "check-out", "erken", "gec", "isim"]):
        return "guest_ops"
    if any(w in lowered for w in ["avukat", "hasta", "ambulans", "kredi kart"]):
        return "edge_case"
    return "general"


def _detect_risk_flags(user_message: str, ai_response: str, rating: int) -> list[str]:
    """Detect potential risk flags based on content."""
    flags: list[str] = []
    lowered_msg = user_message.lower()

    if any(w in lowered_msg for w in ["avukat", "hukuk", "yasal", "dava"]):
        flags.append("LEGAL_REQUEST")
    if any(w in lowered_msg for w in ["hasta", "ambulans", "bayil", "acil"]):
        flags.append("MEDICAL_EMERGENCY")
    if any(w in lowered_msg for w in ["kredi kart", "4532", "5678"]):
        flags.append("PII_OVERREQUEST")
    if any(w in lowered_msg for w in ["iade", "refund", "geri"]):
        flags.append("REFUND_DISPUTE")
    if any(w in lowered_msg for w in ["rezalet", "berbat", "bir daha kalmam"]):
        flags.append("ANGRY_COMPLAINT")
    if any(w in lowered_msg for w in ["alerji", "allergy"]):
        flags.append("ALLERGY_ALERT")
    if any(w in lowered_msg for w in ["balayi", "dogum gunu", "surpriz"]):
        flags.append("SPECIAL_EVENT")

    return flags


def _extract_must_not_terms(correct_answer: str, bad_answer: str) -> list[str]:
    """Extract terms that should NOT appear, based on what was wrong."""
    must_not: list[str] = []
    bad_words = bad_answer.lower().split()
    correct_words = correct_answer.lower().split()

    # Yanlis cevaptaki ama dogru cevaptaki olmayan anahtar kelimeler
    for word in bad_words:
        if len(word) > 4 and word not in correct_words:
            # Olasi halusin kelimeler
            if word not in ["ancak", "olarak", "icin", "evet", "hayir", "mevcut"]:
                must_not.append(word)

    return must_not[:5]  # En fazla 5 yasakli terim


def generate_scenario_yaml(
    user_message: str,
    ai_response: str,
    correct_answer: str,
    rating: int,
    reason: str,
    code: str,
) -> str:
    """Generate scenario YAML from training interaction."""
    category = _detect_category(user_message)
    intent = detect_intent(user_message).value
    risk_flags = _detect_risk_flags(user_message, ai_response, rating)

    # Dogru cevaptaki anahtar kelimeler -> expect_reply_contains
    contains_terms: list[str] = []
    correct_lower = correct_answer.lower()
    for word in correct_lower.split():
        if len(word) > 4 and word not in ["ancak", "olarak", "icin", "burada", "sizin"]:
            contains_terms.append(word)
    contains_terms = contains_terms[:5]

    # Yanlis cevaptaki sorunlu kelimeler -> expect_reply_must_not
    must_not_terms = _extract_must_not_terms(correct_answer, ai_response)

    lines: list[str] = []
    lines.append(f'code: "{code}"')
    lines.append(f'name: "Training - {user_message[:50]}"')
    lines.append(f'description: "Egitimden olusturuldu. Puan: {rating}/5. Sebep: {reason}"')
    lines.append(f'category: "{category}"')
    lines.append('language: "tr"')
    lines.append(f'tags: ["training", "{category}", "human_feedback"]')
    lines.append(f"source: \"trainer_{datetime.now(timezone.utc).strftime('%Y%m%d')}\"")
    lines.append("")
    lines.append("steps:")
    lines.append(f'  - user: "{user_message}"')
    lines.append(f'    expect_intent: "{intent}"')

    # State tahmini
    if risk_flags and any(f in ["LEGAL_REQUEST", "MEDICAL_EMERGENCY", "ANGRY_COMPLAINT"] for f in risk_flags):
        lines.append('    expect_state: "HANDOFF"')
    else:
        lines.append('    expect_state: "INTENT_DETECTED"')

    lines.append("    expect_tool_calls: []")

    if contains_terms:
        terms_str = ", ".join(f'"{t}"' for t in contains_terms)
        lines.append(f"    expect_reply_contains: [{terms_str}]")
    else:
        lines.append("    expect_reply_contains: []")

    if must_not_terms:
        must_not_str = ", ".join(f'"{t}"' for t in must_not_terms)
        lines.append(f"    expect_reply_must_not: [{must_not_str}]")
    else:
        lines.append("    expect_reply_must_not: []")

    if risk_flags:
        flags_str = ", ".join(f'"{f}"' for f in risk_flags)
        lines.append(f"    expect_risk_flags: [{flags_str}]")
    else:
        lines.append("    expect_risk_flags: []")

    lines.append(f'    note: "Dogru cevap: {correct_answer[:100]}"')

    return "\n".join(lines)


def save_scenario(yaml_content: str, code: str, user_message: str) -> Path:
    """Save scenario YAML to data/scenarios/."""
    slug = _slugify(user_message)
    filename = f"{code}_{slug}.yaml"
    filepath = SCENARIOS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(yaml_content)
    return filepath


def save_training_log(interactions: list[dict[str, Any]]) -> Path:
    """Save full training session log."""
    TRAINING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = TRAINING_LOG_DIR / f"training_{timestamp}.json"
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(interactions, fh, ensure_ascii=False, indent=2)
    return filepath


async def real_ai_response(
    user_message: str,
    conversation: Conversation,
) -> dict[str, Any]:
    """Gercek LLM pipeline'ini cagirarak AI cevabi al.

    Returns:
        dict: {
            "reply": str,           # Misafire gosterilecek cevap
            "intent": str,          # Algilanan intent
            "state": str,           # Yeni state
            "risk_flags": list,     # Risk flag'lari
            "tool_calls": list,     # Cagrilan tool'lar
            "internal_json": dict,  # Tam InternalJSON (debug icin)
        }
    """
    from velox.api.routes.whatsapp_webhook import _run_message_pipeline
    from velox.escalation.risk_detector import detect_all_risk_flags
    from velox.llm.response_parser import ResponseParser

    # Kullanici mesajini gecmise ekle
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
    )
    conversation.messages.append(user_msg)

    # Gercek pipeline'i cagir
    llm_response = await _run_message_pipeline(
        conversation=conversation,
        normalized_text=user_message,
        dispatcher=None,  # Mock tool executor kullanilacak
        expected_language=conversation.language,
    )

    # AI yanitini gecmise ekle (bir sonraki mesaj icin context)
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=llm_response.user_message,
        internal_json=llm_response.internal_json.model_dump(mode="json"),
    )
    conversation.messages.append(assistant_msg)

    # State guncelle
    new_state = llm_response.internal_json.state or conversation.current_state.value
    try:
        conversation.current_state = ConversationState(new_state)
    except ValueError:
        conversation.current_state = ConversationState.INTENT_DETECTED

    # Risk flag'lari birlestirilmis sekilde al
    risk_flags = detect_all_risk_flags(user_message, llm_response.internal_json)
    risk_flag_values = [f.value for f in risk_flags]

    # Tool call isimlerini cikar
    tool_calls = [
        tc["name"]
        for tc in ResponseParser.extract_tool_calls(llm_response.internal_json)
    ]

    return {
        "reply": llm_response.user_message,
        "intent": llm_response.internal_json.intent,
        "state": new_state,
        "risk_flags": risk_flag_values,
        "tool_calls": tool_calls,
        "internal_json": llm_response.internal_json.model_dump(mode="json"),
    }


async def interactive_session() -> None:
    """Run interactive training session with real LLM pipeline."""
    print("\n" + "=" * 60)
    print("  VELOX INTERACTIVE TRAINER")
    print("  Musteri gibi soru sor, cevabi puanla, sistemi egit!")
    print("  (Gercek LLM Pipeline aktif)")
    print("=" * 60)
    print()
    print("  Komutlar:")
    print("    /quit     — Cikis")
    print("    /summary  — Oturum ozeti")
    print("    /skip     — Bu cevabi atla")
    print("    /reset    — Konusmayi sifirla (yeni misafir)")
    print()

    interactions: list[dict[str, Any]] = []
    new_scenarios: list[str] = []

    # Her oturum icin bir Conversation olustur
    conv_id = uuid4()
    conversation = Conversation(
        id=conv_id,
        hotel_id=settings.elektra_hotel_id,
        phone_hash="trainer_session",
        phone_display="trainer***",
        language="tr",
        current_state=ConversationState.GREETING,
    )

    while True:
        # ADIM 1: Kullanicidan mesaj al
        print("-" * 40)
        user_input = input("  Sen (musteri): ").strip()

        if not user_input:
            continue
        if user_input == "/quit":
            break
        if user_input == "/summary":
            _print_summary(interactions, new_scenarios)
            continue
        if user_input == "/reset":
            conv_id = uuid4()
            conversation = Conversation(
                id=conv_id,
                hotel_id=settings.elektra_hotel_id,
                phone_hash="trainer_session",
                phone_display="trainer***",
                language="tr",
                current_state=ConversationState.GREETING,
            )
            print("  Konusma sifirlandi. Yeni misafir olarak devam edebilirsin.\n")
            continue

        # ADIM 2: AI cevap verir (gercek LLM pipeline)
        print("\n  Dusunuyor...", end="", flush=True)
        try:
            result = await real_ai_response(user_input, conversation)
            ai_response = result["reply"]
        except Exception as e:
            print(f"\r  HATA: {e}")
            print("  Pipeline calismiyor olabilir. .env dosyasinda OPENAI_API_KEY var mi?\n")
            continue

        # Cevabi ve debug bilgisini goster
        print(f"\r  AI: {ai_response}")
        print(f"      [intent={result['intent']} | state={result['state']} | "
              f"tools={result['tool_calls']} | flags={result['risk_flags']}]\n")

        # ADIM 3: Puanlama
        rating_input = ""
        while True:
            rating_input = input("  Puan (1-5, /skip): ").strip()
            if rating_input == "/skip":
                break
            try:
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    break
                print("  1-5 arasi bir sayi gir!")
            except ValueError:
                print("  Gecersiz! 1-5 arasi sayi veya /skip yaz.")

        if rating_input == "/skip":
            continue

        interaction: dict[str, Any] = {
            "user_message": user_input,
            "ai_response": ai_response,
            "rating": rating,
            "intent": result["intent"],
            "state": result["state"],
            "risk_flags": result["risk_flags"],
            "tool_calls": result["tool_calls"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # ADIM 4: Dusuk puanli ise dogru cevabi iste
        if rating <= 3:
            print(f"\n  Puan dusuk ({rating}/5). Dogru cevabi yaz:")
            reason = input("  Neden yanlis? (1 cumle): ").strip()
            correct = input("  Dogru cevap ne olmali?: ").strip()

            if correct:
                interaction["reason"] = reason
                interaction["correct_answer"] = correct

                # ADIM 5: Senaryo olustur
                code = _next_scenario_code()
                yaml_content = generate_scenario_yaml(
                    user_message=user_input,
                    ai_response=ai_response,
                    correct_answer=correct,
                    rating=rating,
                    reason=reason,
                    code=code,
                )

                filepath = save_scenario(yaml_content, code, user_input)
                new_scenarios.append(code)
                interaction["generated_scenario"] = code

                print(f"\n  ✅ Yeni senaryo olusturuldu: {code}")
                print(f"     Dosya: {filepath.name}")
                print()
        else:
            print(f"  ✅ Puan: {rating}/5 — iyi cevap!\n")

        interactions.append(interaction)

    # Cikista ozet ve log kaydet
    if interactions:
        log_path = save_training_log(interactions)
        print(f"\n  Egitim logu kaydedildi: {log_path}")

    _print_summary(interactions, new_scenarios)


def _print_summary(interactions: list[dict[str, Any]], new_scenarios: list[str]) -> None:
    """Print training session summary."""
    if not interactions:
        print("\n  Henuz etkilesim yok.\n")
        return

    total = len(interactions)
    avg_rating = sum(i["rating"] for i in interactions) / total
    low_rated = sum(1 for i in interactions if i["rating"] <= 3)

    print("\n" + "=" * 60)
    print("  EGITIM OTURUMU OZETI")
    print("=" * 60)
    print(f"  Toplam soru:           {total}")
    print(f"  Ortalama puan:         {avg_rating:.1f}/5")
    print(f"  Dusuk puanli (1-3):    {low_rated}")
    print(f"  Yeni senaryo uretilen: {len(new_scenarios)}")
    if new_scenarios:
        print(f"  Senaryo kodlari:       {', '.join(new_scenarios)}")
    print()
    if new_scenarios:
        print("  Sonraki adim:")
        print("    python scripts/eval_cycle.py --real")
        print("    (Yeni senaryolari gercek pipeline ile test edip FIX prompt uretir)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(interactive_session())
