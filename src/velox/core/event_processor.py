"""Webhook event processor for approval, payment, and transfer updates."""

import asyncio
from datetime import date, timedelta
from time import perf_counter
from typing import Any
from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.adapters.whatsapp.client import get_whatsapp_client
from velox.config.constants import MAX_TOOL_RETRIES, TOOL_RETRY_BACKOFF_SECONDS, HoldStatus
from velox.core.hold_workflow import HoldWorkflowEvent, HoldWorkflowState, apply_hold_transition
from velox.core.idempotency import (
    IDEMPOTENCY_NAMESPACE_APPROVAL,
    IDEMPOTENCY_NAMESPACE_CREATE,
    IdempotencyInput,
    build_idempotency_key,
)
from velox.core.reconciliation import (
    ReconciliationAction,
    ReconciliationInput,
    decide_reconciliation_action,
)
from velox.db.repositories.conversation import ConversationRepository
from velox.models.conversation import Message
from velox.models.webhook_events import ApprovalEvent, PaymentEvent, TransferEvent

logger = structlog.get_logger(__name__)

DB_TIMEOUT_SECONDS = 5
EXTERNAL_TIMEOUT_SECONDS = 10


def _mask_phone(phone: str) -> str:
    """Mask phone for logs."""
    if len(phone) < 4:
        return "***"
    return f"{phone[:3]}***{phone[-2:]}"


class EventProcessor:
    """Process admin webhook events and continue related conversation flow."""

    def __init__(self, db_pool: asyncpg.Pool, dispatcher: Any) -> None:
        self._db_pool = db_pool
        self._dispatcher = dispatcher
        self._conversation_repository = ConversationRepository()

    async def process_approval_event(self, event: ApprovalEvent) -> dict[str, Any]:
        """Process approval webhook and execute post-approval actions."""
        async with self._db_pool.acquire() as conn:
            approval_row = await conn.fetchrow(
                """
                SELECT request_id, hotel_id, approval_type, reference_id
                FROM approval_requests
                WHERE request_id = $1 AND hotel_id = $2
                """,
                event.approval_request_id,
                event.hotel_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if approval_row is None:
                raise ValueError("approval_request_not_found")

            approval_type = str(approval_row["approval_type"])
            reference_id = str(approval_row["reference_id"])

            hold = await self._load_hold(conn, approval_type, reference_id, event.hotel_id)
            if hold is None:
                raise ValueError("referenced_hold_not_found")

            new_status = "APPROVED" if event.approved else "REJECTED"
            await conn.execute(
                """
                UPDATE approval_requests
                SET status = $2, decided_by_role = $3, decided_by_name = $4, decided_at = $5
                WHERE request_id = $1
                """,
                event.approval_request_id,
                new_status,
                event.approved_by_role,
                "admin_webhook",
                event.timestamp,
                timeout=DB_TIMEOUT_SECONDS,
            )

            conversation_id = hold["conversation_id"]
            phone = self._extract_phone(approval_type, hold)
            user_message = ""
            tool_results: dict[str, Any] = {}

            if not event.approved:
                await self._update_hold_status(conn, approval_type, reference_id, status="REJECTED")
                await self._upsert_stay_workflow_metadata(
                    conn,
                    reference_id=reference_id,
                    workflow_state=HoldWorkflowState.rejected.value,
                )
                user_message = (
                    "Talebiniz su an onaylanamadi. Ekibimiz alternatifler icin size yardimci olacaktir."
                )
            elif approval_type == "STAY":
                approval_idempotency_key = build_idempotency_key(
                    IdempotencyInput(
                        namespace=IDEMPOTENCY_NAMESPACE_APPROVAL,
                        reference_id=reference_id,
                        hotel_id=event.hotel_id,
                    )
                )
                create_idempotency_key = build_idempotency_key(
                    IdempotencyInput(
                        namespace=IDEMPOTENCY_NAMESPACE_CREATE,
                        reference_id=reference_id,
                        hotel_id=event.hotel_id,
                    )
                )
                if self._is_duplicate_stay_approval(hold, approval_idempotency_key):
                    logger.info(
                        "approval_event_duplicate_ignored",
                        approval_request_id=event.approval_request_id,
                        hotel_id=event.hotel_id,
                        reference_id=reference_id,
                    )
                    return {
                        "approval_request_id": event.approval_request_id,
                        "status": "processed",
                        "approved": event.approved,
                        "duplicate": True,
                    }

                pms_pending_transition = apply_hold_transition(
                    current_state=HoldWorkflowState.pending_approval,
                    event=HoldWorkflowEvent.admin_approved,
                )
                await self._update_hold_status(
                    conn,
                    approval_type,
                    reference_id,
                    status=pms_pending_transition.to_state.value,
                    approved_by=event.approved_by_role,
                    approved_at=event.timestamp,
                )
                await self._upsert_stay_workflow_metadata(
                    conn,
                    reference_id=reference_id,
                    workflow_state=pms_pending_transition.to_state.value,
                    approval_idempotency_key=approval_idempotency_key,
                    create_idempotency_key=create_idempotency_key,
                    pms_create_started=True,
                )

                draft = self._extract_stay_draft(hold)
                try:
                    booking_result = await self._dispatch_with_retry(
                        "booking_create_reservation",
                        hotel_id=event.hotel_id,
                        draft=draft,
                        approval_context="ADMIN_APPROVED",
                        admin_approved=True,
                    )
                except Exception as exc:
                    is_timeout = isinstance(exc, TimeoutError | asyncio.TimeoutError)
                    reconciliation_action = decide_reconciliation_action(
                        ReconciliationInput(
                            create_http_timeout=is_timeout,
                            create_response_success=False,
                            reservation_found_by_id=False,
                            reservation_found_by_voucher=False,
                            readback_attempts_exhausted=True,
                        )
                    )
                    failed_state = (
                        HoldStatus.MANUAL_REVIEW.value
                        if reconciliation_action == ReconciliationAction.MANUAL_REVIEW
                        else HoldStatus.PMS_FAILED.value
                    )
                    await self._update_hold_status(conn, approval_type, reference_id, status=failed_state)
                    await self._upsert_stay_workflow_metadata(
                        conn,
                        reference_id=reference_id,
                        workflow_state=failed_state,
                        manual_review_reason=(
                            f"create_failed:{type(exc).__name__}:{reconciliation_action.value}"
                        ),
                        pms_create_completed=True,
                    )
                    tool_results["booking_create_reservation"] = {
                        "success": False,
                        "error_type": type(exc).__name__,
                        "reconciliation_action": reconciliation_action.value,
                    }
                    user_message = (
                        "Talebiniz alindi ancak rezervasyon onayinda teknik bir dogrulama gerekiyor. "
                        "Ekibimiz en kisa surede sizinle iletisime gececektir."
                    )
                    await self.inject_system_event(
                        conversation_id,
                        {
                            "event_type": "approval.updated",
                            "approval_request_id": event.approval_request_id,
                            "approval_type": approval_type,
                            "approved": event.approved,
                            "reference_id": reference_id,
                            "tool_results": tool_results,
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )
                    await self._append_assistant_message(conversation_id, user_message)
                    await self._send_user_message(phone, user_message)
                    return {
                        "approval_request_id": event.approval_request_id,
                        "status": "processed",
                        "approved": event.approved,
                        "reconciliation_action": reconciliation_action.value,
                    }

                tool_results["booking_create_reservation"] = booking_result
                reservation_id = str(booking_result.get("reservation_id", "")).strip()
                voucher_no = str(booking_result.get("voucher_no", "")).strip() or None

                # Create response without reservation identifiers is considered uncertain and blocked.
                if not reservation_id and not voucher_no:
                    reconciliation_action = ReconciliationAction.MANUAL_REVIEW
                    failed_state = HoldStatus.MANUAL_REVIEW.value
                    await self._update_hold_status(conn, approval_type, reference_id, status=failed_state)
                    await self._upsert_stay_workflow_metadata(
                        conn,
                        reference_id=reference_id,
                        workflow_state=failed_state,
                        manual_review_reason="create_missing_identifiers",
                        pms_create_completed=True,
                    )
                    tool_results["booking_get_reservation"] = {
                        "success": False,
                        "error_type": "MissingReservationIdentifiers",
                    }
                    user_message = (
                        "Talebiniz alindi ancak rezervasyon dogrulama adiminda teknik kontrol gerekiyor. "
                        "Ekibimiz en kisa surede sizinle iletisime gececektir."
                    )
                    await self.inject_system_event(
                        conversation_id,
                        {
                            "event_type": "approval.updated",
                            "approval_request_id": event.approval_request_id,
                            "approval_type": approval_type,
                            "approved": event.approved,
                            "reference_id": reference_id,
                            "tool_results": tool_results,
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )
                    await self._append_assistant_message(conversation_id, user_message)
                    await self._send_user_message(phone, user_message)
                    return {
                        "approval_request_id": event.approval_request_id,
                        "status": "processed",
                        "approved": event.approved,
                        "reconciliation_action": reconciliation_action.value,
                    }

                readback_result: dict[str, Any] | None = None
                try:
                    readback_result = await self._fetch_reservation_readback(
                        hotel_id=event.hotel_id,
                        reservation_id=reservation_id or None,
                        voucher_no=voucher_no,
                    )
                    tool_results["booking_get_reservation"] = {"success": True, "result": readback_result}
                except Exception as exc:
                    readback_result = None
                    tool_results["booking_get_reservation"] = {
                        "success": False,
                        "error_type": type(exc).__name__,
                    }
                    logger.warning(
                        "reservation_readback_failed",
                        hold_id=reference_id,
                        error_type=type(exc).__name__,
                    )

                reservation_found_by_id = False
                reservation_found_by_voucher = False
                if isinstance(readback_result, dict):
                    readback_reservation_id = str(readback_result.get("reservation_id", "")).strip()
                    readback_voucher = str(readback_result.get("voucher_no", "")).strip()
                    reservation_found_by_id = bool(reservation_id and readback_reservation_id)
                    reservation_found_by_voucher = bool(voucher_no and readback_voucher)

                if not (reservation_found_by_id or reservation_found_by_voucher):
                    reconciliation_action = ReconciliationAction.MANUAL_REVIEW
                    failed_state = HoldStatus.MANUAL_REVIEW.value
                    await self._update_hold_status(conn, approval_type, reference_id, status=failed_state)
                    await self._upsert_stay_workflow_metadata(
                        conn,
                        reference_id=reference_id,
                        workflow_state=failed_state,
                        manual_review_reason="create_unverified_after_readback",
                        pms_create_completed=True,
                    )
                    user_message = (
                        "Talebiniz alindi ancak rezervasyon dogrulama adiminda teknik kontrol gerekiyor. "
                        "Ekibimiz en kisa surede sizinle iletisime gececektir."
                    )
                    await self.inject_system_event(
                        conversation_id,
                        {
                            "event_type": "approval.updated",
                            "approval_request_id": event.approval_request_id,
                            "approval_type": approval_type,
                            "approved": event.approved,
                            "reference_id": reference_id,
                            "tool_results": tool_results,
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )
                    await self._append_assistant_message(conversation_id, user_message)
                    await self._send_user_message(phone, user_message)
                    return {
                        "approval_request_id": event.approval_request_id,
                        "status": "processed",
                        "approved": event.approved,
                        "reconciliation_action": reconciliation_action.value,
                    }

                pms_created_transition = apply_hold_transition(
                    current_state=pms_pending_transition.to_state,
                    event=HoldWorkflowEvent.pms_create_succeeded,
                )
                await self._update_hold_status(
                    conn,
                    approval_type,
                    reference_id,
                    status=pms_created_transition.to_state.value,
                )
                await self._upsert_stay_workflow_metadata(
                    conn,
                    reference_id=reference_id,
                    workflow_state=pms_created_transition.to_state.value,
                    pms_create_completed=True,
                )

                if reservation_id:
                    await conn.execute(
                        """
                        UPDATE stay_holds
                        SET pms_reservation_id = $2, voucher_no = $3, updated_at = now()
                        WHERE hold_id = $1
                        """,
                        reference_id,
                        reservation_id,
                        voucher_no,
                        timeout=DB_TIMEOUT_SECONDS,
                    )

                cancel_policy = str(draft.get("cancel_policy_type", "FREE_CANCEL")).upper()
                due_mode = "NOW" if cancel_policy == "NON_REFUNDABLE" else "SCHEDULED"
                scheduled_date = self._resolve_scheduled_date(draft, due_mode)

                payment_payload: dict[str, Any] = {
                    "hotel_id": event.hotel_id,
                    "reference_id": reservation_id or reference_id,
                    "amount": float(draft.get("total_price_eur", 0.0)),
                    "currency": str(draft.get("currency_display", "EUR")),
                    "methods": ["BANK_TRANSFER", "PAYMENT_LINK", "MAIL_ORDER"],
                    "due_mode": due_mode,
                    "cancel_policy_type": cancel_policy,
                }
                if scheduled_date is not None:
                    payment_payload["scheduled_date"] = scheduled_date

                payment_result = await self._dispatch_with_retry(
                    "payment_request_prepayment",
                    **payment_payload,
                )
                tool_results["payment_request_prepayment"] = payment_result
                payment_pending_transition = apply_hold_transition(
                    current_state=pms_created_transition.to_state,
                    event=HoldWorkflowEvent.payment_requested,
                )
                await self._update_hold_status(
                    conn,
                    approval_type,
                    reference_id,
                    status=payment_pending_transition.to_state.value,
                )
                await self._upsert_stay_workflow_metadata(
                    conn,
                    reference_id=reference_id,
                    workflow_state=payment_pending_transition.to_state.value,
                )

                if due_mode == "NOW":
                    user_message = (
                        "Rezervasyonunuz onaylandi. On odeme sureci icin satis ekibimiz en kisa surede "
                        "sizinle iletisime gececektir."
                    )
                else:
                    user_message = (
                        "Rezervasyonunuz onaylandi. Check-in tarihinizden 7 gun once satis ekibimiz odeme "
                        "detaylari icin sizinle iletisime gececektir."
                    )
            elif approval_type == "RESTAURANT":
                await self._update_hold_status(
                    conn,
                    approval_type,
                    reference_id,
                    status="CONFIRMED",
                    approved_by=event.approved_by_role,
                    approved_at=event.timestamp,
                )
                user_message = "Restoran rezervasyonunuz onaylandi ve kesinlestirildi."
            elif approval_type == "TRANSFER":
                await self._update_hold_status(
                    conn,
                    approval_type,
                    reference_id,
                    status="CONFIRMED",
                    approved_by=event.approved_by_role,
                    approved_at=event.timestamp,
                )
                user_message = "Transfer talebiniz onaylandi ve kesinlestirildi."
            else:
                user_message = "Talebiniz guncellendi. Ekibimiz en kisa surede sizi bilgilendirecektir."

            await self.inject_system_event(
                conversation_id,
                {
                    "event_type": "approval.updated",
                    "approval_request_id": event.approval_request_id,
                    "approval_type": approval_type,
                    "approved": event.approved,
                    "reference_id": reference_id,
                    "tool_results": tool_results,
                    "timestamp": event.timestamp.isoformat(),
                },
            )
            await self._append_assistant_message(conversation_id, user_message)
            await self._send_user_message(phone, user_message)

        return {
            "approval_request_id": event.approval_request_id,
            "status": "processed",
            "approved": event.approved,
        }

    async def process_payment_event(self, event: PaymentEvent) -> dict[str, Any]:
        """Process payment status webhook and update related hold/reservation state."""
        normalized_status = event.status.upper()
        if normalized_status not in {"PAID", "FAILED", "EXPIRED"}:
            raise ValueError("invalid_payment_status")

        async with self._db_pool.acquire() as conn:
            payment_row = await conn.fetchrow(
                """
                SELECT request_id, hotel_id, reference_id
                FROM payment_requests
                WHERE request_id = $1 AND hotel_id = $2
                """,
                event.payment_request_id,
                event.hotel_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if payment_row is None:
                raise ValueError("payment_request_not_found")

            await conn.execute(
                """
                UPDATE payment_requests
                SET status = $2, paid_at = CASE WHEN $2 = 'PAID' THEN $3 ELSE paid_at END
                WHERE request_id = $1
                """,
                event.payment_request_id,
                normalized_status,
                event.timestamp,
                timeout=DB_TIMEOUT_SECONDS,
            )

            reference_id = str(payment_row["reference_id"])
            hold = await conn.fetchrow(
                """
                SELECT * FROM stay_holds
                WHERE hotel_id = $1 AND (pms_reservation_id = $2 OR hold_id = $2)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                event.hotel_id,
                reference_id,
                timeout=DB_TIMEOUT_SECONDS,
            )

            conversation_id = hold["conversation_id"] if hold else None
            phone = self._extract_phone("STAY", hold) if hold else ""
            if normalized_status == "PAID":
                if hold is not None:
                    await conn.execute(
                        """
                        UPDATE stay_holds
                        SET status = 'CONFIRMED', updated_at = now()
                        WHERE hold_id = $1
                        """,
                        hold["hold_id"],
                        timeout=DB_TIMEOUT_SECONDS,
                    )
                user_message = "Odemeniz basariyla alindi. Rezervasyonunuz kesinlesti."
            elif normalized_status == "FAILED":
                user_message = (
                    "Odeme islemi basarisiz oldu. Alternatif odeme yontemleri icin satis ekibimiz size "
                    "yardimci olacaktir."
                )
            else:
                if hold is not None:
                    await conn.execute(
                        """
                        UPDATE stay_holds
                        SET status = 'PAYMENT_EXPIRED', updated_at = now()
                        WHERE hold_id = $1
                        """,
                        hold["hold_id"],
                        timeout=DB_TIMEOUT_SECONDS,
                    )
                user_message = (
                    "Odeme suresi doldu. Devam etmek isterseniz satis ekibimiz odeme adimlarinda size "
                    "yardimci olacaktir."
                )

            if conversation_id is not None:
                await self.inject_system_event(
                    conversation_id,
                    {
                        "event_type": "payment.updated",
                        "payment_request_id": event.payment_request_id,
                        "status": normalized_status,
                        "reference_id": reference_id,
                        "timestamp": event.timestamp.isoformat(),
                    },
                )
                await self._append_assistant_message(conversation_id, user_message)
            await self._send_user_message(phone, user_message)

        return {
            "payment_request_id": event.payment_request_id,
            "status": "processed",
            "payment_status": normalized_status,
        }

    async def process_transfer_event(self, event: TransferEvent) -> dict[str, Any]:
        """Process transfer confirmation/cancel webhook event."""
        normalized_status = event.status.upper()
        if normalized_status not in {"CONFIRMED", "CANCELLED"}:
            raise ValueError("invalid_transfer_status")

        async with self._db_pool.acquire() as conn:
            hold = await conn.fetchrow(
                """
                SELECT * FROM transfer_holds
                WHERE hotel_id = $1 AND hold_id = $2
                """,
                event.hotel_id,
                event.transfer_hold_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
            if hold is None:
                raise ValueError("transfer_hold_not_found")

            await conn.execute(
                """
                UPDATE transfer_holds
                SET status = $2, updated_at = now()
                WHERE hotel_id = $1 AND hold_id = $3
                """,
                event.hotel_id,
                normalized_status,
                event.transfer_hold_id,
                timeout=DB_TIMEOUT_SECONDS,
            )

            message = (
                "Transferiniz onaylandi ve kesinlestirildi."
                if normalized_status == "CONFIRMED"
                else "Transfer talebiniz iptal edildi."
            )
            conversation_id = hold["conversation_id"]
            await self.inject_system_event(
                conversation_id,
                {
                    "event_type": "transfer.updated",
                    "transfer_hold_id": event.transfer_hold_id,
                    "status": normalized_status,
                    "timestamp": event.timestamp.isoformat(),
                },
            )
            await self._append_assistant_message(conversation_id, message)
            await self._send_user_message(self._extract_phone("TRANSFER", hold), message)

        return {
            "transfer_hold_id": event.transfer_hold_id,
            "status": "processed",
            "transfer_status": normalized_status,
        }

    async def inject_system_event(self, conversation_id: UUID | None, event_data: dict[str, Any]) -> None:
        """Inject system event message to conversation history."""
        if conversation_id is None:
            return
        content = f"SYSTEM_EVENT: {orjson.dumps(event_data).decode()}"
        await self._conversation_repository.add_message(
            Message(
                conversation_id=conversation_id,
                role="system",
                content=content,
                internal_json=event_data,
            )
        )

    async def _append_assistant_message(self, conversation_id: UUID | None, content: str) -> None:
        """Store assistant message in conversation history."""
        if conversation_id is None:
            return
        await self._conversation_repository.add_message(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=content,
            )
        )

    async def _send_user_message(self, phone: str, message: str) -> None:
        """Send WhatsApp message to user if a raw phone is available."""
        if not phone or "*" in phone:
            logger.warning("webhook_user_message_skipped_no_phone")
            return

        whatsapp_client = get_whatsapp_client()
        for attempt in range(1, MAX_TOOL_RETRIES + 1):
            started = perf_counter()
            try:
                await asyncio.wait_for(
                    whatsapp_client.send_text_message(to=phone, body=message),
                    timeout=EXTERNAL_TIMEOUT_SECONDS,
                )
                logger.info("webhook_user_message_sent", phone=_mask_phone(phone))
                return
            except Exception:
                duration_ms = int((perf_counter() - started) * 1000)
                logger.exception(
                    "webhook_user_message_failed",
                    phone=_mask_phone(phone),
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                )
                if attempt >= MAX_TOOL_RETRIES:
                    return
                backoff = TOOL_RETRY_BACKOFF_SECONDS[min(attempt - 1, len(TOOL_RETRY_BACKOFF_SECONDS) - 1)]
                await asyncio.sleep(backoff)

    async def _dispatch_with_retry(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """Dispatch tool call with bounded retries and timeout."""
        for attempt in range(1, MAX_TOOL_RETRIES + 1):
            started = perf_counter()
            try:
                result = await asyncio.wait_for(
                    self._dispatcher.dispatch(tool_name, **kwargs),
                    timeout=EXTERNAL_TIMEOUT_SECONDS,
                )
                if isinstance(result, dict):
                    return result
                return {"result": result}
            except Exception as exc:
                duration_ms = int((perf_counter() - started) * 1000)
                logger.warning(
                    "webhook_tool_call_failed",
                    tool_name=tool_name,
                    error_type=type(exc).__name__,
                    attempt_number=attempt,
                    duration_ms=duration_ms,
                )
                if attempt >= MAX_TOOL_RETRIES:
                    raise
                backoff = TOOL_RETRY_BACKOFF_SECONDS[min(attempt - 1, len(TOOL_RETRY_BACKOFF_SECONDS) - 1)]
                await asyncio.sleep(backoff)
        raise RuntimeError("tool_dispatch_retry_exhausted")

    async def _fetch_reservation_readback(
        self,
        *,
        hotel_id: int,
        reservation_id: str | None,
        voucher_no: str | None,
    ) -> dict[str, Any]:
        """Fetch reservation using reservation id and voucher fallback."""
        if reservation_id:
            return await self._dispatch_with_retry(
                "booking_get_reservation",
                hotel_id=hotel_id,
                reservation_id=reservation_id,
            )
        if voucher_no:
            return await self._dispatch_with_retry(
                "booking_get_reservation",
                hotel_id=hotel_id,
                voucher_no=voucher_no,
            )
        raise ValueError("reservation identifiers are required for readback")

    @staticmethod
    async def _load_hold(
        conn: asyncpg.Connection,
        approval_type: str,
        reference_id: str,
        hotel_id: int,
    ) -> asyncpg.Record | None:
        """Load hold row by approval type/reference."""
        if approval_type == "STAY":
            return await conn.fetchrow(
                "SELECT * FROM stay_holds WHERE hotel_id = $1 AND hold_id = $2",
                hotel_id,
                reference_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
        if approval_type == "RESTAURANT":
            return await conn.fetchrow(
                "SELECT * FROM restaurant_holds WHERE hotel_id = $1 AND hold_id = $2",
                hotel_id,
                reference_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
        if approval_type == "TRANSFER":
            return await conn.fetchrow(
                "SELECT * FROM transfer_holds WHERE hotel_id = $1 AND hold_id = $2",
                hotel_id,
                reference_id,
                timeout=DB_TIMEOUT_SECONDS,
            )
        return None

    @staticmethod
    async def _update_hold_status(
        conn: asyncpg.Connection,
        approval_type: str,
        reference_id: str,
        status: str,
        approved_by: str | None = None,
        approved_at: Any | None = None,
    ) -> None:
        """Update hold status for given approval type."""
        if approval_type == "STAY":
            await conn.execute(
                """
                UPDATE stay_holds
                SET status = $2, approved_by = COALESCE($3, approved_by),
                    approved_at = COALESCE($4, approved_at), updated_at = now()
                WHERE hold_id = $1
                """,
                reference_id,
                status,
                approved_by,
                approved_at,
                timeout=DB_TIMEOUT_SECONDS,
            )
            return
        if approval_type == "RESTAURANT":
            await conn.execute(
                """
                UPDATE restaurant_holds
                SET status = $2, approved_by = COALESCE($3, approved_by),
                    approved_at = COALESCE($4, approved_at), updated_at = now()
                WHERE hold_id = $1
                """,
                reference_id,
                status,
                approved_by,
                approved_at,
                timeout=DB_TIMEOUT_SECONDS,
            )
            return
        if approval_type == "TRANSFER":
            await conn.execute(
                """
                UPDATE transfer_holds
                SET status = $2, approved_by = COALESCE($3, approved_by),
                    approved_at = COALESCE($4, approved_at), updated_at = now()
                WHERE hold_id = $1
                """,
                reference_id,
                status,
                approved_by,
                approved_at,
                timeout=DB_TIMEOUT_SECONDS,
            )

    @staticmethod
    def _extract_stay_draft(hold: asyncpg.Record) -> dict[str, Any]:
        """Extract stay draft JSON from hold safely."""
        draft = hold["draft_json"]
        return dict(draft) if isinstance(draft, dict) else {}

    @staticmethod
    def _resolve_scheduled_date(draft: dict[str, Any], due_mode: str) -> str | None:
        """Resolve scheduled payment date using checkin minus seven days."""
        if due_mode != "SCHEDULED":
            return None
        checkin_value = draft.get("checkin_date")
        if not isinstance(checkin_value, str):
            return None
        try:
            checkin_date = date.fromisoformat(checkin_value)
        except ValueError:
            return None
        return (checkin_date - timedelta(days=7)).isoformat()

    @staticmethod
    async def _upsert_stay_workflow_metadata(
        conn: asyncpg.Connection,
        *,
        reference_id: str,
        workflow_state: str | None = None,
        approval_idempotency_key: str | None = None,
        create_idempotency_key: str | None = None,
        manual_review_reason: str | None = None,
        pms_create_started: bool = False,
        pms_create_completed: bool = False,
    ) -> None:
        """Persist stay workflow metadata when workflow columns are available."""
        try:
            if workflow_state is not None:
                await conn.execute(
                    """
                    UPDATE stay_holds
                    SET workflow_state = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    reference_id,
                    workflow_state,
                    timeout=DB_TIMEOUT_SECONDS,
                )
            if approval_idempotency_key is not None:
                await conn.execute(
                    """
                    UPDATE stay_holds
                    SET approval_idempotency_key = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    reference_id,
                    approval_idempotency_key,
                    timeout=DB_TIMEOUT_SECONDS,
                )
            if create_idempotency_key is not None:
                await conn.execute(
                    """
                    UPDATE stay_holds
                    SET create_idempotency_key = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    reference_id,
                    create_idempotency_key,
                    timeout=DB_TIMEOUT_SECONDS,
                )
            if manual_review_reason is not None:
                await conn.execute(
                    """
                    UPDATE stay_holds
                    SET manual_review_reason = $2, updated_at = now()
                    WHERE hold_id = $1
                    """,
                    reference_id,
                    manual_review_reason,
                    timeout=DB_TIMEOUT_SECONDS,
                )
            if pms_create_started:
                await conn.execute(
                    """
                    UPDATE stay_holds
                    SET pms_create_started_at = now(), updated_at = now()
                    WHERE hold_id = $1
                    """,
                    reference_id,
                    timeout=DB_TIMEOUT_SECONDS,
                )
            if pms_create_completed:
                await conn.execute(
                    """
                    UPDATE stay_holds
                    SET pms_create_completed_at = now(), updated_at = now()
                    WHERE hold_id = $1
                    """,
                    reference_id,
                    timeout=DB_TIMEOUT_SECONDS,
                )
        except asyncpg.UndefinedColumnError:
            logger.warning("stay_workflow_columns_missing", hold_id=reference_id)

    @staticmethod
    def _is_duplicate_stay_approval(hold: asyncpg.Record, approval_idempotency_key: str) -> bool:
        """Checks whether stay approval event was already processed."""
        if "approval_idempotency_key" not in hold:
            return False
        existing_key = hold["approval_idempotency_key"]
        if not existing_key:
            return False
        if str(existing_key) != approval_idempotency_key:
            return False

        current_status = str(hold["status"]).upper()
        return current_status in {
            HoldStatus.PMS_PENDING.value,
            HoldStatus.PMS_CREATED.value,
            HoldStatus.PAYMENT_PENDING.value,
            HoldStatus.CONFIRMED.value,
            HoldStatus.MANUAL_REVIEW.value,
        }

    @staticmethod
    def _extract_phone(approval_type: str, hold: asyncpg.Record | None) -> str:
        """Extract raw phone from hold data when available."""
        if hold is None:
            return ""
        if approval_type == "STAY":
            draft = hold["draft_json"]
            if isinstance(draft, dict):
                phone = draft.get("phone")
                return str(phone) if phone else ""
            return ""
        phone = hold.get("phone", None)
        return str(phone) if phone else ""
