"""Integration tests for the Prometheus metrics endpoint."""

import httpx
import pytest
from fastapi import FastAPI

from velox.api.routes import health
from velox.config.settings import settings
from velox.utils.metrics import (
    record_intent_domain_guard,
    record_structured_output_parser_error,
    reset_metrics,
)


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_text() -> None:
    """The metrics endpoint should expose runtime counters in Prometheus text format."""
    reset_metrics()
    record_structured_output_parser_error("invalid_internal_json")
    record_intent_domain_guard(
        "stay_followup_without_restaurant_tools",
        "restaurant_booking_create",
        "stay_availability",
    )

    app = FastAPI()
    app.include_router(health.metrics_router)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    assert (
        'velox_llm_structured_output_parser_errors_total{reason="invalid_internal_json"} 1.0'
        in response.text
    )
    assert (
        'velox_llm_intent_domain_guard_total{from_intent="restaurant_booking_create",'
        'reason="stay_followup_without_restaurant_tools",to_intent="stay_availability"} 1.0'
        in response.text
    )


@pytest.mark.asyncio
async def test_metrics_endpoint_rejects_non_private_clients_by_default() -> None:
    """The metrics endpoint should stay private unless explicitly exposed."""
    reset_metrics()

    app = FastAPI()
    app.include_router(health.metrics_router)
    transport = httpx.ASGITransport(app=app, client=("8.8.8.8", 123))

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/metrics")

    assert response.status_code == 403
    assert response.json() == {"detail": "metrics_access_denied"}


@pytest.mark.asyncio
async def test_metrics_endpoint_can_be_explicitly_opened_for_public_scrape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Public access should require an explicit settings override."""
    reset_metrics()
    monkeypatch.setattr(settings, "metrics_allow_public", True)

    app = FastAPI()
    app.include_router(health.metrics_router)
    transport = httpx.ASGITransport(app=app, client=("8.8.8.8", 123))

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
