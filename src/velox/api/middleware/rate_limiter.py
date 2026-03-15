"""Redis-based rate limiting middleware."""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from velox.config.settings import settings


class RateLimiter:
    """Redis sliding-window rate limiter helpers."""

    @staticmethod
    async def check_rate_limit(
        redis: Any,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """Return True if request count is below threshold in the window."""
        now = time.time()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        current_count = int(results[1] or 0)
        return current_count < max_requests

    @staticmethod
    async def check_phone_rate_limit(redis: Any, phone_hash: str) -> None:
        """Enforce per-phone minute/hour thresholds."""
        minute_key = f"rl:phone:{phone_hash}:min"
        minute_ok = await RateLimiter.check_rate_limit(
            redis,
            minute_key,
            settings.rate_limit_per_phone_per_minute,
            60,
        )
        if not minute_ok:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many messages per minute",
            )

        hour_key = f"rl:phone:{phone_hash}:hour"
        hour_ok = await RateLimiter.check_rate_limit(
            redis,
            hour_key,
            settings.rate_limit_per_phone_per_hour,
            3600,
        )
        if not hour_ok:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many messages per hour",
            )

    @staticmethod
    async def check_webhook_rate_limit(redis: Any, ip_address: str) -> None:
        """Enforce per-IP webhook request threshold."""
        key = f"rl:webhook:{ip_address}:min"
        allowed = await RateLimiter.check_rate_limit(
            redis,
            key,
            settings.rate_limit_webhook_per_minute,
            60,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many webhook requests",
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limit checks for webhook routes."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.startswith("/api/v1/webhook"):
            redis = getattr(request.app.state, "redis", None)
            if redis is not None:
                client_ip = request.client.host if request.client else "unknown"
                try:
                    await RateLimiter.check_webhook_rate_limit(redis, client_ip)
                except HTTPException as exc:
                    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)
