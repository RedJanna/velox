"""System prompt and message assembly for LLM requests."""

from pathlib import Path
from typing import Any

import structlog

from velox.config.constants import CONTEXT_WINDOW_MAX_MESSAGES
from velox.core.template_engine import Template
from velox.models.conversation import Conversation, Message
from velox.models.escalation import EscalationMatrixEntry
from velox.models.hotel_profile import HotelProfile

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT_CHAR_LIMIT = 32000
MASTER_PROMPT_PATH = "docs/master_prompt_v2.md"
_MASTER_PROMPT_A_SECTION: str | None = None


def _load_master_prompt_a_section() -> str:
    """Load runtime A-section from master prompt once per process."""
    global _MASTER_PROMPT_A_SECTION
    if _MASTER_PROMPT_A_SECTION is not None:
        return _MASTER_PROMPT_A_SECTION

    prompt_path = Path(MASTER_PROMPT_PATH)
    if not prompt_path.exists():
        logger.warning("master_prompt_file_missing", path=str(prompt_path))
        _MASTER_PROMPT_A_SECTION = "Master prompt not found."
        return _MASTER_PROMPT_A_SECTION

    raw_text = prompt_path.read_text(encoding="utf-8")
    start_marker = "# A)"
    end_marker = "# B)"
    start_index = raw_text.find(start_marker)
    end_index = raw_text.find(end_marker)

    if start_index == -1:
        selected = raw_text
    elif end_index == -1 or end_index <= start_index:
        selected = raw_text[start_index:]
    else:
        selected = raw_text[start_index:end_index]

    _MASTER_PROMPT_A_SECTION = selected.strip()
    return _MASTER_PROMPT_A_SECTION


class PromptBuilder:
    """Build system prompt and chat messages for a conversation turn."""

    def __init__(
        self,
        hotel_profiles: dict[int, HotelProfile],
        escalation_matrix: list[EscalationMatrixEntry],
        template_library: list[Template],
    ) -> None:
        self.hotel_profiles = hotel_profiles
        self.escalation_matrix = escalation_matrix
        self.template_library = template_library
        self.master_prompt_a = _load_master_prompt_a_section()

    def build_system_prompt(self, hotel_id: int) -> str:
        """Build complete system prompt from static and dynamic context layers."""
        profile = self.hotel_profiles.get(hotel_id)
        if profile is None:
            logger.warning("prompt_builder_profile_missing", hotel_id=hotel_id)
            profile_dump: dict[str, Any] = {"hotel_id": hotel_id}
            facility_policies: dict[str, Any] = {}
            faq_data: list[dict[str, Any]] = []
        else:
            profile_dump = profile.model_dump()
            facility_policies = profile.facility_policies
            faq_data = profile.faq_data

        escalation_summary = [
            {
                "risk_flag": entry.risk_flag,
                "level": entry.level.value,
                "route_to_role": entry.route_to_role.value,
                "priority": entry.priority.value,
                "actions": entry.action,
            }
            for entry in self.escalation_matrix
        ]

        template_summary = [
            {
                "id": template.id,
                "intent": template.intent,
                "state": template.state,
                "language": template.language,
            }
            for template in self.template_library
        ]

        sections = [
            "### MASTER_PROMPT_A_SECTION",
            self.master_prompt_a,
            "### HOTEL_PROFILE",
            str(profile_dump),
            "### FACILITY_POLICIES",
            str(facility_policies),
            "### ESCALATION_MATRIX",
            str(escalation_summary),
            "### TEMPLATE_LIBRARY",
            str(template_summary),
            "### FAQ_DATA",
            str(faq_data),
        ]
        joined_prompt = "\n\n".join(sections)

        if len(joined_prompt) > SYSTEM_PROMPT_CHAR_LIMIT:
            logger.warning(
                "system_prompt_truncated",
                hotel_id=hotel_id,
                total_chars=len(joined_prompt),
                max_chars=SYSTEM_PROMPT_CHAR_LIMIT,
            )
            return joined_prompt[: SYSTEM_PROMPT_CHAR_LIMIT - 3] + "..."
        return joined_prompt

    def build_messages(
        self,
        conversation: Conversation,
        new_user_message: str,
        system_events: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Build OpenAI messages array for current turn."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.build_system_prompt(conversation.hotel_id)}
        ]

        history = sorted(conversation.messages, key=lambda message: message.created_at)
        if len(history) > CONTEXT_WINDOW_MAX_MESSAGES:
            old_messages = history[: -CONTEXT_WINDOW_MAX_MESSAGES]
            recent_messages = history[-CONTEXT_WINDOW_MAX_MESSAGES :]
            summary = self.summarize_old_messages(old_messages)
            messages.append({"role": "system", "content": f"CONVERSATION_SUMMARY:\n{summary}"})
        else:
            recent_messages = history

        for item in recent_messages:
            role = item.role if item.role in {"user", "assistant", "system", "tool"} else "user"
            messages.append({"role": role, "content": item.content})

        if system_events:
            for event in system_events:
                messages.append({"role": "system", "content": f"SYSTEM_EVENT: {event}"})

        messages.append({"role": "user", "content": new_user_message})
        messages.append(
            {
                "role": "system",
                "content": (
                    "Respond in two parts: USER_MESSAGE and INTERNAL_JSON. "
                    "INTERNAL_JSON must be valid JSON and include intent, state, entities, "
                    "tool_calls, risk_flags, escalation, and next_step."
                ),
            }
        )
        return messages

    def summarize_old_messages(self, messages: list[Message]) -> str:
        """Summarize old history by extracting intents, entities, and latest user ask."""
        if not messages:
            return "No previous messages."

        last_user_text = ""
        intents: list[str] = []
        entity_keys: set[str] = set()

        for message in messages:
            if message.role == "user":
                last_user_text = message.content
            if isinstance(message.internal_json, dict):
                intent = message.internal_json.get("intent")
                if isinstance(intent, str) and intent:
                    intents.append(intent)
                entities = message.internal_json.get("entities")
                if isinstance(entities, dict):
                    entity_keys.update(str(key) for key in entities.keys())

        unique_intents = list(dict.fromkeys(intents))
        summary_parts = [
            f"message_count={len(messages)}",
            f"last_user_message={last_user_text or 'n/a'}",
            f"intents={unique_intents or ['unknown']}",
            f"entity_keys={sorted(entity_keys)}",
        ]
        return "; ".join(summary_parts)


def build_prompt_builder(
    hotel_profiles: dict[int, HotelProfile],
    escalation_matrix: list[EscalationMatrixEntry],
    template_library: list[Template],
) -> PromptBuilder:
    """Construct a prompt builder instance."""
    return PromptBuilder(
        hotel_profiles=hotel_profiles,
        escalation_matrix=escalation_matrix,
        template_library=template_library,
    )
