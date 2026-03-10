"""Chat Lab feedback service for corrected replies and scenario generation."""

from __future__ import annotations

import asyncio
import hashlib
import re
import unicodedata
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog
import yaml

from velox.config.constants import TOOL_RETRY_BACKOFF_SECONDS
from velox.config.settings import settings
from velox.core.intent_engine import detect_intent
from velox.db.repositories.conversation import ConversationRepository
from velox.llm.client import LLMClient, get_llm_client
from velox.models.chat_lab_feedback import (
    ChatLabFeedbackRequest,
    ChatLabFeedbackResponse,
    FeedbackScaleItem,
)
from velox.models.conversation import Conversation, Message

logger = structlog.get_logger(__name__)

_SCENARIO_WRITE_LOCK = asyncio.Lock()
_SCENARIO_STOP_WORDS = {
    "acaba",
    "ama",
    "ancak",
    "artik",
    "bana",
    "bence",
    "bir",
    "bize",
    "bunu",
    "burada",
    "cok",
    "daha",
    "degil",
    "gibi",
    "gore",
    "icin",
    "ile",
    "ilgili",
    "isterseniz",
    "kadar",
    "lutfen",
    "nasil",
    "olan",
    "olarak",
    "olsun",
    "sonra",
    "sizin",
    "size",
    "tekrar",
    "ve",
    "veya",
    "yani",
}
_MODEL_TIMEOUT_SECONDS = 10.0
_MODEL_VARIANT_PENALTIES = {
    "mini": 220,
    "nano": 260,
    "preview": 40,
    "audio": 500,
    "realtime": 500,
    "transcribe": 500,
    "search": 500,
}


class ChatLabFeedbackError(RuntimeError):
    """Base exception for Chat Lab feedback workflows."""


class FeedbackConversationNotFoundError(ChatLabFeedbackError):
    """Raised when no active test conversation exists."""


class FeedbackMessageNotFoundError(ChatLabFeedbackError):
    """Raised when the selected assistant message is missing."""


FEEDBACK_SCALE: tuple[FeedbackScaleItem, ...] = (
    FeedbackScaleItem(
        rating=1,
        label="Kesinlikle Yanlis",
        summary="Yanit tamamen hatali.",
        tooltip="Bilgi tamamen yanlis mi? Burayi sec ve dogruyu sisteme ogret.",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=2,
        label="Hatali Anlatim",
        summary="Bilgi dogru ama anlatim yaniltici.",
        tooltip="Bilgi dogru ama anlatim bozuk mu?",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=3,
        label="Eksik Bilgi",
        summary="Temel cevap dogru ama kritik detay eksik.",
        tooltip="Cevap yetersiz mi? Eksikleri tamamla.",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=4,
        label="Gereksiz Ayrinti",
        summary="Bilgi dogru ama fazla uzun.",
        tooltip="Cok mu laf kalabaligi var? Sadelestirilmis halini onayla.",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=5,
        label="Mukemmel",
        summary="Yanit dogru ve yeterli.",
        tooltip="Yanit dogruysa bunu secin; ek islem yapilmaz.",
        correction_required=False,
    ),
)
_FEEDBACK_BY_RATING = {item.rating: item for item in FEEDBACK_SCALE}


class ChatLabFeedbackService:
    """Coordinate reply feedback, correction synthesis, and scenario export."""

    def __init__(
        self,
        repository: ConversationRepository | None = None,
        llm_client: LLMClient | None = None,
        scenarios_dir: Path | None = None,
        template_path: Path | None = None,
    ) -> None:
        self._repository = repository or ConversationRepository()
        self._llm_client = llm_client or get_llm_client()
        project_root = Path(__file__).resolve().parents[3]
        self._scenarios_dir = scenarios_dir or (project_root / settings.scenarios_dir)
        self._template_path = template_path or (self._scenarios_dir / "_TEMPLATE.yaml")

    async def submit_feedback(self, payload: ChatLabFeedbackRequest) -> ChatLabFeedbackResponse:
        """Process one feedback event and optionally generate a new scenario file."""
        scale_item = _FEEDBACK_BY_RATING[payload.rating]
        if payload.rating == 5:
            return ChatLabFeedbackResponse(
                status="acknowledged",
                rating=payload.rating,
                rating_label=scale_item.label,
            )

        conversation = await self._load_active_conversation(payload.phone)
        messages = await self._repository.get_messages(conversation.id, limit=500, offset=0)
        relevant_messages = _messages_until_target(messages, payload.assistant_message_id)
        assistant_message = relevant_messages[-1]
        if assistant_message.role != "assistant":
            raise FeedbackMessageNotFoundError("The selected message is not an assistant reply.")

        selected_model = await self._select_best_model()
        corrected_reply = await self._build_corrected_reply(
            conversation=conversation,
            messages=relevant_messages,
            rating=payload.rating,
            correction=str(payload.correction or ""),
            selected_model=selected_model,
        )

        scenario_path = await self._save_feedback_scenario(
            conversation=conversation,
            messages=relevant_messages,
            rating=payload.rating,
            correction=str(payload.correction or ""),
            corrected_reply=corrected_reply,
            selected_model=selected_model,
        )
        scenario_code = scenario_path.stem.split("_", 1)[0]

        logger.info(
            "chat_lab_feedback_saved",
            rating=payload.rating,
            scenario_code=scenario_code,
            model=selected_model,
            message_id=str(payload.assistant_message_id),
        )
        return ChatLabFeedbackResponse(
            status="scenario_created",
            rating=payload.rating,
            rating_label=scale_item.label,
            corrected_reply=corrected_reply,
            selected_model=selected_model,
            scenario_code=scenario_code,
            scenario_path=_display_path(scenario_path),
        )

    async def _load_active_conversation(self, phone: str) -> Conversation:
        hashed_phone = _hash_phone(_ensure_test_phone(phone))
        conversation = await self._repository.get_active_by_phone(settings.elektra_hotel_id, hashed_phone)
        if conversation is None or conversation.id is None:
            raise FeedbackConversationNotFoundError("No active test conversation found for this phone.")
        return conversation

    async def _select_best_model(self) -> str:
        available_models = await self._list_available_models()
        if not available_models:
            return self._llm_client.primary_model
        return max(available_models, key=_model_rank)

    async def _list_available_models(self) -> list[str]:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                models_page = await asyncio.wait_for(
                    self._llm_client.client.models.list(),
                    timeout=_MODEL_TIMEOUT_SECONDS,
                )
                model_ids = [
                    str(model.id)
                    for model in getattr(models_page, "data", [])
                    if _is_feedback_model_candidate(str(model.id))
                ]
                if model_ids:
                    return sorted(set(model_ids))
                return []
            except Exception as error:
                last_error = error
                logger.warning(
                    "chat_lab_model_list_failed",
                    attempt_number=attempt,
                    error_type=type(error).__name__,
                )
                if attempt < 3:
                    await asyncio.sleep(TOOL_RETRY_BACKOFF_SECONDS[attempt - 1])
        if last_error is not None:
            logger.warning("chat_lab_model_list_fallback", fallback_model=self._llm_client.primary_model)
        return []

    async def _build_corrected_reply(
        self,
        conversation: Conversation,
        messages: Sequence[Message],
        rating: int,
        correction: str,
        selected_model: str,
    ) -> str:
        user_message = _latest_user_message(messages)
        wrong_reply = str(messages[-1].content)
        scale_item = _FEEDBACK_BY_RATING[rating]
        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You rewrite one hotel assistant reply for internal QA. "
                    "Return only the final guest-facing reply. "
                    "Use the admin correction as the source of truth. "
                    "If the old answer conflicts with the admin correction, ignore the old answer. "
                    "Keep the response in a single WhatsApp-style message, concise, and in the requested language."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Language: {conversation.language}\n"
                    f"Rating: {rating} - {scale_item.label}\n"
                    f"Guest message: {user_message}\n"
                    f"Wrong assistant reply: {wrong_reply}\n"
                    f"Admin correction: {correction}\n"
                    "Produce the ideal corrected reply."
                ),
            },
        ]
        try:
            response = await self._llm_client.chat_completion(
                messages=prompt_messages,
                model=selected_model,
            )
            corrected_reply = _extract_response_text(response).strip()
            if corrected_reply:
                return corrected_reply
        except Exception as error:
            logger.warning(
                "chat_lab_reply_synthesis_failed",
                error_type=type(error).__name__,
                model=selected_model,
            )
        return correction.strip()

    async def _save_feedback_scenario(
        self,
        conversation: Conversation,
        messages: Sequence[Message],
        rating: int,
        correction: str,
        corrected_reply: str,
        selected_model: str,
    ) -> Path:
        async with _SCENARIO_WRITE_LOCK:
            scenario_template = await asyncio.to_thread(_load_template_data, self._template_path)
            scenario_code = await asyncio.to_thread(_next_scenario_code, self._scenarios_dir)
            scenario_data = _build_scenario_document(
                template_data=scenario_template,
                code=scenario_code,
                conversation=conversation,
                messages=messages,
                rating=rating,
                correction=correction,
                corrected_reply=corrected_reply,
                selected_model=selected_model,
            )
            await asyncio.to_thread(self._scenarios_dir.mkdir, parents=True, exist_ok=True)
            filename = f"{scenario_code}_{_slugify(_latest_user_message(messages))}.yaml"
            scenario_path = self._scenarios_dir / filename
            await asyncio.to_thread(_write_yaml_file, scenario_path, scenario_data)
            return scenario_path


def _ensure_test_phone(phone: str) -> str:
    clean_phone = phone.strip()
    if clean_phone.startswith("test_"):
        return clean_phone
    return f"test_{clean_phone}"


def _hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


def _messages_until_target(messages: Sequence[Message], message_id: UUID) -> list[Message]:
    collected: list[Message] = []
    for message in messages:
        collected.append(message)
        if message.id == message_id:
            return collected
    raise FeedbackMessageNotFoundError("The selected assistant reply could not be found.")


def _latest_user_message(messages: Sequence[Message]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return str(message.content)
    return ""


def _load_template_data(template_path: Path) -> dict[str, Any]:
    with template_path.open(encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}
    if not isinstance(data, dict):
        raise ChatLabFeedbackError("Scenario template is invalid.")
    return data


def _next_scenario_code(scenarios_dir: Path) -> str:
    existing = sorted(scenarios_dir.glob("S*.yaml"))
    if not existing:
        return "S048"
    last_code = existing[-1].stem.split("_", 1)[0]
    next_value = int(last_code.removeprefix("S")) + 1
    return f"S{next_value:03d}"


def _write_yaml_file(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file_obj:
        yaml.safe_dump(
            payload,
            file_obj,
            allow_unicode=True,
            sort_keys=False,
            width=1000,
        )


def _build_scenario_document(
    template_data: dict[str, Any],
    code: str,
    conversation: Conversation,
    messages: Sequence[Message],
    rating: int,
    correction: str,
    corrected_reply: str,
    selected_model: str,
) -> dict[str, Any]:
    assistant_message = messages[-1]
    assistant_internal = assistant_message.internal_json or {}
    intent = str(assistant_internal.get("intent") or detect_intent(_latest_user_message(messages)).value)
    category = _category_from_intent(intent)
    summary = _FEEDBACK_BY_RATING[rating].label
    steps = _build_scenario_steps(messages, corrected_reply)
    scenario_data = dict(template_data)
    scenario_data["code"] = code
    scenario_data["name"] = f"Chat Lab - {_compact_text(_latest_user_message(messages), limit=48)}"
    scenario_data["description"] = (
        f"Admin geri bildirimi ile uretildi. Puan: {rating}/5 ({summary}). "
        f"Mesaj kimligi: {assistant_message.id}."
    )
    scenario_data["category"] = category
    scenario_data["language"] = conversation.language
    scenario_data["tags"] = ["chat_lab", "human_feedback", category, f"rating_{rating}"]
    scenario_data["source"] = f"chat_lab_feedback_{assistant_message.id}"
    scenario_data["steps"] = steps
    scenario_data["feedback"] = {
        "rating": rating,
        "rating_label": summary,
        "selected_model": selected_model,
        "admin_correction": correction,
        "corrected_reply": corrected_reply,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return scenario_data


def _build_scenario_steps(messages: Sequence[Message], corrected_reply: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    pairs = _pair_user_assistant_messages(messages)
    if not pairs:
        raise ChatLabFeedbackError("Conversation transcript is missing a user-assistant pair.")

    for index, (user_message, assistant_message) in enumerate(pairs, start=1):
        assistant_internal = assistant_message.internal_json or {}
        is_last = index == len(pairs)
        step = {
            "user": user_message.content,
            "expect_intent": str(assistant_internal.get("intent") or detect_intent(user_message.content).value),
            "expect_state": str(assistant_internal.get("state") or "INTENT_DETECTED"),
            "expect_tool_calls": _tool_call_names(assistant_internal.get("tool_calls")),
            "expect_reply_contains": _extract_significant_terms(
                corrected_reply if is_last else assistant_message.content
            ),
            "expect_reply_must_not": _extract_forbidden_terms(
                bad_reply=assistant_message.content,
                corrected_reply=corrected_reply,
            )
            if is_last
            else [],
            "expect_risk_flags": [str(flag) for flag in assistant_internal.get("risk_flags") or []],
            "note": "Admin duzeltmesiyle guncellenen hedef adim."
            if is_last
            else "Baglam adimi.",
        }
        steps.append(step)
    return steps


def _pair_user_assistant_messages(messages: Sequence[Message]) -> list[tuple[Message, Message]]:
    pending_user: Message | None = None
    pairs: list[tuple[Message, Message]] = []
    for message in messages:
        if message.role == "user":
            pending_user = message
            continue
        if message.role == "assistant" and pending_user is not None:
            pairs.append((pending_user, message))
            pending_user = None
    return pairs


def _tool_call_names(raw_tool_calls: Any) -> list[str]:
    if not isinstance(raw_tool_calls, list):
        return []
    names: list[str] = []
    for item in raw_tool_calls:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return names


def _extract_significant_terms(text: str, limit: int = 5) -> list[str]:
    tokens = re.findall(r"\b[\w\-]{4,}\b", text.lower())
    terms: list[str] = []
    for token in tokens:
        if token in _SCENARIO_STOP_WORDS:
            continue
        if token not in terms:
            terms.append(token)
        if len(terms) >= limit:
            break
    return terms


def _extract_forbidden_terms(bad_reply: str, corrected_reply: str, limit: int = 5) -> list[str]:
    bad_terms = _extract_significant_terms(bad_reply, limit=limit * 3)
    corrected_terms = set(_extract_significant_terms(corrected_reply, limit=limit * 3))
    forbidden = [term for term in bad_terms if term not in corrected_terms]
    return forbidden[:limit]


def _compact_text(text: str, limit: int) -> str:
    clean_text = " ".join(text.split())
    if len(clean_text) <= limit:
        return clean_text
    return clean_text[: limit - 3].rstrip() + "..."


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return (slug or "chat_lab_feedback")[:48]


def _category_from_intent(intent: str) -> str:
    if intent.startswith("stay_"):
        return "stay"
    if intent.startswith("restaurant_"):
        return "restaurant"
    if intent.startswith("transfer_"):
        return "transfer"
    if intent.startswith("guest_") or intent in {
        "early_checkin_request",
        "late_checkout_request",
        "special_event_request",
    }:
        return "guest_ops"
    return "general"


def _extract_response_text(response: dict[str, Any]) -> str:
    choices = response.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _is_feedback_model_candidate(model_id: str) -> bool:
    normalized = model_id.lower()
    if not (normalized.startswith("gpt") or normalized.startswith("o")):
        return False
    return not any(marker in normalized for marker in ("audio", "realtime", "transcribe", "search", "tts"))


def _model_rank(model_id: str) -> tuple[int, int, str]:
    normalized = model_id.lower()
    capability = 100
    if normalized.startswith("gpt-5"):
        capability = 1000
    elif normalized.startswith("o4"):
        capability = 930
    elif normalized.startswith("o3"):
        capability = 900
    elif normalized.startswith("gpt-4.5"):
        capability = 860
    elif normalized.startswith("gpt-4o"):
        capability = 840
    elif normalized.startswith("gpt-4.1"):
        capability = 820
    elif normalized.startswith("gpt-4"):
        capability = 780
    elif normalized.startswith("o1"):
        capability = 760
    elif normalized.startswith("gpt-3.5"):
        capability = 500

    for marker, penalty in _MODEL_VARIANT_PENALTIES.items():
        if marker in normalized:
            capability -= penalty

    date_match = re.search(r"(20\d{2})-(\d{2})-(\d{2})$", normalized)
    date_value = 0
    if date_match:
        year, month, day = date_match.groups()
        date_value = int(year) * 10_000 + int(month) * 100 + int(day)
    return capability, date_value, normalized


def _display_path(path: Path) -> str:
    raw_path = str(path)
    if raw_path.startswith("/mnt/") and len(raw_path) > 6:
        drive = raw_path[5].upper()
        remainder = raw_path[6:].replace("/", "\\")
        return f"{drive}:{remainder}"
    return raw_path
