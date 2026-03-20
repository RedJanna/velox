"""Unit tests for restaurant floor plan editor assets and models."""

from velox.api.routes.admin_panel_restaurant_assets import ADMIN_RESTAURANT_SCRIPT, ADMIN_RESTAURANT_STYLE
from velox.api.routes.admin_panel_ui import render_admin_panel_html
from velox.models.restaurant import FloorPlanLayout


def test_floor_plan_layout_accepts_legacy_shape_items_without_rotation() -> None:
    layout = FloorPlanLayout.model_validate(
        {
            "tables": [
                {
                    "table_id": "T4-1",
                    "type": "TABLE_4",
                    "capacity": 4,
                    "x": 120,
                    "y": 200,
                }
            ],
            "shapes": [
                {
                    "shape_id": "S-1",
                    "type": "WALL",
                    "x": 40,
                    "y": 60,
                    "width": 160,
                    "height": 8,
                }
            ],
        }
    )

    assert layout.floor_theme == "CREAM_MARBLE_CLASSIC"
    assert layout.tables[0].rotation == 0
    assert layout.shapes[0].rotation == 0


def test_restaurant_editor_exposes_new_floor_plan_tools() -> None:
    html = render_admin_panel_html()

    assert "Yuvarlak Duvar" in html
    assert "Agac" in html
    assert "Cali" in html
    assert "Duvarlari uzatip kisaltabilir" in html


def test_restaurant_assets_support_flexible_shape_editing_controls() -> None:
    assert "CURVED_WALL" in ADMIN_RESTAURANT_SCRIPT
    assert "shape-resize-handle" in ADMIN_RESTAURANT_SCRIPT
    assert "shape-act-btn edit" in ADMIN_RESTAURANT_SCRIPT
    assert "setActiveShapeEdit" in ADMIN_RESTAURANT_SCRIPT
    assert "syncShapeEditState" in ADMIN_RESTAURANT_SCRIPT
    assert "HORIZONTAL_DIVIDER" in ADMIN_RESTAURANT_SCRIPT
    assert "VERTICAL_DIVIDER" in ADMIN_RESTAURANT_SCRIPT
    assert "TREE" in ADMIN_RESTAURANT_SCRIPT
    assert "BUSH" in ADMIN_RESTAURANT_SCRIPT
    assert "FLOOR_THEMES" in ADMIN_RESTAURANT_SCRIPT
    assert "applyFloorTheme" in ADMIN_RESTAURANT_SCRIPT
    assert "floor_theme" in ADMIN_RESTAURANT_SCRIPT
    assert "normalizedRotation === 90 || normalizedRotation === 270" in ADMIN_RESTAURANT_SCRIPT
    assert "e.target.closest('.shape-act-btn')" in ADMIN_RESTAURANT_SCRIPT
    assert "e.target.closest('.shape-resize-handle')" in ADMIN_RESTAURANT_SCRIPT
    assert ".canvas-shape.shape-editing .shape-actions" in ADMIN_RESTAURANT_STYLE
    assert ".shape-resize-handle::before" in ADMIN_RESTAURANT_STYLE
    assert ".floor-plan-canvas.floor-cream-marble-classic" in ADMIN_RESTAURANT_STYLE
    assert ".fp-floor-select" in ADMIN_RESTAURANT_STYLE
    assert ".canvas-shape.shape-compact .shape-actions{top:calc(100% + 10px);right:auto;left:50%;transform:translateX(-50%)}" in ADMIN_RESTAURANT_STYLE


def test_restaurant_editor_exposes_cream_marble_floor_options() -> None:
    html = render_admin_panel_html()

    assert "fpFloorTheme" in html
    assert "Krem Mermer - Klasik" in html
    assert "Krem Mermer - Sicak Ton" in html
    assert "Krem Mermer - Yumusayak Doku" in html
