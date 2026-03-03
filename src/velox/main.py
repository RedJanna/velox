"""Velox (NexlumeAI) — FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
import structlog

from velox.adapters.elektraweb.client import close_elektraweb_client
from velox.api.routes import admin, health
from velox.config.settings import settings
from velox.core.hotel_profile_loader import load_all_profiles
from velox.core.template_engine import load_templates
from velox.db.database import close_db_pool, init_db_pool
from velox.db.repositories.hotel import HotelRepository
from velox.escalation.matrix import load_escalation_matrix
from velox.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    setup_logging()
    logger.info("application_startup", env=settings.app_env)
    await init_db_pool()
    # TODO: Initialize Redis connection

    profiles = load_all_profiles()
    logger.info("hotel_profiles_loaded", count=len(profiles))

    hotel_repository = HotelRepository()
    for hotel_id, profile in profiles.items():
        await hotel_repository.upsert(
            hotel_id=profile.hotel_id,
            name_tr=profile.hotel_name.tr,
            name_en=profile.hotel_name.en,
            profile_json=profile.model_dump(),
            hotel_type=profile.hotel_type,
            timezone=profile.timezone,
            currency_base=profile.currency_base,
            pms=profile.pms,
            whatsapp_number=profile.whatsapp_number,
            season_open=profile.season.get("open"),
            season_close=profile.season.get("close"),
        )
        logger.info("hotel_synced_to_db", hotel_id=hotel_id)

    matrix = load_escalation_matrix()
    logger.info("escalation_matrix_loaded", count=len(matrix))

    templates = load_templates()
    logger.info("templates_loaded", count=len(templates))

    yield
    await close_db_pool()
    await close_elektraweb_client()
    logger.info("application_shutdown")
    # TODO: Close Redis connection


app = FastAPI(
    title="Velox (NexlumeAI)",
    description="WhatsApp AI Receptionist for Hotels",
    version="0.1.0",
    lifespan=lifespan,
)

# TODO: Include routers
# from velox.api.routes import whatsapp_webhook, admin_webhook, admin
app.include_router(health.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
# app.include_router(whatsapp_webhook.router, prefix="/api/v1")
# app.include_router(admin_webhook.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Return service status for root endpoint."""
    return {"service": "velox", "status": "running"}
