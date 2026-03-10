#!/usr/bin/env python3
"""Velox Eval Pipeline — tek tusla calistirma scripti.

Kullanim:
    # Tum senaryolar
    python scripts/run_eval.py

    # Hizli mod (kritik 10 senaryo, ~1-3 dk)
    python scripts/run_eval.py --mode fast

    # Orta mod (tek kategori)
    python scripts/run_eval.py --category stay

    # Belirli senaryolar
    python scripts/run_eval.py --codes S001 S009 S041

    # JSON rapor kaydet
    python scripts/run_eval.py --save-json

    # Kombinasyon
    python scripts/run_eval.py --mode fast --save-json
"""

import sys
from pathlib import Path

# Proje kokunu sys.path'e ekle
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from tests.scenarios.eval_pipeline import main  # noqa: E402
import asyncio  # noqa: E402

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
