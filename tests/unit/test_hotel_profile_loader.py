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


def test_cache_profile_definition_keeps_dynamic_admin_fields() -> None:
    profile_payload = {
        "hotel_id": 9010,
        "hotel_name": {"tr": "Dinamik Otel", "en": "Dynamic Hotel"},
        "location": {"city": "Mugla", "google_maps_restaurant": "https://maps.example"},
        "highlights": ["central_location", "beachside"],
        "contacts": {
            "restaurant": {
                "phone": "+905550000111",
                "name": "Restoran",
                "role": "RESTAURANT",
            }
        },
    }
    hotel_profile_loader._profiles.clear()
    hotel_profile_loader._profile_sources.clear()

    hotel_profile_loader.cache_profile_definition(profile_payload)

    cached = hotel_profile_loader.get_profile(9010)
    assert cached is not None
    dumped = cached.model_dump()
    assert dumped["location"]["city"] == "Mugla"
    assert dumped["contacts"]["restaurant"]["role"] == "RESTAURANT"


def test_save_profile_definition_succeeds_even_if_other_yaml_is_invalid(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(hotel_profile_loader.settings, "hotel_profiles_dir", str(profiles_dir))
    hotel_profile_loader._profiles.clear()
    hotel_profile_loader._profile_sources.clear()

    # Simulate a broken/unrelated YAML file in the same folder.
    (profiles_dir / "broken.yaml").write_text("foo: [unclosed", encoding="utf-8")

    profile_payload = {
        "hotel_id": 9020,
        "hotel_name": {"tr": "Yedek Otel", "en": "Backup Hotel"},
        "currency_base": "EUR",
    }

    saved_path = hotel_profile_loader.save_profile_definition(profile_payload)

    assert saved_path == profiles_dir / "backup_hotel.yaml"
    assert saved_path.exists()
    cached = hotel_profile_loader.get_profile(9020)
    assert cached is not None
    assert cached.hotel_name.en == "Backup Hotel"
