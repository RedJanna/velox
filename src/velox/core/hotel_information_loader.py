"""Loader for structured hotel information JSON datasets."""

from __future__ import annotations

from pathlib import Path

import orjson
import structlog

from velox.core.hotel_profile_loader import get_profile, load_all_profiles
from velox.models.hotel_information import HotelInformationDataset
from velox.models.hotel_profile import HotelProfile
from velox.utils.project_paths import get_project_root

logger = structlog.get_logger(__name__)

_datasets: dict[int, HotelInformationDataset] = {}
_dataset_sources: dict[int, Path] = {}


def load_hotel_information(
    hotel_id: int,
    *,
    profile: HotelProfile | None = None,
) -> HotelInformationDataset | None:
    """Load and cache the structured hotel information dataset for one hotel."""
    source_path = _resolve_dataset_source(hotel_id, profile=profile)
    if source_path is None:
        logger.info("hotel_information_source_missing", hotel_id=hotel_id)
        _datasets.pop(hotel_id, None)
        _dataset_sources.pop(hotel_id, None)
        return None

    if not source_path.exists() or not source_path.is_file():
        logger.warning(
            "hotel_information_file_not_found",
            hotel_id=hotel_id,
            path=str(source_path),
        )
        _datasets.pop(hotel_id, None)
        _dataset_sources.pop(hotel_id, None)
        return None

    try:
        raw = orjson.loads(source_path.read_bytes())
        dataset = HotelInformationDataset.model_validate(raw)
    except Exception:
        logger.exception(
            "hotel_information_load_failed",
            hotel_id=hotel_id,
            path=str(source_path),
        )
        _datasets.pop(hotel_id, None)
        _dataset_sources.pop(hotel_id, None)
        return None

    _datasets[hotel_id] = dataset
    _dataset_sources[hotel_id] = source_path
    logger.info(
        "hotel_information_loaded",
        hotel_id=hotel_id,
        version=dataset.hotel_data_version,
        count=len(dataset.hotel_information),
        path=str(source_path),
    )
    return dataset


def get_hotel_information(hotel_id: int) -> HotelInformationDataset | None:
    """Return a cached dataset, loading it from the hotel profile when needed."""
    dataset = _datasets.get(hotel_id)
    if dataset is not None:
        return dataset

    profile = get_profile(hotel_id)
    if profile is None:
        profile = load_all_profiles().get(hotel_id)
    return load_hotel_information(hotel_id, profile=profile)


def reload_hotel_information(hotel_id: int) -> HotelInformationDataset | None:
    """Reload one hotel information dataset from disk."""
    profile = get_profile(hotel_id)
    return load_hotel_information(hotel_id, profile=profile)


def get_hotel_information_source(hotel_id: int) -> Path | None:
    """Return the cached source path for one dataset."""
    return _dataset_sources.get(hotel_id)


def profile_has_hotel_information_dataset(
    hotel_id: int,
    profile: HotelProfile | None,
) -> bool:
    """Return True when a profile points at a structured hotel-information dataset."""
    if _profile_information_source(profile):
        return True
    default_source = get_project_root() / "data" / "hotel_information" / f"hotel_{hotel_id}.json"
    return default_source.exists()


def _resolve_dataset_source(
    hotel_id: int,
    *,
    profile: HotelProfile | None = None,
) -> Path | None:
    """Resolve the JSON source path from HOTEL_PROFILE extras or default layout."""
    profile = profile or get_profile(hotel_id)
    configured_source = _profile_information_source(profile)
    if configured_source:
        return _resolve_project_path(configured_source)

    default_source = get_project_root() / "data" / "hotel_information" / f"hotel_{hotel_id}.json"
    return default_source if default_source.exists() else None


def _profile_information_source(profile: HotelProfile | None) -> str:
    """Read optional hotel_information_source from model extras."""
    if profile is None:
        return ""
    extras = profile.model_extra if isinstance(profile.model_extra, dict) else {}
    configured_source = extras.get("hotel_information_source")
    return str(configured_source or "").strip()


def _resolve_project_path(value: str) -> Path:
    """Resolve absolute or project-relative dataset paths."""
    path = Path(value)
    if path.is_absolute():
        return path
    return (get_project_root() / path).resolve()
