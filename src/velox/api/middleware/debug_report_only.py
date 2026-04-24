"""Report-only middleware for admin debug worker sessions."""

from __future__ import annotations

from typing import Final

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from velox.utils.admin_debug_security import DEBUG_SESSION_HEADER, AdminDebugSession, decode_debug_session_token
from velox.utils.admin_security import SAFE_HTTP_METHODS

logger = structlog.get_logger(__name__)

REPORT_ONLY_BLOCK_MESSAGE: Final[str] = "Report-only debug session blocked a mutation-capable operation"


class ReportOnlyDebugMiddleware(BaseHTTPMiddleware):
    """Attach validated debug sessions to requests and block unsafe mutations."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        token = request.headers.get(DEBUG_SESSION_HEADER, "").strip()
        if not token:
            return await call_next(request)

        try:
            debug_session = decode_debug_session_token(token)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid debug session token."},
            )

        request.state.debug_session = debug_session
        if debug_session.report_only and request.method.upper() not in SAFE_HTTP_METHODS:
            logger.warning(
                "admin_debug_mutation_blocked",
                run_id=str(debug_session.run_id),
                hotel_id=debug_session.hotel_id,
                triggered_by_user_id=debug_session.triggered_by_user_id,
                method=request.method.upper(),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": REPORT_ONLY_BLOCK_MESSAGE},
            )
        return await call_next(request)


def get_debug_session(request: Request) -> AdminDebugSession | None:
    """Return the request-scoped debug session when the middleware validated one."""
    debug_session = getattr(request.state, "debug_session", None)
    if isinstance(debug_session, AdminDebugSession):
        return debug_session
    return None
