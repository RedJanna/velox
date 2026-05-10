"""Operations Desk response review service."""

from __future__ import annotations

from datetime import UTC
from typing import Any
from uuid import UUID

import asyncpg
import orjson
import structlog

from velox.core.chat_lab_feedback import ChatLabFeedbackService
from velox.models.chat_lab_feedback import ChatLabFeedbackRequest
from velox.models.response_review import (
    ResponseReviewClassification,
    ResponseReviewClassifyRequest,
    ResponseReviewCreateRequest,
    ResponseReviewDetail,
    ResponseReviewErrorType,
    ResponseReviewListItem,
    ResponseReviewListResponse,
    ResponseReviewStatus,
)

logger = structlog.get_logger(__name__)

_REPORTABLE_ROLES = {"assistant", "operator", "system"}
_CONTEXT_WINDOW = 4
_ERROR_TYPE_TO_FEEDBACK_CATEGORY = {
    ResponseReviewErrorType.WRONG_INFO: "yanlis_bilgi",
    ResponseReviewErrorType.MISSING_INFO: "eksik_bilgi",
    ResponseReviewErrorType.WRONG_INTENT: "intent_iskalama",
    ResponseReviewErrorType.SOURCE_MISMATCH: "mantik_celiskisi",
    ResponseReviewErrorType.UNSUPPORTED_CLAIM: "uydurma_bilgi",
    ResponseReviewErrorType.POLICY_RISK: "ton_politika_ihlali",
    ResponseReviewErrorType.PII_RISK: "ton_politika_ihlali",
    ResponseReviewErrorType.TONE_OR_LENGTH: "gevezelik",
    ResponseReviewErrorType.LANGUAGE_ISSUE: "format_ihlali",
    ResponseReviewErrorType.TOOL_MISMATCH: "mantik_celiskisi",
    ResponseReviewErrorType.HANDOFF_REQUIRED: "ton_politika_ihlali",
    ResponseReviewErrorType.DELIVERY_STATUS_ISSUE: "format_ihlali",
    ResponseReviewErrorType.OTHER: "ozel_kategori",
    ResponseReviewErrorType.NOT_CLASSIFIED: "ozel_kategori",
}


def _json_dumps(payload: Any) -> str:
    return orjson.dumps(payload).decode()


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = orjson.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except orjson.JSONDecodeError:
            return {}
    return {}


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = orjson.loads(value)
            return parsed if isinstance(parsed, list) else []
        except orjson.JSONDecodeError:
            return []
    return []


def _iso(value: Any) -> str:
    if value is None:
        return ""
    return value.astimezone(UTC).isoformat() if hasattr(value, "astimezone") else str(value)


def _to_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} geçerli bir UUID değil.") from exc


def _safe_internal_summary(value: Any) -> dict[str, Any]:
    internal = _json_object(value)
    allowed_keys = {
        "intent",
        "state",
        "risk_flags",
        "source",
        "source_name",
        "knowledge_source",
        "tool_name",
        "provider_status",
        "delivery_status",
        "approval_pending",
        "send_blocked",
        "model",
        "missing_fields",
        "missing_info",
    }
    return {key: internal[key] for key in allowed_keys if key in internal}


def _message_context_item(row: asyncpg.Record) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "role": str(row["role"]),
        "content": str(row["content"] or ""),
        "created_at": _iso(row["created_at"]),
        "internal_summary": _safe_internal_summary(row.get("internal_json")),
    }


def _row_to_list_item(row: asyncpg.Record) -> ResponseReviewListItem:
    return ResponseReviewListItem(
        id=str(row["id"]),
        hotel_id=int(row["hotel_id"]),
        conversation_id=str(row["conversation_id"]),
        message_id=str(row["message_id"]),
        message_role=str(row["message_role"]),
        message_content=str(row["message_content"]),
        report_reason=str(row["report_reason"] or ""),
        error_type=ResponseReviewErrorType(str(row["error_type"])),
        status=ResponseReviewStatus(str(row["status"])),
        classification=ResponseReviewClassification(str(row["classification"])),
        reported_by_username=str(row["reported_by_username"] or ""),
        reported_by_display_name=str(row["reported_by_display_name"]) if row.get("reported_by_display_name") else None,
        reported_at=_iso(row["reported_at"]),
        reviewed_at=_iso(row["reviewed_at"]) if row.get("reviewed_at") else None,
        rating=int(row["rating"]) if row.get("rating") is not None else None,
        included_in_report=bool(row["included_in_report"]),
        feedback_id=str(row["feedback_id"]) if row.get("feedback_id") else None,
    )


def _row_to_detail(row: asyncpg.Record, actions: list[dict[str, Any]]) -> ResponseReviewDetail:
    base = _row_to_list_item(row)
    return ResponseReviewDetail(
        **base.model_dump(),
        message_created_at=_iso(row["message_created_at"]),
        conversation_snapshot=_json_object(row.get("conversation_snapshot_json")),
        context_messages=[
            item for item in _json_list(row.get("context_messages_json")) if isinstance(item, dict)
        ],
        reviewed_by_username=str(row["reviewed_by_username"]) if row.get("reviewed_by_username") else None,
        notes=str(row["notes"]) if row.get("notes") else None,
        gold_standard=str(row["gold_standard"]) if row.get("gold_standard") else None,
        feedback_storage_group=str(row["feedback_storage_group"]) if row.get("feedback_storage_group") else None,
        feedback_storage_path=str(row["feedback_storage_path"]) if row.get("feedback_storage_path") else None,
        actions=actions,
    )


class ResponseReviewService:
    """Create, list, classify, and export reported response reviews."""

    def __init__(
        self,
        pool: asyncpg.Pool,
        feedback_service: ChatLabFeedbackService | None = None,
    ) -> None:
        self._pool = pool
        self._feedback_service = feedback_service or ChatLabFeedbackService()

    async def create_review(
        self,
        payload: ResponseReviewCreateRequest,
        *,
        hotel_id: int,
        reporter_user_id: int,
        reporter_username: str,
        reporter_display_name: str | None,
    ) -> ResponseReviewDetail:
        """Create or reuse an open review for one selected conversation message."""
        conversation_id = _to_uuid(payload.conversation_id, "conversation_id")
        message_id = _to_uuid(payload.message_id, "message_id")
        async with self._pool.acquire() as conn, conn.transaction():
            source = await conn.fetchrow(
                """
                SELECT
                    c.id AS conversation_id,
                    c.hotel_id,
                    c.phone_display,
                    c.language,
                    c.current_state,
                    c.current_intent,
                    c.risk_flags,
                    c.human_override,
                    c.is_active,
                    c.last_message_at,
                    m.id AS message_id,
                    m.role AS message_role,
                    m.content AS message_content,
                    m.created_at AS message_created_at
                FROM conversations c
                JOIN messages m ON m.conversation_id = c.id
                WHERE c.id = $1
                  AND m.id = $2
                  AND c.hotel_id = $3
                """,
                conversation_id,
                message_id,
                hotel_id,
            )
            if source is None:
                raise LookupError("Raporlanacak mesaj bulunamadı.")

            message_role = str(source["message_role"]).lower()
            if message_role not in _REPORTABLE_ROLES:
                raise ValueError("Yalnızca AI, operatör veya sistem yanıtları raporlanabilir.")

            existing = await conn.fetchrow(
                """
                SELECT *
                FROM response_reviews
                WHERE hotel_id = $1
                  AND message_id = $2
                  AND reported_by_user_id = $3
                  AND status IN ('open', 'in_review')
                ORDER BY reported_at DESC
                LIMIT 1
                """,
                hotel_id,
                message_id,
                reporter_user_id,
            )
            if existing is not None:
                return await self._detail_from_row(conn, existing)

            context_rows = await conn.fetch(
                """
                SELECT id, role, content, internal_json, created_at
                FROM (
                    SELECT id, role, content, internal_json, created_at
                    FROM messages
                    WHERE conversation_id = $1
                      AND created_at <= $2
                    ORDER BY created_at DESC
                    LIMIT $3
                ) recent
                ORDER BY created_at ASC
                """,
                conversation_id,
                source["message_created_at"],
                (_CONTEXT_WINDOW * 2) + 1,
            )
            snapshot = {
                "conversation_id": str(source["conversation_id"]),
                "hotel_id": int(source["hotel_id"]),
                "phone_display": source["phone_display"],
                "language": source["language"],
                "current_state": source["current_state"],
                "current_intent": source["current_intent"],
                "risk_flags": list(source["risk_flags"] or []),
                "human_override": bool(source["human_override"]),
                "is_active": bool(source["is_active"]),
                "last_message_at": _iso(source["last_message_at"]),
            }
            context_messages = [_message_context_item(row) for row in context_rows]
            row = await conn.fetchrow(
                """
                INSERT INTO response_reviews (
                    hotel_id,
                    conversation_id,
                    message_id,
                    message_role,
                    message_content,
                    message_created_at,
                    conversation_snapshot_json,
                    context_messages_json,
                    report_reason,
                    error_type,
                    status,
                    classification,
                    reported_by_user_id,
                    reported_by_username,
                    reported_by_display_name
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7::jsonb, $8::jsonb, $9, $10,
                    'open', 'needs_review', $11, $12, $13
                )
                RETURNING *
                """,
                hotel_id,
                conversation_id,
                message_id,
                message_role,
                str(source["message_content"] or ""),
                source["message_created_at"],
                _json_dumps(snapshot),
                _json_dumps(context_messages),
                (payload.reason or "").strip(),
                payload.error_type.value,
                reporter_user_id,
                reporter_username,
                reporter_display_name,
            )
            if row is None:
                raise RuntimeError("Rapor kaydı oluşturulamadı.")
            await self._insert_action(
                conn,
                review_id=UUID(str(row["id"])),
                actor_user_id=reporter_user_id,
                actor_username=reporter_username,
                action_type="reported",
                from_status=None,
                to_status="open",
                notes=(payload.reason or "").strip() or None,
                metadata={"error_type": payload.error_type.value},
            )
            logger.info(
                "response_review_created",
                hotel_id=hotel_id,
                conversation_id=str(conversation_id),
                message_id=str(message_id),
                review_id=str(row["id"]),
            )
            return await self._detail_from_row(conn, row)

    async def list_reviews(
        self,
        *,
        hotel_id: int,
        status_filter: ResponseReviewStatus | None = None,
        classification: ResponseReviewClassification | None = None,
        error_type: ResponseReviewErrorType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ResponseReviewListResponse:
        """List response reviews for one hotel scope."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *
                FROM response_reviews
                WHERE hotel_id = $1
                  AND ($2::text IS NULL OR status = $2)
                  AND ($3::text IS NULL OR classification = $3)
                  AND ($4::text IS NULL OR error_type = $4)
                ORDER BY reported_at DESC
                LIMIT $5 OFFSET $6
                """,
                hotel_id,
                status_filter.value if status_filter else None,
                classification.value if classification else None,
                error_type.value if error_type else None,
                limit,
                offset,
            )
            total = int(
                await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM response_reviews
                    WHERE hotel_id = $1
                      AND ($2::text IS NULL OR status = $2)
                      AND ($3::text IS NULL OR classification = $3)
                      AND ($4::text IS NULL OR error_type = $4)
                    """,
                    hotel_id,
                    status_filter.value if status_filter else None,
                    classification.value if classification else None,
                    error_type.value if error_type else None,
                )
                or 0
            )
        return ResponseReviewListResponse(
            items=[_row_to_list_item(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_review(self, *, review_id: UUID, hotel_id: int) -> ResponseReviewDetail | None:
        """Return one response review detail."""
        async with self._pool.acquire() as conn:
            row = await self._get_row(conn, review_id=review_id, hotel_id=hotel_id)
            if row is None:
                return None
            return await self._detail_from_row(conn, row)

    async def classify_review(
        self,
        review_id: UUID,
        payload: ResponseReviewClassifyRequest,
        *,
        hotel_id: int,
        reviewer_user_id: int,
        reviewer_username: str,
    ) -> ResponseReviewDetail:
        """Classify a review and export it into the Chat Lab feedback structure."""
        async with self._pool.acquire() as conn, conn.transaction():
            row = await self._get_row(conn, review_id=review_id, hotel_id=hotel_id, for_update=True)
            if row is None:
                raise LookupError("Rapor kaydı bulunamadı.")
            previous_status = str(row["status"])
            next_status = "finalized" if payload.finalize else "in_review"
            feedback_result = None
            if payload.finalize:
                feedback_result = await self._export_feedback(row, payload, reviewer_username)

            updated = await conn.fetchrow(
                """
                UPDATE response_reviews
                SET status = $3,
                    classification = $4,
                    error_type = $5,
                    reviewed_by_user_id = $6,
                    reviewed_by_username = $7,
                    reviewed_at = now(),
                    notes = $8,
                    gold_standard = $9,
                    rating = $10,
                    included_in_report = $11,
                    feedback_id = COALESCE($12, feedback_id),
                    feedback_storage_group = COALESCE($13, feedback_storage_group),
                    feedback_storage_path = COALESCE($14, feedback_storage_path),
                    updated_at = now()
                WHERE id = $1
                  AND hotel_id = $2
                RETURNING *
                """,
                review_id,
                hotel_id,
                next_status,
                payload.classification.value,
                payload.error_type.value,
                reviewer_user_id,
                reviewer_username,
                payload.notes,
                payload.gold_standard,
                payload.rating,
                payload.included_in_report,
                feedback_result.feedback_id if feedback_result else None,
                feedback_result.storage_group if feedback_result else None,
                feedback_result.storage_path if feedback_result else None,
            )
            if updated is None:
                raise RuntimeError("Rapor kaydı güncellenemedi.")
            await self._insert_action(
                conn,
                review_id=review_id,
                actor_user_id=reviewer_user_id,
                actor_username=reviewer_username,
                action_type="classified",
                from_status=previous_status,
                to_status=next_status,
                notes=payload.notes,
                metadata={
                    "classification": payload.classification.value,
                    "error_type": payload.error_type.value,
                    "rating": payload.rating,
                    "feedback_id": feedback_result.feedback_id if feedback_result else None,
                },
            )
            logger.info(
                "response_review_classified",
                hotel_id=hotel_id,
                review_id=str(review_id),
                classification=payload.classification.value,
                error_type=payload.error_type.value,
            )
            return await self._detail_from_row(conn, updated)

    async def _export_feedback(
        self,
        row: asyncpg.Record,
        payload: ResponseReviewClassifyRequest,
        reviewer_username: str,
    ):
        category = _ERROR_TYPE_TO_FEEDBACK_CATEGORY.get(payload.error_type, "ozel_kategori")
        tags = [tag.strip().lower() for tag in payload.tags if tag.strip()]
        if payload.error_type.value not in tags and payload.error_type != ResponseReviewErrorType.NOT_CLASSIFIED:
            tags.append(payload.error_type.value)
        return await self._feedback_service.submit_feedback(
            ChatLabFeedbackRequest(
                source_type="live_conversation",
                conversation_id=str(row["conversation_id"]),
                assistant_message_id=str(row["message_id"]),
                rating=payload.rating or 5,
                category=None if payload.classification == ResponseReviewClassification.CORRECT else category,
                tags=[] if payload.classification == ResponseReviewClassification.CORRECT else tags[:8],
                gold_standard=payload.gold_standard,
                notes=payload.notes,
                approved_example=payload.classification == ResponseReviewClassification.CORRECT,
                source_flow="response_review",
                report_id=str(row["id"]),
                report_reason=str(row["report_reason"] or ""),
                reporter_username=str(row["reported_by_username"] or ""),
                reviewer_username=reviewer_username,
                review_classification=payload.classification.value,
                included_in_report=payload.included_in_report,
                redact_for_review=True,
            )
        )

    async def _get_row(
        self,
        conn: asyncpg.Connection,
        *,
        review_id: UUID,
        hotel_id: int,
        for_update: bool = False,
    ) -> asyncpg.Record | None:
        query = (
            """
            SELECT *
            FROM response_reviews
            WHERE id = $1
              AND hotel_id = $2
            FOR UPDATE
            """
            if for_update
            else """
            SELECT *
            FROM response_reviews
            WHERE id = $1
              AND hotel_id = $2
            """
        )
        return await conn.fetchrow(
            query,
            review_id,
            hotel_id,
        )

    async def _detail_from_row(self, conn: asyncpg.Connection, row: asyncpg.Record) -> ResponseReviewDetail:
        actions = await conn.fetch(
            """
            SELECT action_type, actor_username, from_status, to_status, notes, metadata_json, created_at
            FROM response_review_actions
            WHERE review_id = $1
            ORDER BY created_at DESC
            """,
            row["id"],
        )
        action_items = [
            {
                "action_type": str(action["action_type"]),
                "actor_username": str(action["actor_username"] or ""),
                "from_status": str(action["from_status"]) if action.get("from_status") else None,
                "to_status": str(action["to_status"]) if action.get("to_status") else None,
                "notes": str(action["notes"]) if action.get("notes") else None,
                "metadata": _json_object(action.get("metadata_json")),
                "created_at": _iso(action["created_at"]),
            }
            for action in actions
        ]
        return _row_to_detail(row, action_items)

    async def _insert_action(
        self,
        conn: asyncpg.Connection,
        *,
        review_id: UUID,
        actor_user_id: int,
        actor_username: str,
        action_type: str,
        from_status: str | None,
        to_status: str | None,
        notes: str | None,
        metadata: dict[str, Any],
    ) -> None:
        await conn.execute(
            """
            INSERT INTO response_review_actions (
                review_id,
                actor_user_id,
                actor_username,
                action_type,
                from_status,
                to_status,
                notes,
                metadata_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
            """,
            review_id,
            actor_user_id,
            actor_username,
            action_type,
            from_status,
            to_status,
            notes,
            _json_dumps(metadata),
        )
