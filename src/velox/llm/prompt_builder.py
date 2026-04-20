"""System prompt and message assembly for LLM requests."""

from pathlib import Path
from typing import Any

import orjson
import structlog

from velox.config.constants import CONTEXT_WINDOW_MAX_MESSAGES
from velox.core.template_engine import Template
from velox.models.conversation import Conversation, Message
from velox.models.escalation import EscalationMatrixEntry
from velox.models.hotel_profile import (
    BoardType,
    CancellationRule,
    FAQEntry,
    HotelProfile,
    RoomType,
    TransferRouteConfig,
)
from velox.utils.project_paths import get_project_root
from velox.utils.metrics import record_prompt_truncation

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT_CHAR_LIMIT = 12000
_MAX_POLICY_CHARS = 240
_MAX_PROFILE_JSON_CHARS = 420
_MAX_ROOM_TYPES_IN_PROMPT = 6
_MAX_TRANSFER_ROUTES_IN_PROMPT = 6
_MAX_FAQ_TOPICS_IN_PROMPT = 10
_MAX_MENU_TEXT_TOTAL_CHARS = 5000
_MAX_MENU_TEXT_SINGLE_CHARS = 1800

_RUNTIME_POLICY_KERNEL = """
VELox runtime core
- You are Velox, a hotel WhatsApp receptionist.
- Help only with hotel stay, reservation, restaurant, transfer, room service,
  facility, and concierge-nearby topics.
- Reply in RESPONSE_LANGUAGE_LOCK unless the guest explicitly asks to switch language.
- Use only TOOL results and HOTEL_CONTEXT below for hotel facts.
  Do not invent prices, availability, policies, menu items, or facilities.
- For restaurant menu questions, if MENU_TEXT_CONTEXT exists in the prompt,
  treat MENU_TEXT_CONTEXT as authoritative menu source together with HOTEL_CONTEXT.
- For FAQ-style hotel questions, prefer faq_lookup instead of guessing from memory.
- For static hotel-info questions (location, map links, address, contacts),
  call hotel_info_lookup before answering.
- Use booking_availability and booking_quote for live stay answers.
  Never state live availability or price without tool grounding.
- Ask exactly one missing field per turn during verification.
- Do not ask card, CVV, OTP, or bank password. Payment collection is always human-assisted.
- Do not promise a physical action, order, preparation, sending, or finalized
  reservation unless the matching tool has actually executed.
- If a request is outside hotel scope, politely redirect to stay, reservation, room, or hotel services.
- Keep the guest reply concise, premium, and WhatsApp-friendly.
- During reservation date collection, do not ask the year separately.
  Use the current year by default.
- If the guest explicitly requests a different year than the current year,
  stop automated collection and route to human handoff.
- SEASON GATE (STRICT): The hotel operates only between the season.open and
  season.close dates shown in HOTEL_IDENTITY.
- This applies to ALL reservation types: accommodation, restaurant, transfer,
  room service, and any other bookable service.
- If a guest requests any reservation or booking for a date outside the season
  window, immediately inform them that the hotel is closed on that date, provide
  the season opening and closing dates, and do NOT proceed with data collection
  or tool calls for that request.
""".strip()

_OUTPUT_CONTRACT_PROMPT = """
Your response must contain exactly two parts.
Part 1: guest-facing reply in plain text.
Part 2: a new line with the literal header INTERNAL_JSON: followed by exactly one valid JSON object.

INTERNAL_JSON rules:
- keys required: language, intent, state, entities, required_questions,
  tool_calls, notifications, handoff, risk_flags, escalation, next_step
- entities must be an object
- required_questions, tool_calls, notifications, risk_flags must be arrays
- handoff and escalation must be objects
- do not wrap JSON in markdown or code fences
- do not add commentary after the JSON object
""".strip()


def _truncate_text(value: Any, max_chars: int) -> str:
    """Return a short single-line text representation."""
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _compact_json(value: Any, max_chars: int = _MAX_PROFILE_JSON_CHARS) -> str:
    """Serialize a structure compactly for prompt inclusion."""
    if value in (None, "", [], {}):
        return ""
    try:
        text = orjson.dumps(value).decode()
    except TypeError:
        text = str(value)
    return _truncate_text(text, max_chars)


def _localized_name(value: Any) -> str:
    """Return a compact label from localized text objects."""
    if value is None:
        return ""
    tr_name = str(getattr(value, "tr", "") or "").strip()
    en_name = str(getattr(value, "en", "") or "").strip()
    return tr_name or en_name


def _render_section(title: str, lines: list[str]) -> str:
    """Render a prompt section when there are non-empty lines."""
    filtered = [line for line in lines if line]
    if not filtered:
        return ""
    return f"{title}:\n" + "\n".join(filtered)


def _render_freeform_section(title: str, value: Any, max_chars: int = 2600) -> str:
    """Render a freeform multi-line section with bounded size."""
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > max_chars:
        text = text[: max_chars - 3].rstrip() + "..."
    return f"{title}:\n{text}"


def _summarize_room_types(room_types: list[RoomType]) -> str:
    """Return a compact room-type summary for the prompt."""
    lines: list[str] = []
    for room in room_types[:_MAX_ROOM_TYPES_IN_PROMPT]:
        flags = []
        if room.extra_bed:
            flags.append("extra_bed")
        if room.baby_crib:
            flags.append("baby_crib")
        if room.accessible:
            flags.append("accessible")
        room_name = _localized_name(room.name) or f"room_{room.id}"
        flag_text = ",".join(flags) if flags else "standard"
        lines.append(

                f"- id={room.id}; name={room_name}; max_pax={room.max_pax}; size_m2={room.size_m2}; "
                f"bed={room.bed_type}; view={room.view}; flags={flag_text}"

        )
    remaining = len(room_types) - len(lines)
    if remaining > 0:
        lines.append(f"- {remaining} more room types available via HOTEL_CONTEXT lookup.")
    return _render_section("ROOM_TYPES", lines)


def _summarize_board_types(board_types: list[BoardType]) -> str:
    """Return a compact board-type summary."""
    lines = [
        f"- code={board.code}; name={_localized_name(board.name) or board.code}"
        for board in board_types
    ]
    return _render_section("BOARD_TYPES", lines)


def _summarize_cancellation_rules(rules: dict[str, CancellationRule]) -> str:
    """Return key cancellation-policy facts."""
    lines = []
    for name, rule in rules.items():
        lines.append(

                f"- {name}: free_cancel_deadline_days={rule.free_cancel_deadline_days}; "
                f"prepayment_days_before={rule.prepayment_days_before}; "
                f"prepayment_immediate={str(rule.prepayment_immediate).lower()}; refund={str(rule.refund).lower()}"

        )
    return _render_section("CANCELLATION_RULES", lines)


def _summarize_transfer_routes(routes: list[TransferRouteConfig]) -> str:
    """Return compact transfer-route guidance."""
    lines: list[str] = []
    for route in routes[:_MAX_TRANSFER_ROUTES_IN_PROMPT]:
        lines.append(

                f"- {route.route_code}: {route.from_location} -> {route.to_location}; "
                f"price_eur={route.price_eur}; vehicle={route.vehicle_type}; "
                f"max_pax={route.max_pax}; duration_min={route.duration_min}; "
                f"baby_seat={str(route.baby_seat).lower()}"

        )
    remaining = len(routes) - len(lines)
    if remaining > 0:
        lines.append(f"- {remaining} more transfer routes configured.")
    return _render_section("TRANSFER_ROUTES", lines)


def _summarize_restaurant(profile: HotelProfile) -> str:
    """Return compact restaurant context."""
    restaurant = profile.restaurant
    if restaurant is None:
        return ""

    menu = getattr(restaurant, "menu", None)
    menu_summary = "not_configured"
    menu_preview = ""
    if isinstance(menu, dict) and menu:
        category_counts, preview_items = _collect_menu_preview(menu)
        if category_counts:
            menu_summary = ", ".join(category_counts)
        if preview_items:
            menu_preview = ", ".join(preview_items)

    lines = [
        f"- name={restaurant.name}; concept={restaurant.concept}",
        (
            f"- capacity_min={restaurant.capacity_min}; capacity_max={restaurant.capacity_max}; "
            f"max_ai_party_size={restaurant.max_ai_party_size}; late_tolerance_min={restaurant.late_tolerance_min}"
        ),
        f"- area_types={restaurant.area_types or []}",
        f"- hours={_compact_json(restaurant.hours, max_chars=200)}",
        f"- external_guests_allowed={str(restaurant.external_guests_allowed).lower()}",
        f"- menu_catalogue={menu_summary}",
        f"- menu_preview={menu_preview}" if menu_preview else "",
    ]
    return _render_section("RESTAURANT_CONTEXT", lines)


def _collect_menu_preview(menu: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return compact category counts and sample menu items."""
    category_counts: list[str] = []
    preview_items: list[str] = []

    for category, items in menu.items():
        count = _count_menu_items(items)
        if count > 0:
            category_counts.append(f"{category}={count}")
        _append_menu_preview(items, preview_items, limit=12)
        if len(preview_items) >= 12:
            break
    return category_counts, preview_items[:12]


def _count_menu_items(value: Any) -> int:
    """Count likely menu items recursively."""
    if isinstance(value, str):
        return 1 if value.strip() else 0
    if isinstance(value, list):
        return sum(_count_menu_items(item) for item in value)
    if isinstance(value, dict):
        if any(isinstance(value.get(key), str) and str(value.get(key)).strip() for key in ("name", "name_tr", "name_en")):
            return 1
        return sum(_count_menu_items(item) for item in value.values())
    return 0


def _append_menu_preview(value: Any, collector: list[str], *, limit: int) -> None:
    """Append sample menu item names recursively."""
    if len(collector) >= limit:
        return

    if isinstance(value, str):
        normalized = value.strip()
        if normalized and normalized not in collector:
            collector.append(normalized)
        return

    if isinstance(value, list):
        for item in value:
            _append_menu_preview(item, collector, limit=limit)
            if len(collector) >= limit:
                break
        return

    if isinstance(value, dict):
        for key in ("name_tr", "name_en", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                normalized = candidate.strip()
                if normalized and normalized not in collector:
                    collector.append(normalized)
                    if len(collector) >= limit:
                        return
        for nested in value.values():
            _append_menu_preview(nested, collector, limit=limit)
            if len(collector) >= limit:
                break


def _summarize_payment(profile: HotelProfile) -> str:
    """Return compact payment context."""
    payment = profile.payment or {}
    if not payment:
        return ""
    methods = payment.get("methods") or []
    lines = [
        f"- methods={methods}",
        f"- payment_link_handling={_truncate_text(payment.get('payment_link_handling'), _MAX_POLICY_CHARS)}",
        f"- mail_order_handling={_truncate_text(payment.get('mail_order_handling'), _MAX_POLICY_CHARS)}",
    ]
    return _render_section("PAYMENT_CONTEXT", lines)


def _summarize_facility_policies(profile: HotelProfile) -> str:
    """Return selected facility-policy keys only."""
    policy_keys = [
        "check_in",
        "check_out",
        "children",
        "pets",
        "smoking",
        "parking",
        "pool",
        "wifi",
        "accessibility",
        "wellness",
        "laundry",
        "room_service",
    ]
    lines = []
    for key in policy_keys:
        value = profile.facility_policies.get(key)
        if value in (None, "", [], {}):
            continue
        lines.append(f"- {key}={_compact_json(value, max_chars=_MAX_PROFILE_JSON_CHARS)}")
    return _render_section("FACILITY_POLICIES", lines)


def _summarize_faq_topics(faq_entries: list[FAQEntry]) -> str:
    """Return FAQ metadata only; content stays behind faq_lookup."""
    if not faq_entries:
        return ""

    topics: list[str] = []
    for entry in faq_entries:
        topic = str(entry.topic or "").strip()
        if topic and topic not in topics:
            topics.append(topic)
        if len(topics) >= _MAX_FAQ_TOPICS_IN_PROMPT:
            break

    lines = [
        f"- faq_count={len(faq_entries)}",
        f"- use faq_lookup for answer retrieval; topics_sample={topics}",
    ]
    return _render_section("FAQ_CONTEXT", lines)


def _summarize_admin_profile_context(profile: HotelProfile) -> str:
    """Return compact context for admin-managed extra profile fields."""
    extras = profile.model_extra if isinstance(profile.model_extra, dict) else {}
    if not extras:
        return ""

    keys = (
        "location",
        "description",
        "highlights",
        "nearby_places",
        "operational",
        "room_common",
    )
    lines: list[str] = []
    for key in keys:
        value = extras.get(key)
        if value in (None, "", [], {}):
            continue
        lines.append(f"- {key}={_compact_json(value, max_chars=360)}")
    return _render_section("HOTEL_ADMIN_CONTEXT", lines)


def _summarize_assistant_profile_rules(profile: HotelProfile) -> str:
    """Return optional admin-defined assistant constraints from profile extras."""
    extras = profile.model_extra if isinstance(profile.model_extra, dict) else {}
    assistant = extras.get("assistant")
    if not isinstance(assistant, dict):
        return ""

    source_docs = assistant.get("menu_source_documents")
    source_doc_lines: list[str] = []
    if isinstance(source_docs, list):
        for value in source_docs:
            normalized = str(value or "").strip()
            if normalized:
                source_doc_lines.append(f"- {normalized}")

    sections: list[str] = []
    if source_doc_lines:
        sections.append(_render_section("MENU_SOURCE_DOCUMENTS", source_doc_lines))
        menu_text_context = _build_menu_text_context(source_doc_lines)
        if menu_text_context:
            sections.append(_render_freeform_section("MENU_TEXT_CONTEXT", menu_text_context, max_chars=5200))

    menu_scope_prompt = assistant.get("menu_scope_prompt")
    menu_scope_section = _render_freeform_section("MENU_SCOPE_INSTRUCTION_STRICT", menu_scope_prompt)
    if menu_scope_section:
        sections.append(menu_scope_section)

    return "\n\n".join(section for section in sections if section)


def _build_menu_text_context(source_docs: list[str]) -> str:
    """Load text snippets when source documents point to local .txt files."""
    project_root = get_project_root()
    snippets: list[str] = []
    remaining = _MAX_MENU_TEXT_TOTAL_CHARS

    for entry in source_docs:
        if remaining <= 0:
            break
        relative = str(entry).strip()
        if not relative.lower().endswith(".txt"):
            continue
        candidate = (project_root / relative).resolve()
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError:
            continue

        compact = text.strip()
        if not compact:
            continue
        max_chars = min(_MAX_MENU_TEXT_SINGLE_CHARS, remaining)
        excerpt = compact[:max_chars]
        if len(compact) > max_chars:
            excerpt = excerpt.rstrip() + "..."
        snippets.append(f"[{relative}]\n{excerpt}")
        remaining -= len(excerpt)

    return "\n\n".join(snippets)


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
            "- For stay pricing, if the guest asks generally without naming a room type, include every eligible and available room type suitable for the requested occupancy in the same reply.\n"
            "- For stay pricing, if the guest explicitly asks for one room type, keep the reply limited to that room type only.\n"
            "- Never omit an eligible available room type from a general stay-pricing reply and never defer part of the room-price list to a later turn.\n"
            "- During reservation data collection, ask for exactly one missing field per turn."
        )

    def build_system_prompt(self, hotel_id: int) -> str:
        """Build a compact runtime prompt with only high-signal hotel context."""
        profile = self.hotel_profiles.get(hotel_id)
        if profile is None:
            logger.warning("prompt_builder_profile_missing", hotel_id=hotel_id)
            identity_lines = [f"- hotel_id={hotel_id}"]
            sections = [_RUNTIME_POLICY_KERNEL, _render_section("HOTEL_IDENTITY", identity_lines)]
        else:
            identity_lines = [
                f"- hotel_id={profile.hotel_id}; name={_localized_name(profile.hotel_name)}",
                (
                    f"- hotel_type={profile.hotel_type}; timezone={profile.timezone}; "
                    f"currency_base={profile.currency_base}"
                ),
                f"- season={_compact_json(profile.season, max_chars=120)}",
                f"- contacts={_compact_json(profile.contacts, max_chars=240)}",
            ]
            sections = [
                _RUNTIME_POLICY_KERNEL,
                _render_section("HOTEL_IDENTITY", identity_lines),
                _summarize_admin_profile_context(profile),
                _summarize_assistant_profile_rules(profile),
                _summarize_room_types(profile.room_types),
                _summarize_board_types(profile.board_types),
                _summarize_cancellation_rules(profile.cancellation_rules),
                _summarize_transfer_routes(profile.transfer_routes),
                _summarize_restaurant(profile),
                _summarize_payment(profile),
                _summarize_facility_policies(profile),
                _summarize_faq_topics(profile.faq_data),
            ]

        joined_prompt = "\n\n".join(section for section in sections if section)
        if len(joined_prompt) > SYSTEM_PROMPT_CHAR_LIMIT:
            record_prompt_truncation("system_prompt")
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
        detected_language: str | None = None,
        burst_metadata: dict[str, Any] | None = None,
        reply_context: dict[str, Any] | None = None,
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

        if reply_context and reply_context.get("present"):
            if reply_context.get("resolved"):
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "REPLY_CONTEXT: The guest explicitly used WhatsApp reply-to for this turn.\n"
                            f"Replied target role: {reply_context.get('target_role', 'unknown')}\n"
                            f"Replied target message: {reply_context.get('target_content', '')}\n"
                            "Interpret short references like 'this', 'that', 'yes', 'no', "
                            "or 'the second one' relative to that replied target first."
                        ),
                    }
                )
            else:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "REPLY_CONTEXT: The guest used WhatsApp reply-to, but the referenced "
                            "message could not be resolved reliably. Use normal conversation history "
                            "and do not over-assume the target."
                        ),
                    }
                )

        if burst_metadata and burst_metadata.get("part_count", 1) > 1:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"BURST_CONTEXT: The guest sent {burst_metadata['part_count']} "
                        f"consecutive messages within {burst_metadata.get('span_seconds', '?')}s. "
                        "They have been merged into a single user turn below. "
                        "Treat them as one coherent request and reply with a single unified response."
                    ),
                }
            )

        response_language = (detected_language or conversation.language or "tr").upper()
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
        messages.append({"role": "system", "content": _OUTPUT_CONTRACT_PROMPT})
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
            f"last_user_message={_truncate_text(last_user_text or 'n/a', 180)}",
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
