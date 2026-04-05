"""Menu PDF importer for HotelProfile integration."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from velox.core.hotel_profile_loader import get_profile, load_all_profiles, save_profile_definition
from velox.utils.project_paths import get_project_root

_PRICE_RE = re.compile(
    r"(?P<price>\d{1,4}(?:[.,]\d{1,2})?)\s*(?P<currency>EUR|€|TRY|TL|₺|USD|\$|GBP|£|RUB|₽)?",
    flags=re.IGNORECASE,
)

_NOISE_LINE_RE = re.compile(r"^(page\s*\d+|\d+/\d+|menu|wine list|snack)$", flags=re.IGNORECASE)


class MenuPdfImportError(RuntimeError):
    """Raised when a menu PDF import cannot complete."""


@dataclass(slots=True)
class ParsedMenuDocument:
    """Parsed menu document output."""

    category: str
    copied_file: str
    extracted_items: list[dict[str, str]]


def import_menu_pdfs(
    *,
    hotel_id: int,
    document_paths: list[Path],
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Import menu PDFs into project data and update the target hotel profile."""
    if not document_paths:
        raise MenuPdfImportError("En az bir PDF dosya yolu verilmelidir.")

    load_all_profiles()
    profile = get_profile(hotel_id)
    if profile is None:
        raise MenuPdfImportError(f"HotelProfile bulunamadi: hotel_id={hotel_id}")

    project_root = get_project_root()
    menu_root = project_root / "data" / "menus" / f"hotel_{hotel_id}"
    menu_root.mkdir(parents=True, exist_ok=True)

    parsed_documents: list[ParsedMenuDocument] = []
    for idx, source_path in enumerate(document_paths):
        source = source_path.expanduser().resolve()
        if not source.exists():
            raise MenuPdfImportError(f"PDF dosyasi bulunamadi: {source}")
        if source.suffix.lower() != ".pdf":
            raise MenuPdfImportError(f"Sadece PDF desteklenir: {source}")

        category = _normalize_category(
            categories[idx] if categories and idx < len(categories) else source.stem,
        )
        copied_name = f"{category}.pdf"
        copied_path = menu_root / copied_name
        shutil.copy2(source, copied_path)

        lines = _extract_pdf_lines(copied_path)
        items = _extract_items_from_lines(lines, source_label=category)
        parsed_documents.append(
            ParsedMenuDocument(
                category=category,
                copied_file=str(copied_path.relative_to(project_root)).replace("\\", "/"),
                extracted_items=items,
            )
        )

    profile_payload = profile.model_dump(mode="json")
    assistant_payload = profile_payload.get("assistant")
    if not isinstance(assistant_payload, dict):
        assistant_payload = {}
        profile_payload["assistant"] = assistant_payload

    assistant_payload["menu_source_documents"] = [doc.copied_file for doc in parsed_documents]
    if not str(assistant_payload.get("menu_scope_prompt", "")).strip():
        assistant_payload["menu_scope_prompt"] = _default_menu_scope_prompt(
            [doc.copied_file for doc in parsed_documents]
        )

    restaurant_payload = profile_payload.get("restaurant")
    if not isinstance(restaurant_payload, dict):
        restaurant_payload = {}
        profile_payload["restaurant"] = restaurant_payload

    existing_menu = restaurant_payload.get("menu")
    menu_payload = existing_menu if isinstance(existing_menu, dict) else {}
    for document in parsed_documents:
        menu_payload[document.category] = document.extracted_items
    restaurant_payload["menu"] = menu_payload

    saved_path = save_profile_definition(profile_payload)
    return {
        "hotel_id": hotel_id,
        "profile_path": str(saved_path),
        "menu_directory": str(menu_root),
        "imported_documents": [
            {
                "category": item.category,
                "copied_file": item.copied_file,
                "item_count": len(item.extracted_items),
            }
            for item in parsed_documents
        ],
    }


def _extract_pdf_lines(pdf_path: Path) -> list[str]:
    """Extract normalized lines from a PDF file."""
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - import guard
        raise MenuPdfImportError(
            "PDF import icin 'pypdf' gerekli. Lutfen ortama pypdf kurun."
        ) from exc

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise MenuPdfImportError(f"PDF okunamadi: {pdf_path}") from exc

    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            normalized = _normalize_line(raw_line)
            if normalized:
                lines.append(normalized)
    return lines


def _normalize_line(value: str) -> str:
    compact = " ".join(str(value or "").strip().split())
    if len(compact) < 2:
        return ""
    if _NOISE_LINE_RE.match(compact):
        return ""
    return compact


def _extract_items_from_lines(lines: list[str], *, source_label: str) -> list[dict[str, str]]:
    """Build a compact menu item list from extracted PDF lines."""
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in lines:
        match = _PRICE_RE.search(line)
        if match:
            raw_name = line[: match.start()].strip(" .:-")
            if _looks_like_item_name(raw_name):
                price = match.group("price") or ""
                currency = (match.group("currency") or "").upper()
                normalized_name = raw_name.casefold()
                if normalized_name in seen:
                    continue
                seen.add(normalized_name)
                items.append(
                    {
                        "name": raw_name,
                        "price_text": f"{price} {currency}".strip(),
                        "source_document": source_label,
                    }
                )

    if items:
        return items

    fallback_items: list[dict[str, str]] = []
    for line in lines[:80]:
        if _looks_like_item_name(line):
            normalized_name = line.casefold()
            if normalized_name in seen:
                continue
            seen.add(normalized_name)
            fallback_items.append(
                {
                    "name": line,
                    "price_text": "",
                    "source_document": source_label,
                }
            )
        if len(fallback_items) >= 80:
            break
    return fallback_items


def _looks_like_item_name(value: str) -> bool:
    cleaned = str(value or "").strip()
    if len(cleaned) < 2 or len(cleaned) > 120:
        return False
    letter_count = sum(1 for char in cleaned if char.isalpha())
    if letter_count < 2:
        return False
    return True


def _normalize_category(value: str) -> str:
    lowered = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return lowered or "menu"


def _default_menu_scope_prompt(source_documents: list[str]) -> str:
    listed = "\n".join(f"- {item}" for item in source_documents)
    return (
        "[RESTAURANT_MENU_STRICT_MODE]\n\n"
        "Restoran menusu sorularinda yalnizca asagidaki kaynak dosyalari kullan:\n"
        f"{listed}\n\n"
        "Sadece dosyalarda acikca gecen urun, icerik, aciklama ve fiyat bilgisini paylas.\n"
        "Dosyada yoksa tahmin yapma; acikca bilmedigini belirt.\n\n"
        "[END_RESTAURANT_MENU_STRICT_MODE]"
    )

