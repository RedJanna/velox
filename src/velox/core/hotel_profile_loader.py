"""Hotel profile loader — loads YAML files and parses into HotelProfile models."""

from pathlib import Path

import structlog
import yaml

from velox.config.settings import settings
from velox.models.hotel_profile import HotelProfile

logger = structlog.get_logger(__name__)

_profiles: dict[int, HotelProfile] = {}


def load_all_profiles() -> dict[int, HotelProfile]:
    """Load all hotel profile YAML files from the configured directory."""
    global _profiles
    _profiles.clear()

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
