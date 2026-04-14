#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGETS=(
  "src/velox/api/routes/test_chat_ui.py"
  "src/velox/api/routes/test_chat_ui_assets.py"
  "src/velox/api/routes/admin_panel_ui.py"
  "src/velox/api/routes/admin_panel_ui_assets.py"
  "src/velox/api/routes/test_chat.py"
  "src/velox/core/chat_lab_feedback.py"
)

# User-facing legacy terms we do not want to reintroduce.
PATTERNS=(
  "Diagnostics"
  "Feedback Studio"
  "Conversation State"
  "Risk Flags"
  "Next Step"
  "Role Mapping"
  "Read only"
  "Importlar"
  "Altin Standart"
  "Niyet Iskalama"
  "Sorunlu"
  "Yeniden Isle"
  "Gonderme"
  "REDDEDILDI"
  "BEKLIYOR"
  "GONDERILDI"
  "Konusma"
  "Gonder"
  "Yuklen"
  "bulunamadi"
  "gecersiz"
  "Lutfen"
  "Baglanti"
)

found=0
for pattern in "${PATTERNS[@]}"; do
  if rg -n --color never "$pattern" "${TARGETS[@]}" >/tmp/chatlab_copy_smoke.out 2>/dev/null; then
    echo "[FAIL] Yasakli veya eski ifade bulundu: $pattern"
    cat /tmp/chatlab_copy_smoke.out
    echo
    found=1
  fi
done

rm -f /tmp/chatlab_copy_smoke.out

if [[ $found -ne 0 ]]; then
  exit 1
fi

echo "[OK] Chat Lab copy smoke check temiz."
