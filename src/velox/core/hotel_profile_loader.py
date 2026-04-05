"""Hotel profile loader — loads YAML files and parses into HotelProfile models."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import structlog
import yaml

from velox.config.settings import settings
from velox.models.hotel_profile import HotelProfile

logger = structlog.get_logger(__name__)

_profiles: dict[int, HotelProfile] = {}
_profile_sources: dict[int, Path] = {}


def load_all_profiles() -> dict[int, HotelProfile]:
    """Load all hotel profile YAML files from the configured directory."""
    global _profiles
    _profiles.clear()
    _profile_sources.clear()

    profiles_dir = Path(settings.hotel_profiles_dir)
    if not profiles_dir.exists():
        logger.warning("hotel_profiles_dir_not_found", path=str(profiles_dir))
        return _profiles

    yaml_files = list(profiles_dir.glob("*.yaml")) + list(profiles_dir.glob("*.yml"))
    logger.info("hotel_profiles_loading", count=len(yaml_files), directory=str(profiles_dir))

    for yaml_file in yaml_files:
        try:
            with yaml_file.open(encoding="utf-8") as file_obj:
                raw = yaml.safe_load(file_obj)

            if raw is None:
                logger.warning("hotel_profile_empty_yaml_skipped", file=str(yaml_file))
                continue

            profile = HotelProfile(**raw)
            _profiles[profile.hotel_id] = profile
            _profile_sources[profile.hotel_id] = yaml_file
            logger.info(
                "hotel_profile_loaded",
                hotel_id=profile.hotel_id,
                hotel_name=profile.hotel_name.en,
                file=yaml_file.name,
            )
        except Exception:
            logger.exception("hotel_profile_load_failed", file=str(yaml_file))

    return _profiles


def get_profile(hotel_id: int) -> HotelProfile | None:
    """Get a cached hotel profile by hotel_id."""
    return _profiles.get(hotel_id)


def get_all_profiles() -> dict[int, HotelProfile]:
    """Get all cached hotel profiles."""
    return _profiles.copy()


def reload_profiles() -> dict[int, HotelProfile]:
    """Reload all profiles from disk."""
    logger.info("hotel_profiles_reloading")
    return load_all_profiles()


def cache_profile_definition(
    profile_data: dict[str, Any],
    *,
    source_path: Path | None = None,
) -> HotelProfile:
    """Update in-memory profile cache from payload without requiring disk reload."""
    validated = HotelProfile.model_validate(profile_data)
    _profiles[validated.hotel_id] = validated
    if source_path is not None:
        _profile_sources[validated.hotel_id] = source_path
    return validated


def save_profile_definition(profile_data: dict[str, Any]) -> Path:
    """Persist one hotel profile payload to YAML and refresh in-memory cache."""
    validated = HotelProfile.model_validate(profile_data)
    hotel_id = validated.hotel_id
    target_path = _profile_sources.get(hotel_id) or _build_profile_path(validated)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("w", encoding="utf-8") as file_obj:
        yaml.safe_dump(
            profile_data,
            file_obj,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    _profile_sources[hotel_id] = target_path
    reload_profiles()
    return target_path


def _build_profile_path(profile: HotelProfile) -> Path:
    """Resolve the file path for a hotel profile."""
    base_name = profile.hotel_name.en or profile.hotel_name.tr or f"hotel_{profile.hotel_id}"
    slug = _slugify(base_name)
    profiles_dir = Path(settings.hotel_profiles_dir)
    return profiles_dir / f"{slug}.yaml"


def _slugify(value: str) -> str:
    """Create a filesystem-safe ASCII slug."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    compact = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return compact or "hotel_profile"
