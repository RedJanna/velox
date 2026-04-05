"""Unit tests for room service menu catalogue extraction."""

from types import SimpleNamespace

from velox.tools.room_service import _get_menu_catalogue


def test_get_menu_catalogue_reads_nested_menu_documents() -> None:
    profile = SimpleNamespace(
        restaurant={
            "menu": {
                "documents": {
                    "alacarte": [
                        {"name": "Soup of the day", "price_text": "8 EUR"},
                        {"name_tr": "Izgara Somon", "name_en": "Grilled Salmon"},
                    ],
                    "wines": [
                        {"title": "House Red"},
                    ],
                }
            }
        }
    )

    catalogue = _get_menu_catalogue(profile)

    assert "soup of the day" in catalogue
    assert "izgara somon" in catalogue
    assert "grilled salmon" in catalogue
    assert "house red" in catalogue

