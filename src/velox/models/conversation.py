"""Conversation and Message data models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from velox.config.constants import ConversationState, Intent


class Message(BaseModel):
    id: UUID | None = None
    conversation_id: UUID
    role: str  # user, assistant, system
    content: str
    client_message_id: str | None = None
    internal_json: dict | None = None
    tool_calls: list[dict] | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    id: UUID | None = None
    hotel_id: int
    phone_hash: str
    phone_display: str | None = None
    language: str = "tr"
    current_state: ConversationState = ConversationState.GREETING
    current_intent: Intent | None = None
    entities_json: dict = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)
    is_active: bool = True
    last_message_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    messages: list[Message] = Field(default_factory=list)


class InternalJSON(BaseModel):
    """Structured INTERNAL_JSON output from LLM."""
    language: str = "tr"
    intent: str = ""
    state: str = ""
    entities: dict = Field(default_factory=dict)
    required_questions: list[str] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list)
    notifications: list[dict] = Field(default_factory=list)
    handoff: dict = Field(default_factory=lambda: {"needed": False})
    risk_flags: list[str] = Field(default_factory=list)
    escalation: dict = Field(default_factory=lambda: {"level": "L0", "route_to_role": "NONE"})
    next_step: str = ""


class LLMResponse(BaseModel):
    """Parsed LLM response with both parts."""
    user_message: str
    internal_json: InternalJSON
