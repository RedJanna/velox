"""Velox (NexlumeAI) — FastAPI Application Entry Point."""

import asyncio
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from time import perf_counter
from typing import cast

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from redis.asyncio.client import Redis
from starlette.middleware.trustedhost import TrustedHostMiddleware

from velox.adapters.elektraweb.client import close_elektraweb_client
from velox.adapters.whatsapp.client import close_whatsapp_client
from velox.api.middleware.rate_limiter import RateLimitMiddleware
from velox.api.routes import (
    admin,
    admin_holds,
    admin_panel_ui,
    admin_portal,
    admin_session,
    admin_webhook,
    health,
    test_chat,
    whatsapp_webhook,
)
from velox.config.constants import (
    MAX_STARTUP_RETRIES,
    RESTAURANT_NOSHOW_CHECK_INTERVAL_SECONDS,
    STARTUP_DEPENDENCY_TIMEOUT_SECONDS,
    STARTUP_RETRY_BACKOFF_SECONDS,
)
from velox.config.settings import settings
from velox.core.event_processor import EventProcessor
from velox.core.hotel_profile_loader import load_all_profiles
from velox.core.pipeline import post_process_escalation
from velox.core.template_engine import load_templates
from velox.db.database import close_db_pool, init_db_pool
from velox.db.migrate import apply_pending_migrations
from velox.db.repositories.hotel import HotelRepository
from velox.db.repositories.restaurant_floor_plan import RestaurantStatusManager
from velox.db.repositories.whatsapp_number import WhatsAppNumberRepository
from velox.escalation.engine import EscalationEngine
from velox.escalation.matrix import load_escalation_matrix
from velox.llm.client import close_llm_client
from velox.llm.transcription_client import close_transcription_client
from velox.llm.vision_client import close_vision_client
from velox.tools import initialize_tool_dispatcher
from velox.utils.logger import setup_logging

logger = structlog.get_logger(__name__)


async def _connect_redis_with_retry() -> Redis | None:
    """Connect to Redis with bounded retries and degrade cleanly if unavailable."""
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    for attempt in range(1, MAX_STARTUP_RETRIES + 1):
        started = perf_counter()
        try:
            async with asyncio.timeout(STARTUP_DEPENDENCY_TIMEOUT_SECONDS):
                pong = await cast(Awaitable[bool], redis_client.ping())
            if not pong:
                raise RuntimeError("redis_ping_failed")
            logger.info(
                "redis_connected",
                attempt_number=attempt,
                duration_ms=int((perf_counter() - started) * 1000),
            )
            return redis_client
        except Exception as exc:
            logger.warning(
                "redis_connection_failed",
                attempt_number=attempt,
                duration_ms=int((perf_counter() - started) * 1000),
                error_type=type(exc).__name__,
            )
            if attempt >= MAX_STARTUP_RETRIES:
                break
            backoff = STARTUP_RETRY_BACKOFF_SECONDS[min(attempt - 1, len(STARTUP_RETRY_BACKOFF_SECONDS) - 1)]
            await asyncio.sleep(backoff)

    await redis_client.aclose()
    logger.warning("redis_startup_degraded", max_attempts=MAX_STARTUP_RETRIES)
    return None


async def _noshow_background_loop(hotel_ids: list[int]) -> None:
    """Periodically check for no-show reservations and auto-mark GELMEDI."""
    status_mgr = RestaurantStatusManager()
    while True:
        try:
            await asyncio.sleep(RESTAURANT_NOSHOW_CHECK_INTERVAL_SECONDS)
            for hid in hotel_ids:
                try:
                    count = await status_mgr.process_no_shows(hid)
                    if count:
                        logger.info("noshow_processed", hotel_id=hid, count=count)
                except Exception:
                    logger.exception("noshow_check_error", hotel_id=hid)
        except asyncio.CancelledError:
            logger.info("noshow_background_loop_cancelled")
            return
        except Exception:
            logger.exception("noshow_loop_unexpected_error")
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    setup_logging(settings.app_log_level)
    logger.info("application_startup", env=settings.app_env)
    db_pool = await init_db_pool()
    _app.state.db_pool = db_pool
    _app.state.migration_status = await apply_pending_migrations(db_pool)
    _app.state.redis = await _connect_redis_with_retry()

    profiles = load_all_profiles()
    logger.info("hotel_profiles_loaded", count=len(profiles))

    hotel_repository = HotelRepository()
    whatsapp_number_repository = WhatsAppNumberRepository()
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

    if settings.whatsapp_phone_number_id:
        fallback_profile = profiles.get(settings.elektra_hotel_id)
        fallback_display_phone = fallback_profile.whatsapp_number if fallback_profile is not None else None
        await whatsapp_number_repository.upsert_mapping(
            hotel_id=settings.elektra_hotel_id,
            phone_number_id=settings.whatsapp_phone_number_id,
            display_phone_number=fallback_display_phone,
            is_active=True,
        )
        logger.info(
            "whatsapp_number_mapping_synced",
            hotel_id=settings.elektra_hotel_id,
            phone_number_id=settings.whatsapp_phone_number_id,
        )
    else:
        logger.warning("whatsapp_phone_number_id_missing_mapping_not_seeded")

    matrix = load_escalation_matrix()
    logger.info("escalation_matrix_loaded", count=len(matrix))
    escalation_engine = EscalationEngine()
    escalation_engine.load_matrix()
    _app.state.escalation_engine = escalation_engine

    templates = load_templates()
    logger.info("templates_loaded", count=len(templates))
    dispatcher = initialize_tool_dispatcher()
    _app.state.tool_dispatcher = dispatcher
    _app.state.event_processor = EventProcessor(db_pool=db_pool, dispatcher=dispatcher)
    _app.state.post_process_escalation = post_process_escalation
    logger.info("tools_registered", count=len(dispatcher.registered_names()))

    # Start no-show background checker for all loaded hotels
    noshow_task = asyncio.create_task(
        _noshow_background_loop(list(profiles.keys())),
        name="restaurant_noshow_checker",
    )

    yield

    # Cancel the no-show background task
    noshow_task.cancel()
    try:
        await noshow_task
    except asyncio.CancelledError:
        pass
    await close_db_pool()
    await close_elektraweb_client()
    await close_whatsapp_client()
    await close_llm_client()
    await close_transcription_client()
    await close_vision_client()
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
if settings.app_env == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(RateLimitMiddleware)
app.include_router(health.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(admin_holds.router, prefix="/api/v1")
app.include_router(admin_portal.router, prefix="/api/v1")
app.include_router(admin_session.router, prefix="/api/v1")
app.include_router(whatsapp_webhook.router, prefix="/api/v1")
app.include_router(admin_webhook.router, prefix="/api/v1")
app.include_router(admin_panel_ui.router)
app.include_router(test_chat.router, prefix="/api/v1")
app.include_router(test_chat.ui_router)


@app.get("/", response_model=None)
async def root(request: Request) -> JSONResponse | RedirectResponse:
    """Return service status for API clients and redirect browsers to the admin panel."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url=settings.admin_panel_path, status_code=307)
    return JSONResponse(content={"service": "velox", "status": "running"})
