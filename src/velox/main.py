"""Velox (NexlumeAI) — FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
import structlog

from velox.api.routes import health
from velox.config.settings import settings
from velox.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    setup_logging()
    logger = structlog.get_logger("velox.main")
    logger.info("application_startup", env=settings.app_env)
    # Startup
    # TODO: Initialize DB pool (asyncpg)
    # TODO: Initialize Redis connection
    # TODO: Load hotel profiles from YAML
    # TODO: Load escalation matrix
    yield
    # Shutdown
    logger.info("application_shutdown")
    # TODO: Close DB pool
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
# app.include_router(whatsapp_webhook.router, prefix="/api/v1")
# app.include_router(admin_webhook.router, prefix="/api/v1")
# app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Return service status for root endpoint."""
    return {"service": "velox", "status": "running"}
