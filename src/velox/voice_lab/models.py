"""Pydantic models for Voice Lab scenario evaluation."""

from enum import StrEnum

from pydantic import BaseModel, Field


class VoiceLabSource(StrEnum):
    """Allowed evidence sources for a Voice Lab response."""

    HOTEL_PROFILE = "HOTEL_PROFILE"
    TOOL = "TOOL"
    HANDOFF = "HANDOFF"
    UNKNOWN = "UNKNOWN"


class VoiceLabAction(StrEnum):
    """Expected action after intent detection."""

    ANSWER = "answer"
    TOOL_REQUIRED = "tool_required"
    HANDOFF = "handoff"
    CLARIFY = "clarify"


class VoiceLabResult(StrEnum):
    """Scenario evaluation result."""

    PASS = "PASS"  # noqa: S105 - scenario status value, not a secret
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class VoiceLabScenario(BaseModel):
    """A deterministic test scenario for the phone assistant."""

    scenario_id: str
    sample_input: str
    expected_intent: str
    expected_source: VoiceLabSource
    expected_action: VoiceLabAction
    language: str = "tr"
    topic: str | None = None
    required_tool: str | None = None
    acceptance_terms: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)


class VoiceLabRunRequest(BaseModel):
    """Input payload for one Voice Lab text run."""

    hotel_id: int
    transcript: str
    language: str = "tr"
    scenario_id: str | None = None


class VoiceLabRunResult(BaseModel):
    """Evaluation output for one Voice Lab run."""

    hotel_id: int
    scenario_id: str | None
    input_transcript: str
    normalized_text: str
    language_detected: str
    intent: str
    source_type: VoiceLabSource
    source_detail: str
    action: VoiceLabAction
    tool_required: bool
    tool_called: bool
    tool_name: str | None
    handoff_required: bool
    risk_flags: list[str] = Field(default_factory=list)
    response_text: str
    result: VoiceLabResult
    violations: list[str] = Field(default_factory=list)
    match_score: float = 0.0
    latency_ms: dict[str, int] = Field(default_factory=dict)
