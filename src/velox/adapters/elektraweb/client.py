"""Elektraweb PMS HTTP client with JWT authentication and retry logic."""

import asyncio
from datetime import datetime, timedelta

import httpx
import structlog

from velox.config.settings import settings

logger = structlog.get_logger(__name__)

REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 5]


class ElektrawebClient:
    """Async HTTP client for the Elektraweb PMS API."""

    def __init__(self) -> None:
        self._base_url = settings.elektra_api_base_url.rstrip("/")
        self._api_key = settings.elektra_api_key
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

    async def _authenticate(self) -> str:
        """Authenticate with Elektraweb API and get JWT token."""
        client = await self._get_client()
        logger.info("elektraweb_auth_start")

        response = await client.post("/login", json={"apiKey": self._api_key})
        response.raise_for_status()
        data = response.json()

        self._token = data["token"]
        expires_in = data.get("expiresIn", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
        logger.info("elektraweb_auth_success", expires_in=expires_in)
        return self._token

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
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make an authenticated request with retries and token refresh."""
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                token = await self._get_token()
                response = await client.request(
                    method,
                    path,
                    json=json_body,
                    params=params,
                    headers=self._auth_headers(token),
                )

                if response.status_code == 401:
                    logger.warning("elektraweb_unauthorized_refreshing_token", path=path, attempt=attempt + 1)
                    self._token = None
                    self._token_expires_at = None
                    continue

                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as error:
                last_error = error
                logger.warning("elektraweb_timeout", path=path, attempt=attempt + 1, max_retries=MAX_RETRIES)
            except httpx.HTTPStatusError as error:
                last_error = error
                status_code = error.response.status_code
                logger.warning("elektraweb_http_status_error", path=path, status_code=status_code, attempt=attempt + 1)
                if 400 <= status_code < 500:
                    raise
            except httpx.RequestError as error:
                last_error = error
                logger.warning("elektraweb_request_error", path=path, error=str(error), attempt=attempt + 1)

            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                logger.info("elektraweb_retry_wait", wait_seconds=wait_time)
                await asyncio.sleep(wait_time)

        logger.error("elektraweb_request_exhausted", path=path, max_retries=MAX_RETRIES)
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Elektraweb request failed: {path}")

    async def get(self, path: str, params: dict | None = None) -> dict:
        """Make an authenticated GET request."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, json_body: dict | None = None) -> dict:
        """Make an authenticated POST request."""
        return await self.request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: dict | None = None) -> dict:
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
