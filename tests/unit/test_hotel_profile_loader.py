"""Unit tests for hotel profile persistence helpers."""

from pathlib import Path

import yaml

from velox.core import hotel_profile_loader


def test_save_profile_definition_persists_yaml_and_refreshes_cache(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile_payload = {
        "hotel_id": 9001,
        "hotel_name": {"tr": "Deneme Otel", "en": "Demo Hotel"},
        "currency_base": "EUR",
        "contacts": {"reception": {"phone": "+905550000000", "email": "ops@example.com", "hours": "24/7"}},
    }
    profiles_dir = tmp_path / "profiles"
    monkeypatch.setattr(hotel_profile_loader.settings, "hotel_profiles_dir", str(profiles_dir))
    hotel_profile_loader._profiles.clear()
    hotel_profile_loader._profile_sources.clear()

    saved_path = hotel_profile_loader.save_profile_definition(profile_payload)

    assert saved_path == profiles_dir / "demo_hotel.yaml"
    assert saved_path.exists()
    saved_raw = yaml.safe_load(saved_path.read_text(encoding="utf-8"))
    assert saved_raw["hotel_id"] == 9001
    assert hotel_profile_loader.get_profile(9001) is not None
