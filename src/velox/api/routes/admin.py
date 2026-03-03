"""Admin API routes for configuration management."""

from fastapi import APIRouter

from velox.core.hotel_profile_loader import reload_profiles
from velox.core.template_engine import reload_templates
from velox.escalation.matrix import reload_matrix

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reload-config")
async def reload_config() -> dict[str, object]:
    """Reload all configuration from disk."""
    profiles = reload_profiles()
    matrix = reload_matrix()
    templates = reload_templates()

    return {
        "reloaded": True,
        "profiles_count": len(profiles),
        "matrix_entries_count": len(matrix),
        "templates_count": len(templates),
    }
