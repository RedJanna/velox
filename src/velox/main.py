"""Velox (NexlumeAI) — FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
import redis.asyncio as redis
import structlog

from velox.adapters.elektraweb.client import close_elektraweb_client
from velox.adapters.whatsapp.client import close_whatsapp_client
from velox.api.middleware.rate_limiter import RateLimitMiddleware
from velox.api.routes import admin, health, whatsapp_webhook
from velox.config.settings import settings
from velox.core.pipeline import post_process_escalation
from velox.core.hotel_profile_loader import load_all_profiles
from velox.core.template_engine import load_templates
from velox.db.database import close_db_pool, init_db_pool
from velox.db.repositories.hotel import HotelRepository
from velox.escalation.engine import EscalationEngine
from velox.escalation.matrix import load_escalation_matrix
from velox.llm.client import close_llm_client
from velox.tools import initialize_tool_dispatcher
from velox.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    setup_logging()
    logger.info("application_startup", env=settings.app_env)
    db_pool = await init_db_pool()
    _app.state.db_pool = db_pool
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis_client.ping()
        _app.state.redis = redis_client
        logger.info("redis_connected")
    except Exception:
        _app.state.redis = None
        logger.exception("redis_connection_failed")

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
    escalation_engine = EscalationEngine()
    escalation_engine.load_matrix()
    _app.state.escalation_engine = escalation_engine

    templates = load_templates()
    logger.info("templates_loaded", count=len(templates))
    dispatcher = initialize_tool_dispatcher()
    _app.state.tool_dispatcher = dispatcher
    _app.state.post_process_escalation = post_process_escalation
    logger.info("tools_registered", count=len(dispatcher.registered_names()))

    yield
    await close_db_pool()
    await close_elektraweb_client()
    await close_whatsapp_client()
    await close_llm_client()
    redis_state = getattr(_app.state, "redis", None)
    if redis_state is not None:
        await redis_state.aclose()
    logger.info("application_shutdown")


app = FastAPI(
    title="Velox (NexlumeAI)",
    description="WhatsApp AI Receptionist for Hotels",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(RateLimitMiddleware)

# TODO: Include routers
# from velox.api.routes import whatsapp_webhook, admin_webhook, admin
app.include_router(health.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(whatsapp_webhook.router, prefix="/api/v1")
# app.include_router(admin_webhook.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Return service status for root endpoint."""
    return {"service": "velox", "status": "running"}
