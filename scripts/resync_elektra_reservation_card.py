"""Replay Elektra reservation-card voucher/note sync for an existing stay reservation."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from velox.adapters.elektraweb import sync_reservation_card_fields
from velox.db.database import close_db_pool, fetchrow, init_db_pool


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay Elektra reservation-card voucher/note sync for an existing stay hold.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--hold-id", help="Stay hold id, e.g. S_HOLD_009")
    group.add_argument("--reservation-no", help="Internal reservation number, e.g. VLX-21966-2604-0009")
    group.add_argument("--pms-reservation-id", help="Elektra reservation id, e.g. 91254161")
    parser.add_argument("--hotel-id", type=int, default=21966, help="Hotel id (default: 21966)")
    return parser


async def _load_hold(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.hold_id:
        return await fetchrow(
            """
            SELECT hold_id, hotel_id, pms_reservation_id, voucher_no, reservation_no, draft_json
            FROM stay_holds
            WHERE hold_id = $1
            """,
            args.hold_id,
        )
    if args.reservation_no:
        return await fetchrow(
            """
            SELECT hold_id, hotel_id, pms_reservation_id, voucher_no, reservation_no, draft_json
            FROM stay_holds
            WHERE reservation_no = $1
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            args.reservation_no,
        )
    return await fetchrow(
        """
        SELECT hold_id, hotel_id, pms_reservation_id, voucher_no, reservation_no, draft_json
        FROM stay_holds
        WHERE pms_reservation_id = $1
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        args.pms_reservation_id,
    )


async def _run(args: argparse.Namespace) -> int:
    await init_db_pool()
    try:
        row = await _load_hold(args)
        if row is None:
            print("hold_not_found")
            return 1

        draft_json = row["draft_json"] or {}
        reservation_id = str(row["pms_reservation_id"] or "").strip()
        reservation_no = str(row["reservation_no"] or "").strip()
        notes = str((draft_json or {}).get("notes") or "").strip()
        hotel_id = int(row["hotel_id"] or args.hotel_id)
        hold_id = str(row["hold_id"] or "").strip()

        if not reservation_id:
            print(f"hold_missing_pms_reservation_id hold_id={hold_id}")
            return 2
        if not reservation_no:
            print(f"hold_missing_reservation_no hold_id={hold_id} reservation_id={reservation_id}")
            return 3

        result = await sync_reservation_card_fields(
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            voucher_no=reservation_no,
            notes=notes,
        )

        if result.get("voucher_synced"):
            await fetchrow(
                """
                UPDATE stay_holds
                SET voucher_no = COALESCE($2, voucher_no),
                    updated_at = now()
                WHERE hold_id = $1
                RETURNING hold_id
                """,
                hold_id,
                reservation_no,
            )

        print(
            "sync_result "
            f"hold_id={hold_id} "
            f"reservation_id={reservation_id} "
            f"voucher_requested={bool(result.get('voucher_requested'))} "
            f"voucher_synced={bool(result.get('voucher_synced'))} "
            f"notes_requested={bool(result.get('notes_requested'))} "
            f"notes_synced={bool(result.get('notes_synced'))}"
        )
        return 0 if (result.get("voucher_synced") or result.get("notes_synced")) else 4
    finally:
        await close_db_pool()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
