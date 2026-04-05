#!/usr/bin/env python3
"""Replay and analyze structured-output failure turns from the database."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from velox.api.routes.whatsapp_webhook import (  # noqa: E402
    _extract_tool_definition_names,
    _run_message_pipeline,
    _select_tool_definitions_for_turn,
)
from velox.core.structured_output_replay import (  # noqa: E402
    analyze_original_assistant_output,
    build_replay_candidate,
    build_replay_conversation,
    build_replay_summary,
    resolve_replay_time_window,
    sanitize_replay_preview,
)
from velox.db.database import close_db_pool, fetch, init_db_pool  # noqa: E402
from velox.db.repositories.conversation import ConversationRepository  # noqa: E402
from velox.llm.function_registry import get_tool_definitions  # noqa: E402
from velox.llm.prompt_builder import get_prompt_builder  # noqa: E402
from velox.llm.response_parser import ResponseParser  # noqa: E402
from velox.tools import initialize_tool_dispatcher  # noqa: E402
from velox.utils.logger import setup_logging  # noqa: E402


async def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Replay structured-output failure conversations")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of failure turns to inspect")
    parser.add_argument("--conversation-id", type=str, help="Filter to a single conversation UUID")
    parser.add_argument("--assistant-message-id", type=str, help="Filter to a single assistant message UUID")
    parser.add_argument("--reason", type=str, help="Filter parser reason, e.g. missing_internal_json")
    parser.add_argument(
        "--since-hours",
        type=int,
        help="Only include failures from the last N hours. Cannot be combined with --since.",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Only include failures at or after this UTC/ISO-8601 timestamp.",
    )
    parser.add_argument(
        "--until",
        type=str,
        help="Only include failures at or before this UTC/ISO-8601 timestamp.",
    )
    parser.add_argument("--run-llm", action="store_true", help="Replay the selected turns through the current LLM pipeline")
    parser.add_argument(
        "--allow-tools",
        action="store_true",
        help="Allow tool execution during --run-llm replay. Off by default to avoid side effects.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Emit only aggregate summary data and omit per-conversation result rows.",
    )
    parser.add_argument("--output-json", type=Path, help="Write the replay report to a JSON file")
    args = parser.parse_args()

    try:
        since_at, until_at = resolve_replay_time_window(
            since_hours=args.since_hours,
            since=args.since,
            until=args.until,
        )
    except ValueError as exc:
        parser.error(str(exc))

    setup_logging("INFO")
    await init_db_pool()
    try:
        report = await _build_report(
            limit=max(args.limit, 1),
            conversation_id=args.conversation_id,
            assistant_message_id=args.assistant_message_id,
            reason=args.reason,
            since_at=since_at,
            until_at=until_at,
            run_llm=args.run_llm,
            allow_tools=args.allow_tools,
            summary_only=args.summary_only,
        )
    finally:
        await close_db_pool()

    if args.output_json is not None:
        args.output_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


async def _build_report(
    *,
    limit: int,
    conversation_id: str | None,
    assistant_message_id: str | None,
    reason: str | None,
    since_at: datetime | None,
    until_at: datetime | None,
    run_llm: bool,
    allow_tools: bool,
    summary_only: bool,
) -> dict[str, Any]:
    """Build a replay report for matching structured-output failures."""
    prompt_builder = get_prompt_builder()
    tool_definitions = get_tool_definitions()
    dispatcher = initialize_tool_dispatcher() if run_llm and allow_tools else None
    repo = ConversationRepository()

    candidate_rows = await _fetch_failure_rows(
        limit=limit,
        conversation_id=conversation_id,
        assistant_message_id=assistant_message_id,
        reason=reason,
        since_at=since_at,
        until_at=until_at,
    )

    results: list[dict[str, Any]] = []
    for row in candidate_rows:
        conversation = repo._row_to_conversation(row)
        history_rows = await fetch(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = $1
              AND created_at <= $2
            ORDER BY created_at ASC, id ASC
            """,
            conversation.id,
            row["assistant_created_at"],
        )
        history = [repo._row_to_message(message_row) for message_row in history_rows]
        candidate = build_replay_candidate(conversation, history, row["assistant_message_id"])
        if candidate is None:
            continue

        replay_conversation = build_replay_conversation(
            conversation,
            history,
            candidate.trigger_user_message_id,
        )
        selected_tools = _select_tool_definitions_for_turn(
            replay_conversation,
            candidate.trigger_user_text,
            tool_definitions,
        )
        entry: dict[str, Any] = {
            "conversation_id": str(candidate.conversation_id),
            "assistant_message_id": str(candidate.assistant_message_id),
            "assistant_created_at": candidate.assistant_created_at.isoformat(),
            "hotel_id": candidate.hotel_id,
            "language": candidate.language,
            "parser_reason": candidate.parser_reason,
            "trigger_user_message_id": str(candidate.trigger_user_message_id) if candidate.trigger_user_message_id else None,
            "trigger_user_preview": sanitize_replay_preview(candidate.trigger_user_text),
            "original_assistant_preview": sanitize_replay_preview(candidate.assistant_text),
            "history_message_count": len(replay_conversation.messages),
            "system_prompt_length": len(prompt_builder.build_system_prompt(candidate.hotel_id)),
            "tool_count": len(selected_tools),
            "tool_names": _extract_tool_definition_names(selected_tools),
            "current_parser_analysis": analyze_original_assistant_output(candidate.assistant_text),
        }

        if run_llm:
            entry["llm_replay"] = await _run_llm_replay(
                conversation=replay_conversation,
                normalized_text=candidate.trigger_user_text,
                dispatcher=dispatcher,
            )

        results.append(entry)

    return {
        "candidate_count": len(results),
        "filters": {
            "limit": limit,
            "conversation_id": conversation_id,
            "assistant_message_id": assistant_message_id,
            "reason": reason,
            "since_at": since_at.isoformat() if since_at is not None else None,
            "until_at": until_at.isoformat() if until_at is not None else None,
            "run_llm": run_llm,
            "allow_tools": allow_tools,
            "summary_only": summary_only,
        },
        "summary": build_replay_summary(results, run_llm=run_llm),
        "results": [] if summary_only else results,
    }


async def _fetch_failure_rows(
    *,
    limit: int,
    conversation_id: str | None,
    assistant_message_id: str | None,
    reason: str | None,
    since_at: datetime | None,
    until_at: datetime | None,
) -> list[Any]:
    """Fetch assistant messages that persisted a structured-output parser error."""
    conditions = ["m.role = 'assistant'", "(m.internal_json->'entities'->'response_parser'->>'reason') IS NOT NULL"]
    params: list[Any] = []
    if conversation_id:
        params.append(UUID(conversation_id))
        conditions.append(f"c.id = ${len(params)}")
    if assistant_message_id:
        params.append(UUID(assistant_message_id))
        conditions.append(f"m.id = ${len(params)}")
    if reason:
        params.append(reason)
        conditions.append(f"(m.internal_json->'entities'->'response_parser'->>'reason') = ${len(params)}")
    if since_at is not None:
        params.append(since_at)
        conditions.append(f"m.created_at >= ${len(params)}")
    if until_at is not None:
        params.append(until_at)
        conditions.append(f"m.created_at <= ${len(params)}")
    params.append(limit)
    return await fetch(
        f"""
        SELECT
            c.*,
            m.id AS assistant_message_id,
            m.created_at AS assistant_created_at
        FROM conversations c
        JOIN messages m ON m.conversation_id = c.id
        WHERE {' AND '.join(conditions)}
        ORDER BY m.created_at DESC
        LIMIT ${len(params)}
        """,
        *params,
    )


async def _run_llm_replay(
    *,
    conversation: Any,
    normalized_text: str,
    dispatcher: Any | None,
) -> dict[str, Any]:
    """Run the current pipeline against a reconstructed failure turn."""
    try:
        result = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=normalized_text,
            dispatcher=dispatcher,
            expected_language=conversation.language,
        )
    except Exception as exc:
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_detail": str(exc)[:400],
        }

    parser_reason = ResponseParser.extract_parser_error(result.internal_json)
    return {
        "status": "ok",
        "intent": str(result.internal_json.intent or "").strip() or None,
        "state": str(result.internal_json.state or "").strip() or None,
        "parser_error_reason": parser_reason or None,
        "risk_flags": list(result.internal_json.risk_flags),
        "intent_domain_guard_reason": (
            str(
                (
                    result.internal_json.entities.get("intent_domain_guard", {})
                    if isinstance(result.internal_json.entities, dict)
                    else {}
                ).get("reason")
                or ""
            ).strip()
            or None
        ),
        "user_message_preview": sanitize_replay_preview(result.user_message),
    }


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
