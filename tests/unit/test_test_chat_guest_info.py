"""Regression checks for Chat Lab guest info payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from velox.api.routes import test_chat


class _ConversationDetailPool:
    def __init__(self, *, hold_row: dict[str, object] | None) -> None:
        self.conversation_id = uuid4()
        now = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)
        self.conv_row = {
            "id": self.conversation_id,
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
        self.msg_rows = [
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
        if "FROM stay_holds" in query:
            assert args == (self.conversation_id,)
            return self.hold_row
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
