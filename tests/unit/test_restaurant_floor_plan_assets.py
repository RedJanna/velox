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

    assert layout.tables[0].rotation == 0
    assert layout.shapes[0].rotation == 0


def test_restaurant_editor_exposes_new_floor_plan_tools() -> None:
    html = render_admin_panel_html()

    assert "Yuvarlak Duvar" in html
    assert "Agac" in html
    assert "Cali" in html
    assert "Duvarlari uzatip kisaltabilir" in html


def test_restaurant_assets_support_shape_rotation_resize_and_non_drag_actions() -> None:
    assert "CURVED_WALL" in ADMIN_RESTAURANT_SCRIPT
    assert "shape-resize-handle" in ADMIN_RESTAURANT_SCRIPT
    assert "makeShapeResizable" in ADMIN_RESTAURANT_SCRIPT
    assert "TREE" in ADMIN_RESTAURANT_SCRIPT
    assert "BUSH" in ADMIN_RESTAURANT_SCRIPT
    assert "setSelectedElement" in ADMIN_RESTAURANT_SCRIPT
    assert "e.target.closest('.shape-act-btn')" in ADMIN_RESTAURANT_SCRIPT
    assert "e.target.closest('.shape-resize-handle')" in ADMIN_RESTAURANT_SCRIPT
    assert ".canvas-shape .shape-actions{top:-30px;right:0}" in ADMIN_RESTAURANT_STYLE
