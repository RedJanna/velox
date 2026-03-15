"""Elektraweb PMS HTTP client with JWT authentication and retry logic."""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog

from velox.config.settings import settings

logger = structlog.get_logger(__name__)

REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 5]
FALLBACK_BASE_URL = "https://4001.hoteladvisor.net"
ACTION_OBJECT_PATH_PREFIXES = ("/Insert/", "/Update/", "/Select/", "/Execute/", "/Function/")


class ElektrawebClient:
    """Async HTTP client for the Elektraweb PMS API."""

    def __init__(self) -> None:
        configured_base_url = settings.elektra_api_base_url.strip()
        self._base_url = (configured_base_url or "https://bookingapi.elektraweb.com").rstrip("/")
        self._base_urls = self._build_base_urls(self._base_url)
        self._api_key = settings.elektra_api_key.strip()
        legacy_booking_key = "Elektra_Booking"
        legacy_booking = os.getenv(legacy_booking_key, "").strip()
        self._raw_booking_credential = legacy_booking or os.getenv("ELEKTRA_BOOKING", "").strip()
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _build_base_urls(primary_base_url: str) -> list[str]:
        """Build ordered base URLs for failover: primary then fallback."""
        urls = [primary_base_url.rstrip("/")]
        fallback = FALLBACK_BASE_URL.rstrip("/")
        if fallback not in urls:
            urls.append(fallback)
        return urls

    async def _switch_base_url(self, base_url: str) -> None:
        """Switch active base URL and reset auth/client state for the new host."""
        normalized = base_url.rstrip("/")
        if normalized == self._base_url:
            return

        await self.close()
        self._base_url = normalized
        self._token = None
        self._token_expires_at = None

    async def _authenticate(self) -> str:
        """Authenticate with Elektraweb API and get JWT token."""
        client = await self._get_client()
        logger.info("elektraweb_auth_start")
        candidates = self._build_auth_candidates()
        last_response: httpx.Response | None = None

        for candidate in candidates:
            try:
                login_attempts: tuple[tuple[dict[str, str] | None, dict[str, Any] | None], ...] = (
                    ({"Authorization": f"Bearer {candidate}"}, None),
                    ({"Authorization": f"Bearer {candidate}"}, {}),
                    (None, {"apiKey": candidate}),
                )
                for headers, json_payload in login_attempts:
                    request_kwargs: dict[str, Any] = {}
                    if headers is not None:
                        request_kwargs["headers"] = headers
                    if json_payload is not None:
                        request_kwargs["json"] = json_payload
                    response = await client.post("/login", **request_kwargs)
                    if response.status_code >= 400:
                        last_response = response
                        continue

                    data = response.json()
                    token = str(data.get("token") or data.get("jwt") or data.get("accessToken") or "")
                    if not token:
                        last_response = response
                        continue

                    self._token = token
                    expires_in = int(data.get("expiresIn", 3600))
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    logger.info("elektraweb_auth_success", expires_in=expires_in)
                    return self._token
            except Exception as error:
                logger.warning("elektraweb_auth_attempt_failed", error_type=type(error).__name__)

        status_code = last_response.status_code if last_response is not None else None
        body_preview = (last_response.text[:300] if last_response is not None else "")
        logger.error("elektraweb_auth_failed", status_code=status_code, body_preview=body_preview)
        raise RuntimeError("Elektraweb authentication failed. Check ELEKTRA_API_KEY/Elektra_Booking credentials.")

    def _build_auth_candidates(self) -> list[str]:
        """Build possible credential shapes accepted by Elektra login endpoint."""
        candidates: list[str] = []
        if self._api_key:
            candidates.append(self._api_key)
            if "$" not in self._api_key:
                candidates.append(f"booking#{settings.elektra_hotel_id}${self._api_key}")
        if self._raw_booking_credential:
            candidates.append(self._raw_booking_credential)

        # Preserve order while removing duplicates.
        deduped: list[str] = []
        seen: set[str] = set()
        for value in candidates:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped

    async def _get_token(self) -> str:
        """Get a valid token, refreshing it when expired or missing."""
        if self._token is None or (
            self._token_expires_at is not None and datetime.now() >= self._token_expires_at
        ):
            return await self._authenticate()
        return self._token

    @staticmethod
    def _auth_headers(token: str) -> dict[str, str]:
        """Build authorization headers."""
        return {"Authorization": f"Bearer {token}"}

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request with retries and token refresh."""
        last_error: Exception | None = None

        for base_index, base_url in enumerate(self._base_urls, start=1):
            await self._switch_base_url(base_url)
            client = await self._get_client()
            logger.info(
                "elektraweb_request_base_selected",
                path=path,
                base_url=self._base_url,
                base_index=base_index,
                base_count=len(self._base_urls),
            )

            for attempt in range(MAX_RETRIES):
                try:
                    token = await self._get_token()
                    request_headers = self._auth_headers(token)
                    request_json = json_body
                    if isinstance(request_json, dict) and path.startswith(ACTION_OBJECT_PATH_PREFIXES):
                        if "LoginToken" not in request_json:
                            request_json = {**request_json, "LoginToken": token}
                        request_headers = {"Content-Type": "application/json"}

                    response = await client.request(
                        method,
                        path,
                        json=request_json,
                        params=params,
                        headers=request_headers,
                    )

                    if response.status_code == 401:
                        logger.warning("elektraweb_unauthorized_refreshing_token", path=path, attempt=attempt + 1)
                        self._token = None
                        self._token_expires_at = None
                        continue

                    response.raise_for_status()
                    response_json = response.json()
                    if isinstance(response_json, dict):
                        return response_json
                    logger.warning(
                        "elektraweb_non_object_response",
                        path=path,
                        response_type=type(response_json).__name__,
                    )
                    return {"data": response_json}
                except httpx.TimeoutException as error:
                    last_error = error
                    logger.warning(
                        "elektraweb_timeout",
                        path=path,
                        attempt=attempt + 1,
                        max_retries=MAX_RETRIES,
                        base_url=self._base_url,
                    )
                except httpx.HTTPStatusError as error:
                    last_error = error
                    status_code = error.response.status_code
                    logger.warning(
                        "elektraweb_http_status_error",
                        path=path,
                        status_code=status_code,
                        attempt=attempt + 1,
                        base_url=self._base_url,
                    )
                    if 400 <= status_code < 500:
                        break
                except httpx.RequestError as error:
                    last_error = error
                    logger.warning(
                        "elektraweb_request_error",
                        path=path,
                        error=str(error),
                        attempt=attempt + 1,
                        base_url=self._base_url,
                    )
                except Exception as error:
                    last_error = error
                    logger.warning(
                        "elektraweb_unexpected_error",
                        path=path,
                        error_type=type(error).__name__,
                        base_url=self._base_url,
                    )
                    break

                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    logger.info("elektraweb_retry_wait", wait_seconds=wait_time, base_url=self._base_url)
                    await asyncio.sleep(wait_time)

            if base_index < len(self._base_urls):
                logger.warning(
                    "elektraweb_failover_next_base",
                    path=path,
                    failed_base_url=self._base_url,
                    next_base_url=self._base_urls[base_index],
                )

        logger.error(
            "elektraweb_request_exhausted",
            path=path,
            max_retries=MAX_RETRIES,
            base_urls=self._base_urls,
        )
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Elektraweb request failed: {path}")

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated GET request."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated POST request."""
        return await self.request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated PUT request."""
        return await self.request("PUT", path, json_body=json_body)


_client: ElektrawebClient | None = None


def get_elektraweb_client() -> ElektrawebClient:
    """Get or create singleton Elektraweb client."""
    global _client
    if _client is None:
        _client = ElektrawebClient()
    return _client


async def close_elektraweb_client() -> None:
    """Close singleton Elektraweb client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
