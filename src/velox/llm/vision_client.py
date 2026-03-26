"""OpenAI vision analysis helper for inbound guest images."""

from __future__ import annotations

import base64
import re
from typing import Any, cast

import orjson
import structlog
from openai import AsyncOpenAI

from velox.config.settings import settings
from velox.models.media import VisionAnalysisResult

logger = structlog.get_logger(__name__)

VISION_TIMEOUT_SECONDS = 25.0
VISION_MODEL = "gpt-4o-mini"
_FIXED_TEMPERATURE_MODEL_PREFIXES = ("o1", "o3", "gpt-5")

_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", flags=re.DOTALL)


class VisionClient:
    """Small wrapper around OpenAI multimodal input for image analysis."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = VISION_MODEL

    async def close(self) -> None:
        """Close underlying HTTP resources."""
        await self._client.close()

    async def analyze_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        caption: str,
        language: str,
    ) -> VisionAnalysisResult:
        """Analyze one image and return a normalized structured result."""
        safe_language = language.lower() if language else "tr"
        data_url = self._build_data_url(image_bytes=image_bytes, mime_type=mime_type)
        content = [
            {
                "type": "text",
                "text": (
                    "Analyze this hotel guest image for operations routing.\n"
                    "Return STRICT JSON with exactly these keys:\n"
                    "intent, confidence, summary, detected_text, risk_flags, requires_handoff.\n"
                    "intent must be one of: room_issue_photo, payment_proof_photo, general_photo_info.\n"
                    "confidence must be a number 0..1.\n"
                    "summary max 240 chars.\n"
                    "detected_text max 240 chars.\n"
                    "risk_flags must be array of strings.\n"
                    "requires_handoff must be boolean.\n"
                    "If uncertain, set lower confidence and intent=general_photo_info.\n"
                    f"guest_language={safe_language}\n"
                    f"caption={caption[:400]}"
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": data_url},
            },
        ]
        call_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": content}],
            "timeout": VISION_TIMEOUT_SECONDS,
        }
        is_fixed_temp = any(self._model.startswith(prefix) for prefix in _FIXED_TEMPERATURE_MODEL_PREFIXES)
        if not is_fixed_temp:
            call_kwargs["temperature"] = 0.2

        response = await self._client.chat.completions.create(**call_kwargs)
        response_dict = response.model_dump()
        raw_content = str(
            response_dict.get("choices", [{}])[0].get("message", {}).get("content") or ""
        ).strip()
        parsed = self._extract_json(raw_content)
        if parsed is None:
            logger.warning("vision_json_parse_failed")
            return VisionAnalysisResult(
                intent="general_photo_info",
                confidence=0.0,
                summary="",
                detected_text="",
                risk_flags=["TOOL_UNAVAILABLE"],
                requires_handoff=True,
            )

        return VisionAnalysisResult(
            intent=self._normalize_intent(str(parsed.get("intent") or "")),
            confidence=self._normalize_confidence(parsed.get("confidence")),
            summary=str(parsed.get("summary") or "")[:240],
            detected_text=str(parsed.get("detected_text") or "")[:240],
            risk_flags=[str(item) for item in parsed.get("risk_flags", []) if str(item).strip()],
            requires_handoff=bool(parsed.get("requires_handoff", False)),
        )

    @staticmethod
    def _build_data_url(*, image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        safe_mime = mime_type or "image/jpeg"
        return f"data:{safe_mime};base64,{encoded}"

    @staticmethod
    def _extract_json(raw_content: str) -> dict[str, Any] | None:
        if not raw_content:
            return None
        match = _JSON_OBJECT_PATTERN.search(raw_content)
        candidate = match.group(0) if match else raw_content
        try:
            loaded = orjson.loads(candidate)
        except orjson.JSONDecodeError:
            return None
        if not isinstance(loaded, dict):
            return None
        return cast(dict[str, Any], loaded)

    @staticmethod
    def _normalize_intent(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"room_issue_photo", "payment_proof_photo", "general_photo_info"}:
            return normalized
        return "general_photo_info"

    @staticmethod
    def _normalize_confidence(raw_value: Any) -> float:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return 0.0
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value


_vision_client: VisionClient | None = None


def get_vision_client() -> VisionClient:
    """Return singleton vision client."""
    global _vision_client
    if _vision_client is None:
        _vision_client = VisionClient()
    return _vision_client


async def close_vision_client() -> None:
    """Close singleton vision client."""
    global _vision_client
    if _vision_client is not None:
        await _vision_client.close()
        _vision_client = None

