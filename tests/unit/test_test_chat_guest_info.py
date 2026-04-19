"""Regression checks for Chat Lab guest info payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from velox.api.routes import test_chat


class _ConversationDetailPool:
    def __init__(
        self,
        *,
        hold_row: dict[str, object] | None,
        fallback_hold_row: dict[str, object] | None = None,
        msg_rows: list[dict[str, object]] | None = None,
    ) -> None:
        self.conversation_id = uuid4()
        now = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)
        self.conv_row = {
            "id": self.conversation_id,
            "phone_hash": "phone_hash_905304498453",
            "phone_display": "+90 532 555 12 34",
            "language": "tr",
            "current_state": "PENDING_APPROVAL",
            "current_intent": "stay_booking_create",
            "risk_flags": ["PAYMENT_CONFUSION"],
            "is_active": True,
            "human_override": False,
            "hotel_id": 21966,
            "created_at": now,
            "last_message_at": now,
        }
        self.hold_row = hold_row
        self.fallback_hold_row = fallback_hold_row
        self.msg_rows = msg_rows or [
            {
                "id": uuid4(),
                "role": "user",
                "content": "20-23 Mayıs için rezervasyon yapabilir miyiz?",
                "internal_json": {},
                "created_at": now,
            },
            {
                "id": uuid4(),
                "role": "assistant",
                "content": "Rezervasyon detaylarını hazırlıyorum.",
                "internal_json": {"provider_status": "sent"},
                "created_at": now,
            },
        ]

    async def fetchrow(self, query: str, *args: object):
        if "FROM conversations WHERE id = $1" in query:
            assert args == (self.conversation_id,)
            return self.conv_row
        if "FROM stay_holds" in query and "JOIN conversations c ON c.id = sh.conversation_id" not in query:
            assert args == (self.conversation_id,)
            return self.hold_row
        if "JOIN conversations c ON c.id = sh.conversation_id" in query:
            assert args == (21966, "phone_hash_905304498453")
            return self.fallback_hold_row
        raise AssertionError(f"Unsupported fetchrow query: {query}")

    async def fetch(self, query: str, *args: object):
        if "FROM messages" in query:
            assert args == (self.conversation_id,)
            return self.msg_rows
        raise AssertionError(f"Unsupported fetch query: {query}")


def _request(pool: _ConversationDetailPool) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=pool)))


@pytest.mark.asyncio
async def test_conversation_detail_includes_guest_info_from_stay_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_profile = SimpleNamespace(
        room_types=[
            SimpleNamespace(
                id=4,
                pms_room_type_id=104,
                name=SimpleNamespace(tr="Deniz Manzaralı Oda", en="Sea View Room"),
            )
        ],
        board_types=[
            SimpleNamespace(
                id=2,
                code="BB",
                name=SimpleNamespace(tr="Kahvaltı Dahil", en="Bed & Breakfast"),
            )
        ],
    )
    monkeypatch.setattr(test_chat, "get_profile", lambda hotel_id: fake_profile)
    monkeypatch.setattr(test_chat, "load_all_profiles", lambda: {21966: fake_profile})
    async def _fake_find_reservation_list_match(
        hotel_id: int,
        *,
        reservation_id: str | None = None,
        voucher_no: str | None = None,
        contact_phone: str | None = None,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ):
        assert hotel_id == 21966
        assert reservation_id == "RES-44"
        assert voucher_no == "V-44"
        assert contact_phone == "+90 532 555 12 34"
        assert checkin_date == "2026-05-20"
        assert checkout_date == "2026-05-23"
        return SimpleNamespace(state="Reservation", raw_data={})

    monkeypatch.setattr(test_chat, "find_reservation_list_match", _fake_find_reservation_list_match)

    hold_row = {
        "hold_id": "S_HOLD_9001",
        "status": "PENDING_APPROVAL",
        "draft_json": {
            "guest_name": "Lisa Richardson",
            "phone": "+90 532 555 12 34",
            "email": "lisa@example.com",
            "nationality": "TR",
            "checkin_date": "2026-05-20",
            "checkout_date": "2026-05-23",
            "adults": 2,
            "chd_ages": [6],
            "room_type_id": 4,
            "board_type_id": "BB",
            "total_price_eur": "450",
            "currency_display": "EUR",
        },
        "pms_reservation_id": "RES-44",
        "voucher_no": "V-44",
        "reservation_no": "VLX-21966-44",
        "manual_review_reason": None,
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None,
        "created_at": datetime(2026, 4, 19, 12, 0, tzinfo=UTC),
    }
    pool = _ConversationDetailPool(hold_row=hold_row)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is True
    assert guest_info["guest_name"] == "Lisa Richardson"
    assert guest_info["room_label"] == "Deniz Manzaralı Oda"
    assert guest_info["board_label"] == "Kahvaltı Dahil"
    assert guest_info["nights"] == 3
    assert guest_info["children"] == 1
    assert guest_info["approve_enabled"] is True
    assert guest_info["cancel_enabled"] is True
    assert guest_info["cancel_action"] == "cancel_reservation"
    assert guest_info["reservation_reference"] == "V-44"


@pytest.mark.asyncio
async def test_conversation_detail_exposes_guest_info_status_when_hold_is_missing() -> None:
    pool = _ConversationDetailPool(hold_row=None)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is False
    assert guest_info["hold_status_label"] == "Rezervasyon Kaydı Yok"
    assert guest_info["approve_enabled"] is False
    assert guest_info["cancel_enabled"] is False
    assert "rezervasyon kaydı bağlı değil" in guest_info["info_status_label"].lower()


@pytest.mark.asyncio
async def test_conversation_detail_falls_back_to_system_event_reservation_data_when_draft_is_sparse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold_row = {
        "hold_id": "S_HOLD_9013",
        "status": "PAYMENT_PENDING",
        "draft_json": {
            "guest_name": "Udeneme UUdeneme",
            "phone": "+90 532 555 12 34",
        },
        "pms_reservation_id": "91604489",
        "voucher_no": "",
        "reservation_no": "VLX-21966-2604-0013",
        "manual_review_reason": None,
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None,
        "created_at": datetime(2026, 4, 19, 12, 0, tzinfo=UTC),
    }
    msg_rows = [
        {
            "id": uuid4(),
            "role": "system",
            "content": "SYSTEM_EVENT: approval.updated",
            "internal_json": {
                "event_type": "approval.updated",
                "tool_results": {
                    "booking_get_reservation": {
                        "success": True,
                        "result": {
                            "total_price": "1330",
                            "currency_code": "EUR",
                            "raw_data": {
                                "contact_name": "Udeneme UUdeneme",
                                "checkin_date": "2026-10-01",
                                "checkout_date": "2026-10-06",
                                "room_type": "Premium",
                                "board_type": "BB",
                            },
                        },
                    }
                },
            },
            "created_at": datetime(2026, 4, 19, 12, 1, tzinfo=UTC),
        }
    ]
    pool = _ConversationDetailPool(hold_row=hold_row, msg_rows=msg_rows)

    async def _fake_find_reservation_list_match(
        hotel_id: int,
        *,
        reservation_id: str | None = None,
        voucher_no: str | None = None,
        contact_phone: str | None = None,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ):
        assert hotel_id == 21966
        assert reservation_id == "91604489"
        assert voucher_no == "VLX-21966-2604-0013"
        return SimpleNamespace(state="Reservation", raw_data={})

    monkeypatch.setattr(test_chat, "find_reservation_list_match", _fake_find_reservation_list_match)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is True
    assert guest_info["info_status_label"] == "Misafir bilgi durumu: stay hold + PMS rezervasyonu bağlı"
    assert guest_info["reservation_reference"] == "VLX-21966-2604-0013"
    assert guest_info["checkin_date"] == "2026-10-01"
    assert guest_info["checkout_date"] == "2026-10-06"
    assert guest_info["nights"] == 5
    assert guest_info["room_label"] == "Premium"
    assert guest_info["board_label"] == "BB"
    assert guest_info["total_price_display"] == "1330 EUR"


@pytest.mark.asyncio
async def test_conversation_detail_loads_guest_info_from_same_phone_previous_conversation_hold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fallback_hold_row = {
        "hold_id": "S_HOLD_013",
        "status": "PAYMENT_PENDING",
        "draft_json": {
            "guest_name": "Udeneme UUdeneme",
            "phone": "+905304498453",
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-06",
            "room_type_id": 438550,
            "board_type_id": 1,
            "total_price_eur": "1330",
            "currency_display": "EUR",
            "adults": 2,
            "chd_ages": [12, 11],
        },
        "pms_reservation_id": "91604489",
        "voucher_no": "",
        "reservation_no": "VLX-21966-2604-0013",
        "manual_review_reason": None,
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None,
        "created_at": datetime(2026, 4, 19, 12, 0, tzinfo=UTC),
    }
    pool = _ConversationDetailPool(hold_row=None, fallback_hold_row=fallback_hold_row)

    async def _fake_find_reservation_list_match(
        hotel_id: int,
        *,
        reservation_id: str | None = None,
        voucher_no: str | None = None,
        contact_phone: str | None = None,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ):
        assert hotel_id == 21966
        assert reservation_id == "91604489"
        assert voucher_no == "VLX-21966-2604-0013"
        return SimpleNamespace(state="Reservation", raw_data={})

    monkeypatch.setattr(test_chat, "find_reservation_list_match", _fake_find_reservation_list_match)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is True
    assert guest_info["hold_id"] == "S_HOLD_013"
    assert guest_info["pms_reservation_id"] == "91604489"
    assert guest_info["reservation_reference"] == "VLX-21966-2604-0013"
    assert guest_info["info_status_label"] == "Misafir bilgi durumu: stay hold + PMS rezervasyonu bağlı"


@pytest.mark.asyncio
async def test_conversation_detail_enriches_missing_guest_fields_from_live_pms_readback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold_row = {
        "hold_id": "S_HOLD_013",
        "status": "PAYMENT_PENDING",
        "draft_json": {
            "guest_name": "Udeneme UUdeneme",
            "phone": "+905304498453",
        },
        "pms_reservation_id": "91604489",
        "voucher_no": "",
        "reservation_no": "VLX-21966-2604-0013",
        "manual_review_reason": None,
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None,
        "created_at": datetime(2026, 4, 19, 12, 0, tzinfo=UTC),
    }
    pool = _ConversationDetailPool(hold_row=hold_row, msg_rows=[])

    async def _fake_find_reservation_list_match(
        hotel_id: int,
        *,
        reservation_id: str | None = None,
        voucher_no: str | None = None,
        contact_phone: str | None = None,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ):
        assert hotel_id == 21966
        assert reservation_id == "91604489"
        assert voucher_no == "VLX-21966-2604-0013"
        return SimpleNamespace(
            state="Reservation",
            total_price=Decimal("1330"),
            raw_data={
                "contact_name": "Udeneme UUdeneme",
                "checkin_date": "2026-10-01",
                "checkout_date": "2026-10-06",
                "room_type": "Premium",
                "board_type": "BB",
                "adult_count": 2,
                "child_count": 2,
                "currency_code": "EUR",
            },
        )

    monkeypatch.setattr(test_chat, "find_reservation_list_match", _fake_find_reservation_list_match)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is True
    assert guest_info["checkin_date"] == "2026-10-01"
    assert guest_info["checkout_date"] == "2026-10-06"
    assert guest_info["nights"] == 5
    assert guest_info["room_label"] == "Premium"
    assert guest_info["board_label"] == "BB"
    assert guest_info["adults"] == 2
    assert guest_info["children"] == 2
    assert guest_info["total_price_display"] == "1330 EUR"


@pytest.mark.asyncio
async def test_conversation_detail_hides_guest_details_when_pms_reservation_is_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold_row = {
        "hold_id": "S_HOLD_013",
        "status": "PAYMENT_PENDING",
        "draft_json": {
            "guest_name": "Udeneme UUdeneme",
            "phone": "+905304498453",
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-06",
            "room_type_id": 438550,
            "board_type_id": 1,
            "total_price_eur": "1330",
            "currency_display": "EUR",
        },
        "pms_reservation_id": "91604489",
        "voucher_no": "",
        "reservation_no": "VLX-21966-2604-0013",
        "manual_review_reason": None,
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None,
        "created_at": datetime(2026, 4, 19, 12, 0, tzinfo=UTC),
    }
    pool = _ConversationDetailPool(hold_row=hold_row, msg_rows=[])

    async def _fake_find_reservation_list_match(
        hotel_id: int,
        *,
        reservation_id: str | None = None,
        voucher_no: str | None = None,
        contact_phone: str | None = None,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ):
        assert hotel_id == 21966
        assert reservation_id == "91604489"
        assert voucher_no == "VLX-21966-2604-0013"
        return SimpleNamespace(state="Cancelled", raw_data={"status": "Cancelled"})

    monkeypatch.setattr(test_chat, "find_reservation_list_match", _fake_find_reservation_list_match)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is False
    assert "pasif" in guest_info["info_status_label"].lower()
    assert guest_info["hold_status_label"] == "PMS Rezervasyonu Pasif"
    assert guest_info["checkin_date"] == "-"
    assert guest_info["checkout_date"] == "-"
    assert guest_info["room_label"] == "-"
    assert guest_info["total_price_display"] == "-"
    assert guest_info["approve_enabled"] is False
    assert guest_info["cancel_enabled"] is False


@pytest.mark.asyncio
async def test_conversation_detail_hides_guest_details_when_pms_reservation_is_missing_from_live_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold_row = {
        "hold_id": "S_HOLD_013",
        "status": "PAYMENT_PENDING",
        "draft_json": {
            "guest_name": "Udeneme UUdeneme",
            "phone": "+905304498453",
            "checkin_date": "2026-10-01",
            "checkout_date": "2026-10-06",
            "room_type_id": 438550,
            "board_type_id": 1,
            "total_price_eur": "1330",
            "currency_display": "EUR",
        },
        "pms_reservation_id": "91604489",
        "voucher_no": "",
        "reservation_no": "VLX-21966-2604-0013",
        "manual_review_reason": None,
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None,
        "created_at": datetime(2026, 4, 19, 12, 0, tzinfo=UTC),
    }
    pool = _ConversationDetailPool(hold_row=hold_row, msg_rows=[])

    async def _fake_find_reservation_list_match(
        hotel_id: int,
        *,
        reservation_id: str | None = None,
        voucher_no: str | None = None,
        contact_phone: str | None = None,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ):
        assert hotel_id == 21966
        assert reservation_id == "91604489"
        assert voucher_no == "VLX-21966-2604-0013"
        return None

    monkeypatch.setattr(test_chat, "find_reservation_list_match", _fake_find_reservation_list_match)

    response = await test_chat.get_conversation_detail(_request(pool), str(pool.conversation_id))

    guest_info = response["guest_info"]
    assert guest_info["available"] is False
    assert "bulunamadi" in guest_info["info_status_label"].lower()
    assert guest_info["hold_status_label"] == "PMS Rezervasyonu Pasif"
    assert guest_info["reservation_reference"] is None
