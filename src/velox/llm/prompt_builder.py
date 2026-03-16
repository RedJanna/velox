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

    def _build_conversational_flow_instruction(self, hotel_id: int) -> str:
        """Build profile-driven brevity constraints for guest-facing responses."""
        profile = self.hotel_profiles.get(hotel_id)
        flow = profile.hotel_conversational_flow if profile else None

        max_paragraph_lines = flow.max_paragraph_lines if flow else 3
        max_list_items = flow.max_list_items if flow else 5
        max_follow_up_questions = flow.max_follow_up_questions if flow else 2
        avoid_repeating = flow.avoid_repeating_confirmed_facts if flow else True
        summarize_large_lists = flow.summarize_large_price_lists if flow else True
        ask_before_full_dump = flow.ask_before_full_price_dump if flow else True
        style = flow.style if flow else "concise_premium"

        return (
            "HOTEL_CONVERSATIONAL_FLOW (STRICT):\n"
            f"- style={style}\n"
            "- Keep the guest message concise and high-signal.\n"
            f"- Each paragraph must be <= {max_paragraph_lines} lines.\n"
            f"- Show at most {max_list_items} list items in one message.\n"
            f"- Ask at most {max_follow_up_questions} follow-up question(s) per turn.\n"
            f"- avoid_repeating_confirmed_facts={str(avoid_repeating).lower()}\n"
            f"- summarize_large_price_lists={str(summarize_large_lists).lower()}\n"
            f"- ask_before_full_price_dump={str(ask_before_full_dump).lower()}\n"
            "- Do not repeat already confirmed details unless the guest asks again or data changes.\n"
            "- For long room-price outputs, share a compact shortlist first and offer full breakdown on request.\n"
            "- During reservation data collection, ask for exactly one missing field per turn."
        )

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
            faq_data = [entry.model_dump() for entry in profile.faq_data]

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

        response_language = (conversation.language or "tr").upper()
        messages.append(
            {
                "role": "system",
                "content": (
                    f"RESPONSE_LANGUAGE_LOCK: {response_language}. "
                    "Guest-facing reply must be in this language unless the guest explicitly asks to switch."
                ),
            }
        )
        messages.append(
            {
                "role": "system",
                "content": self._build_conversational_flow_instruction(conversation.hotel_id),
            }
        )
        messages.append({"role": "user", "content": new_user_message})
        messages.append(
            {
                "role": "system",
                "content": (
                    "Your response MUST have exactly two clearly separated sections.\n"
                    "Section 1 — the guest-facing reply (plain text, no label needed).\n"
                    "Section 2 — start on a new line with the literal header INTERNAL_JSON: "
                    "followed by a single valid JSON object on the same or next line.\n"
                    "The JSON must include: language, intent, state, entities, "
                    "required_questions, tool_calls, notifications, handoff, "
                    "risk_flags, escalation, and next_step.\n"
                    "Do NOT wrap the JSON in markdown code fences or bold markers.\n\n"
                    "PRICING RULES:\n"
                    "- When presenting room prices, ALWAYS show BOTH cancellation "
                    "policies (FREE_CANCEL and NON_REFUNDABLE) side by side for each "
                    "room type. NEVER ask the guest which cancellation policy they "
                    "prefer before showing prices.\n"
                    "- Always pass the correct 'adults' parameter to booking tools "
                    "based on what the guest requested. Do NOT default to 2.\n"
                    "- If the guest did not specify a currency, default to EUR and "
                    "do not ask a currency question before quoting.\n"
                    "- For stay quote requests, do NOT ask a default year-confirmation "
                    "question (e.g., '2026 mi?'). If the guest gives day/month without "
                    "a year, infer a reasonable upcoming year from context and continue.\n"
                    "- Ask a year-specific clarification only when the guest explicitly "
                    "asks about year selection or context is truly ambiguous.\n"
                    "- If children are included, only show prices when the booking "
                    "tool result explicitly reflects the requested child occupancy. "
                    "If the tool ignores the children or returns an occupancy mismatch "
                    "error, do NOT present adult-only prices.\n"
                    "- If booking_quote cannot return a live rate (error or no offers), "
                    "do NOT ask a year question as fallback. Briefly explain that live "
                    "pricing is unavailable and offer handoff for manual confirmation.\n"
                    "- In Turkish replies, use cancellation labels exactly as "
                    "'İptal edilemez' and 'Ücretsiz İptal'.\n"
                    "- If the response language is Turkish, always use proper Turkish "
                    "spelling and diacritics (e.g., İ, ı, Ş, ş, Ğ, ğ, Ç, ç, Ö, ö, Ü, ü).\n"
                    "- For multi-room requests, list only the requested room count "
                    "and never add extra room blocks not requested by the guest.\n"
                    "- Keep price lists compact: show up to 5 room-type lines first; "
                    "if more exist, ask whether the guest wants the full list.\n"
                    "- Do not add generic statements like 'EUR fiyatlarımız' when "
                    "the currency is already visible in the listed prices.\n"
                    "- Mention 'Ön ödeme girişten 7 gün önce planlanır' only if the "
                    "guest explicitly asks prepayment timing.\n"
                    "- Add the Turkish stay quote policy notes below only when you are "
                    "actually presenting a price list from booking_quote. Do not repeat "
                    "these notes in non-price follow-up messages.\n"
                    "- For child bedding/extra bed questions, do not assume a single "
                    "extra bed by default. Use HOTEL_PROFILE child policy and room "
                    "capacity data exactly as provided.\n"
                    "- In Turkish stay quote messages, include these notes after the "
                    "price list:\n"
                    "  1) Ücretsiz iptal seçeneği ile yapılan rezervasyonlarda "
                    "girişten 5 gün öncesine kadar iptal olması halinde %100 geri "
                    "ödeme alabilirsiniz.\n"
                    "  2) Rezervasyon onayı için iptal edilemez rezervasyonlarda "
                    "1 gecelik ödeme tahsil edilmektedir. Kalan ödemeyi giriş "
                    "günündeki güncel döviz kuruna göre TL veya döviz olarak "
                    "yapabilirsiniz.\n"
                    "  3) Nazik bilgilendirme: Oda numarası için önceden garanti "
                    "veremiyoruz; ancak girişiniz sırasında uygunluk doğrultusunda "
                    "size memnuniyetle yardımcı oluruz."
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
                    entity_keys.update(str(key) for key in entities)

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


_prompt_builder: PromptBuilder | None = None


def get_prompt_builder() -> PromptBuilder:
    """Get singleton prompt builder, lazily initialised from cached loaders."""
    global _prompt_builder
    if _prompt_builder is None:
        from velox.core.hotel_profile_loader import load_all_profiles
        from velox.core.template_engine import load_templates
        from velox.escalation.matrix import load_escalation_matrix

        _prompt_builder = PromptBuilder(
            hotel_profiles=load_all_profiles(),
            escalation_matrix=load_escalation_matrix(),
            template_library=load_templates(),
        )
    return _prompt_builder
