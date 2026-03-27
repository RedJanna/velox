"""Models for inbound WhatsApp media analysis."""

from typing import Any

from pydantic import BaseModel, Field


class InboundMediaItem(BaseModel):
    """One incoming media reference extracted from WhatsApp payload."""

    media_id: str
    media_type: str
    mime_type: str = ""
    sha256: str = ""
    caption: str = ""
    whatsapp_message_id: str = ""


class VisionAnalysisResult(BaseModel):
    """Structured output produced by the vision analysis layer."""

    intent: str = "general_photo_info"
    confidence: float = 0.0
    summary: str = ""
    detected_text: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    requires_handoff: bool = False


class AudioTranscriptionResult(BaseModel):
    """Structured output produced by the audio transcription layer."""

    text: str = ""
    language: str = ""
    duration_seconds: float = 0.0
    confidence: float = 0.0
    model_name: str = ""
    mime_type: str = ""
    raw_json: dict[str, Any] = Field(default_factory=dict)

