"""Shared helpers for per-hotel conversation idle-reset policy."""

from __future__ import annotations

from velox.core.hotel_profile_loader import get_profile
from velox.models.hotel_profile import ConversationIdleResetConfig


def get_idle_reset_config(hotel_id: int) -> ConversationIdleResetConfig:
    """Return the configured idle-reset policy for a hotel."""
    profile = get_profile(hotel_id)
    if profile is not None:
        return profile.conversation_idle_reset
    return ConversationIdleResetConfig()


def get_idle_close_threshold_seconds(hotel_id: int) -> int:
    """Return close threshold in seconds for a hotel."""
    config = get_idle_reset_config(hotel_id)
    return max(0, int(config.idle_timeout_minutes) * 60)


def get_idle_warning_threshold_seconds(hotel_id: int) -> int:
    """Return warning threshold in seconds for a hotel."""
    config = get_idle_reset_config(hotel_id)
    return max(0, int(config.idle_timeout_minutes - config.warning_before_minutes) * 60)


def render_idle_reset_message(
    config: ConversationIdleResetConfig,
    language: str,
    kind: str,
) -> str:
    """Render the configured warning/closed message for the target language."""
    lang = language.casefold()[:2] if language else "tr"
    if kind == "warning":
        template = config.warning_message_en if lang == "en" else config.warning_message_tr
        return (
            template
            .replace("{minutes_remaining}", str(int(config.warning_before_minutes)))
            .replace("{idle_timeout_minutes}", str(int(config.idle_timeout_minutes)))
        )

    template = config.closed_message_en if lang == "en" else config.closed_message_tr
    return template.replace("{idle_timeout_minutes}", str(int(config.idle_timeout_minutes)))
