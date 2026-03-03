"""Escalation and risk flag data models."""

from pydantic import BaseModel, Field

from velox.config.constants import EscalationLevel, Role, TicketPriority


class EscalationMatrixEntry(BaseModel):
    risk_flag: str
    level: EscalationLevel
    route_to_role: Role
    priority: TicketPriority
    action: list[str] = Field(default_factory=list)  # ["notify.send", "handoff.create_ticket"]
    notify_channel: str = "panel"
    user_message_style: str = "calm_premium"
    reason_hint: str = ""


class EscalationResult(BaseModel):
    level: EscalationLevel = EscalationLevel.L0
    route_to_role: Role = Role.NONE
    dedupe_key: str = ""
    reason: str = ""
    sla_hint: str = "low"
    actions: list[str] = Field(default_factory=list)
    risk_flags_matched: list[str] = Field(default_factory=list)
