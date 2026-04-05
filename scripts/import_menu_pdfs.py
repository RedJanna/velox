"""Import menu PDFs and integrate them into HotelProfile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from velox.core.menu_pdf_importer import MenuPdfImportError, import_menu_pdfs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import menu PDF files into HotelProfile and restaurant.menu catalogue."
    )
    parser.add_argument("--hotel-id", type=int, required=True, help="Target hotel id")
    parser.add_argument(
        "--pdf",
        dest="pdfs",
        action="append",
        required=True,
        help="Path to a PDF file. Can be repeated.",
    )
    parser.add_argument(
        "--category",
        dest="categories",
        action="append",
        help="Optional category label for each --pdf. Order-based mapping.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    pdf_paths = [Path(item) for item in args.pdfs]
    categories = args.categories if args.categories else None
    try:
        result = import_menu_pdfs(
            hotel_id=args.hotel_id,
            document_paths=pdf_paths,
            categories=categories,
        )
    except MenuPdfImportError as exc:
        print(f"ERROR: {exc}")  # noqa: T201
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

