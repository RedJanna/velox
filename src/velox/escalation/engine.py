"""Escalation engine — maps risk flags to escalation matrix and executes actions."""

from pathlib import Path
from typing import Any

import asyncpg
import structlog
import yaml

from velox.config.constants import EscalationLevel, Role, TicketPriority
from velox.config.settings import settings
from velox.models.escalation import EscalationMatrixEntry, EscalationResult

logger = structlog.get_logger(__name__)

LEVEL_ORDER: dict[EscalationLevel, int] = {
    EscalationLevel.L0: 0,
    EscalationLevel.L1: 1,
    EscalationLevel.L2: 2,
    EscalationLevel.L3: 3,
}

PRIORITY_ORDER: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


class EscalationEngine:
    """Loads escalation matrix and evaluates risk flags."""

    def __init__(self) -> None:
        self._matrix: dict[str, EscalationMatrixEntry] = {}

    def load_matrix(self, path: str | None = None) -> None:
        """Load escalation matrix from YAML file into in-memory map."""
        matrix_path = Path(path or settings.escalation_matrix_path)
        with matrix_path.open(encoding="utf-8") as file_obj:
            raw_entries = yaml.safe_load(file_obj)

        self._matrix = {}
        if not isinstance(raw_entries, list):
            logger.warning("escalation_matrix_invalid_format", path=str(matrix_path))
            return

        for entry_data in raw_entries:
            try:
                entry = EscalationMatrixEntry(
                    risk_flag=entry_data["risk_flag"],
                    level=EscalationLevel(entry_data["level"]),
                    route_to_role=Role(entry_data["route_to_role"]),
                    priority=TicketPriority(entry_data["priority"]),
                    action=entry_data.get("action", []),
                    notify_channel=entry_data.get("notify_channel", "panel"),
                    user_message_style=entry_data.get("user_message_style", "calm_premium"),
                    reason_hint=entry_data.get("reason_hint", ""),
                )
                self._matrix[entry.risk_flag] = entry
            except Exception:
                logger.exception("escalation_matrix_entry_parse_failed", entry=entry_data)

    def evaluate(
        self,
        risk_flags: list[str],
        intent: str,
        reference_id: str,
        conversation_id: str,
    ) -> EscalationResult:
        """Evaluate risk flags and return highest-priority escalation result."""
        if not risk_flags:
            return EscalationResult()

        matched_entries: list[EscalationMatrixEntry] = []
        for flag in risk_flags:
            entry = self._matrix.get(flag)
            if entry:
                matched_entries.append(entry)

        if not matched_entries:
            return EscalationResult(risk_flags_matched=risk_flags)

        best = max(
            matched_entries,
            key=lambda item: (LEVEL_ORDER[item.level], PRIORITY_ORDER.get(item.priority.value, 0)),
        )

        all_actions: list[str] = []
        seen_actions: set[str] = set()
        for entry in matched_entries:
            for action in entry.action:
                if action not in seen_actions:
                    seen_actions.add(action)
                    all_actions.append(action)
        if "handoff.create_ticket" in seen_actions and "notify.send" not in seen_actions:
            all_actions.append("notify.send")

        dedupe_key = self._generate_dedupe_key(risk_flag=best.risk_flag, intent=intent, reference_id=reference_id)
        sla_map = {"L0": "low", "L1": "medium", "L2": "high", "L3": "critical"}

        logger.info(
            "escalation_evaluated",
            conversation_id=conversation_id,
            level=best.level.value,
            route_to_role=best.route_to_role.value,
            risk_flags=risk_flags,
            actions=all_actions,
        )

        return EscalationResult(
            level=best.level,
            route_to_role=best.route_to_role,
            dedupe_key=dedupe_key,
            reason=best.reason_hint,
            sla_hint=sla_map.get(best.level.value, "low"),
            actions=all_actions,
            risk_flags_matched=risk_flags,
        )

    @staticmethod
    def _generate_dedupe_key(risk_flag: str, intent: str, reference_id: str) -> str:
        """Build deterministic dedupe key for ticket deduplication."""
        return f"{risk_flag}|{intent}|{reference_id}"

    @staticmethod
    async def check_dedupe(dedupe_key: str, db_pool: asyncpg.Pool) -> bool:
        """Return True if open/in-progress ticket exists for dedupe key."""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM tickets
                WHERE dedupe_key = $1
                AND status NOT IN ('RESOLVED', 'CLOSED')
            )
        """
        async with db_pool.acquire() as conn:
            exists = await conn.fetchval(query, dedupe_key)
        return bool(exists)

    @staticmethod
    async def execute_actions(
        result: EscalationResult,
        conversation_id: str,
        hotel_id: int,
        phone_hash: str,
        transcript_summary: str,
        tools: dict[str, Any],
        db_pool: asyncpg.Pool,
    ) -> dict[str, Any]:
        """Execute escalation actions with dedupe protection."""
        action_results: dict[str, Any] = {}
        if not result.actions:
            return action_results

        ticket_exists = False
        if result.dedupe_key:
            ticket_exists = await EscalationEngine.check_dedupe(result.dedupe_key, db_pool)

        for action in result.actions:
            if action == "handoff.create_ticket" and not ticket_exists:
                ticket_result = await tools["handoff"].create_ticket(
                    hotel_id=hotel_id,
                    conversation_id=conversation_id,
                    reason=result.reason,
                    transcript_summary=transcript_summary,
                    priority=result.sla_hint if result.sla_hint in {"low", "medium", "high"} else "high",
                    assigned_to_role=result.route_to_role.value,
                    dedupe_key=result.dedupe_key,
                )
                action_results["ticket"] = ticket_result
            elif action == "notify.send":
                notify_result = await tools["notify"].send(
                    hotel_id=hotel_id,
                    to_role=result.route_to_role.value,
                    channel="panel",
                    message=f"[{result.level.value}] {result.reason}",
                    metadata={
                        "conversation_id": conversation_id,
                        "phone_hash": phone_hash,
                        "risk_flags": result.risk_flags_matched,
                        "dedupe_key": result.dedupe_key,
                        "transcript_summary": transcript_summary,
                    },
                )
                action_results["notification"] = notify_result
        return action_results
