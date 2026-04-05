"""Shared helpers for hotel season window validation in reservation tools."""

from __future__ import annotations

import datetime as _dt
from collections.abc import Iterable
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def _season_window(profile: Any, *, year: int, invalid_event: str) -> tuple[_dt.date, _dt.date] | None:
    """Return configured season bounds for the target year when available."""
    season = getattr(profile, "season", None)
    if not isinstance(season, dict):
        return None

    open_value = str(season.get("open") or "").strip()
    close_value = str(season.get("close") or "").strip()
    if not open_value or not close_value:
        return None

    try:
        open_month, open_day = (int(part) for part in open_value.split("-", maxsplit=1))
        close_month, close_day = (int(part) for part in close_value.split("-", maxsplit=1))
        return _dt.date(year, open_month, open_day), _dt.date(year, close_month, close_day)
    except (TypeError, ValueError):
        logger.warning(
            invalid_event,
            season_open=open_value,
            season_close=close_value,
        )
        return None


def is_within_hotel_season(profile: Any, target_date: _dt.date, *, invalid_event: str) -> bool:
    """Check whether a date falls inside configured season bounds."""
    bounds = _season_window(profile, year=target_date.year, invalid_event=invalid_event)
    if bounds is None:
        return True

    open_date, close_date = bounds
    if open_date <= close_date:
        return open_date <= target_date <= close_date
    return target_date >= open_date or target_date <= close_date


def are_dates_within_hotel_season(profile: Any, dates: Iterable[_dt.date], *, invalid_event: str) -> bool:
    """Return True when every supplied date is inside the configured season window."""
    return all(is_within_hotel_season(profile, target_date, invalid_event=invalid_event) for target_date in dates)


def out_of_season_response(profile: Any) -> dict[str, Any]:
    """Return a normalized out-of-season payload for reservation tools."""
    season = getattr(profile, "season", {}) if profile is not None else {}
    return {
        "available": False,
        "reason": "OUT_OF_SEASON",
        "suggestion": "request_valid_date",
        "season": {
            "open": str(season.get("open") or ""),
            "close": str(season.get("close") or ""),
        },
    }
