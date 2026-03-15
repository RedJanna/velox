"""Real LLM pipeline processor for eval scenarios.

Bu modul, ScenarioRunner'in bekledigi ScenarioProcessor protokolune
uygun sekilde gercek LLM pipeline'ini sarar. Mock processor yerine
gercek OpenAI API cagrilari yapilir.

Kullanim:
    from tests.scenarios.real_processor import RealPipelineProcessor

    processor = RealPipelineProcessor()
    results = await run_eval(mode="fast", processor=processor)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

# Proje kokunu sys.path'e ekle (standalone calisma icin)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from velox.config.constants import ConversationState  # noqa: E402
from velox.config.settings import settings  # noqa: E402
from velox.escalation.risk_detector import detect_all_risk_flags  # noqa: E402
from velox.llm.response_parser import ResponseParser  # noqa: E402
from velox.models.conversation import Conversation, Message  # noqa: E402


class RealPipelineProcessor:
    """Gercek LLM pipeline'ini ScenarioProcessor protokolune uygun sarar.

    Her senaryo icin ayri bir Conversation nesnesi olusturur ve
    multi-turn step'ler arasi mesaj gecmisini biriktirir.

    Args:
        dispatcher: Tool dispatcher (None ise mock_tool_executor kullanilir).
        language: Varsayilan dil kodu.
    """

    def __init__(
        self,
        dispatcher: Any | None = None,
        language: str = "tr",
    ) -> None:
        self._dispatcher = dispatcher
        self._language = language
        self._conversation: Conversation | None = None
        self._conv_id = uuid4()

    def reset(self) -> None:
        """Yeni senaryo oncesi conversation'i sifirla."""
        self._conversation = None
        self._conv_id = uuid4()

    def _ensure_conversation(self, current_state: ConversationState) -> Conversation:
        """Mevcut conversation'i dondur veya yenisini olustur."""
        if self._conversation is None:
            self._conversation = Conversation(
                id=self._conv_id,
                hotel_id=settings.elektra_hotel_id,
                phone_hash="eval_test",
                phone_display="eval***",
                language=self._language,
                current_state=current_state,
            )
        else:
            self._conversation.current_state = current_state
        return self._conversation

    async def __call__(
        self,
        user_message: str,
        current_state: ConversationState,
    ) -> dict[str, Any]:
        """Gercek pipeline'i cagir ve runner-uyumlu dict dondur.

        Args:
            user_message: Misafir mesaji.
            current_state: Konusmanin mevcut durumu.

        Returns:
            dict: {"intent", "state", "tool_calls", "reply", "risk_flags"}
        """
        # Lazy import — whatsapp_webhook modulu agir, sadece ihtiyac olunca yukle
        from velox.api.routes.whatsapp_webhook import _run_message_pipeline

        conversation = self._ensure_conversation(current_state)

        # Kullanici mesajini gecmise ekle
        user_msg = Message(
            conversation_id=self._conv_id,
            role="user",
            content=user_message,
        )
        conversation.messages.append(user_msg)

        # Gercek pipeline'i cagir
        llm_response = await _run_message_pipeline(
            conversation=conversation,
            normalized_text=user_message,
            dispatcher=self._dispatcher,
            expected_language=self._language,
        )

        # AI yanitini gecmise ekle (bir sonraki step icin context)
        assistant_msg = Message(
            conversation_id=self._conv_id,
            role="assistant",
            content=llm_response.user_message,
            internal_json=llm_response.internal_json.model_dump(mode="json"),
        )
        conversation.messages.append(assistant_msg)

        # Risk flag'lari birlestirilmis sekilde al (LLM + regex)
        risk_flags = detect_all_risk_flags(user_message, llm_response.internal_json)
        risk_flag_values = [f.value for f in risk_flags]

        # Tool call isimlerini cikar
        tool_calls = [
            tc["name"]
            for tc in ResponseParser.extract_tool_calls(llm_response.internal_json)
        ]

        # State'i guncelle
        new_state = llm_response.internal_json.state or current_state.value
        conversation.current_state = ConversationState(new_state)

        return {
            "intent": llm_response.internal_json.intent,
            "state": new_state,
            "tool_calls": tool_calls,
            "reply": llm_response.user_message,
            "risk_flags": risk_flag_values,
        }
