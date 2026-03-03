# Task 04: Elektraweb PMS Adapter

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/error_handling.md`
> - `skills/security_privacy.md`

## Objective
Implement the HTTP client adapter for the Elektraweb PMS (Property Management System) API. This adapter handles JWT authentication, request retries, field normalization (kebab-case to snake_case), and exposes typed methods for availability, quote, reservation CRUD.

## Prerequisites
- Task 01 completed (project setup, httpx installed)
- Task 02 completed (database layer)
- Task 03 completed (hotel profile loader)
- Elektraweb API credentials in `.env`:
  - `ELEKTRA_API_BASE_URL=https://api.elektraweb.com`
  - `ELEKTRA_API_KEY=your-api-key`
  - `ELEKTRA_HOTEL_ID=21966`

---

## Step 1: Implement the HTTP Client with JWT Auth

Create `src/velox/adapters/elektraweb/client.py`:

```python
"""Elektraweb PMS HTTP client with JWT authentication and retry logic."""

from datetime import datetime, timedelta

import httpx
import structlog

from velox.config.settings import settings

logger = structlog.get_logger(__name__)

# Default configuration
REQUEST_TIMEOUT = 10.0  # seconds per request
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 5]  # seconds between retries (exponential)


class ElektrawebClient:
    """
    Async HTTP client for the Elektraweb PMS API.

    Features:
    - JWT authentication (POST /login with API key)
    - Automatic token caching and refresh on 401
    - Retry logic with exponential backoff (3 retries)
    - 10-second timeout per request
    - All requests use the base URL from settings.elektra_api_base_url
    """

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
        """Close the HTTP client. Call during app shutdown."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ---- Authentication ----

    async def _authenticate(self) -> str:
        """
        Authenticate with Elektraweb API and get a JWT token.

        POST /login
        Body: {"apiKey": "<api_key>"}
        Response: {"token": "eyJ...", "expiresIn": 3600}
        """
        client = await self._get_client()
        logger.info("Authenticating with Elektraweb API")

        response = await client.post(
            "/login",
            json={"apiKey": self._api_key},
        )
        response.raise_for_status()
        data = response.json()

        self._token = data["token"]
        # Cache token with a small buffer before expiry
        expires_in = data.get("expiresIn", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

        logger.info("Elektraweb authentication successful", expires_in=expires_in)
        return self._token

    async def _get_token(self) -> str:
        """Get a valid JWT token, refreshing if necessary."""
        if self._token is None or (
            self._token_expires_at and datetime.now() >= self._token_expires_at
        ):
            return await self._authenticate()
        return self._token

    def _auth_headers(self, token: str) -> dict[str, str]:
        """Build authorization headers."""
        return {"Authorization": f"Bearer {token}"}

    # ---- Core Request Method ----

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """
        Make an authenticated request to the Elektraweb API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /hotel/21966/availability)
            json_body: Request body for POST/PUT
            params: Query parameters for GET

        Returns:
            Parsed JSON response as dict

        Raises:
            httpx.HTTPStatusError: If all retries fail
        """
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

                # If 401, force token refresh and retry
                if response.status_code == 401:
                    logger.warning("Elektraweb 401 — refreshing token", attempt=attempt + 1)
                    self._token = None
                    self._token_expires_at = None
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Elektraweb request timeout",
                    path=path,
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES,
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    "Elektraweb HTTP error",
                    path=path,
                    status_code=e.response.status_code,
                    attempt=attempt + 1,
                )
                # Don't retry on 4xx (except 401 handled above)
                if 400 <= e.response.status_code < 500:
                    raise
            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    "Elektraweb request error",
                    path=path,
                    error=str(e),
                    attempt=attempt + 1,
                )

            # Wait before retry (exponential backoff)
            if attempt < MAX_RETRIES - 1:
                import asyncio
                wait_time = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                logger.info("Retrying in seconds", wait=wait_time)
                await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error("Elektraweb request failed after all retries", path=path)
        if last_error:
            raise last_error
        raise RuntimeError(f"Elektraweb request to {path} failed after {MAX_RETRIES} retries")

    # ---- Convenience Methods ----

    async def get(self, path: str, params: dict | None = None) -> dict:
        """Make an authenticated GET request."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, json_body: dict | None = None) -> dict:
        """Make an authenticated POST request."""
        return await self.request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: dict | None = None) -> dict:
        """Make an authenticated PUT request."""
        return await self.request("PUT", path, json_body=json_body)


# Module-level singleton
_client: ElektrawebClient | None = None


def get_elektraweb_client() -> ElektrawebClient:
    """Get or create the singleton Elektraweb client."""
    global _client
    if _client is None:
        _client = ElektrawebClient()
    return _client


async def close_elektraweb_client() -> None:
    """Close the singleton client. Call during app shutdown."""
    global _client
    if _client:
        await _client.close()
        _client = None
```

**File to create**: `src/velox/adapters/elektraweb/client.py`

---

## Step 2: Implement Field Mapper (kebab-case to snake_case)

Create `src/velox/adapters/elektraweb/mapper.py`:

```python
"""Elektraweb response field mapper — normalizes kebab-case to snake_case."""

import re
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)


def kebab_to_snake(name: str) -> str:
    """Convert a kebab-case field name to snake_case.

    Examples:
        'room-type-id' -> 'room_type_id'
        'checkin-date' -> 'checkin_date'
        'price-agency-id' -> 'price_agency_id'
        'roomTypeId' -> 'room_type_id'  (also handles camelCase)
    """
    # First handle kebab-case
    name = name.replace("-", "_")
    # Then handle camelCase
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def normalize_keys(data: dict | list) -> dict | list:
    """
    Recursively normalize all keys in a dict/list from kebab-case/camelCase to snake_case.

    Args:
        data: Dict or list from Elektraweb API response

    Returns:
        Same structure with all keys converted to snake_case
    """
    if isinstance(data, dict):
        return {kebab_to_snake(k): normalize_keys(v) for k, v in data.items()}
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    return data


# ---- Response Pydantic Models ----

class AvailabilityRow(BaseModel):
    """A single row in the availability response."""
    date: str
    room_type_id: int
    room_type: str = ""
    room_to_sell: int = 0
    stop_sell: bool = False


class AvailabilityResponse(BaseModel):
    """Parsed availability response from Elektraweb."""
    available: bool = False
    rows: list[AvailabilityRow] = Field(default_factory=list)
    derived: dict = Field(default_factory=dict)
    notes: str = ""


class BookingOffer(BaseModel):
    """A single offer from the quote/price endpoint."""
    id: str = ""
    room_type_id: int
    board_type_id: int
    rate_type_id: int
    rate_code_id: int
    price_agency_id: int | None = None
    currency_code: str = "EUR"
    price: Decimal
    discounted_price: Decimal
    cancellation_penalty: dict = Field(default_factory=dict)


class QuoteResponse(BaseModel):
    """Parsed quote response from Elektraweb."""
    offers: list[BookingOffer] = Field(default_factory=list)


class ReservationResponse(BaseModel):
    """Parsed reservation creation response from Elektraweb."""
    reservation_id: str = ""
    voucher_no: str = ""
    confirmation_url: str | None = None
    state: str = ""


class ReservationDetailResponse(BaseModel):
    """Parsed reservation detail (GET) response from Elektraweb."""
    success: bool = False
    reservation_id: str = ""
    voucher_no: str = ""
    total_price: Decimal | None = None
    state: str = ""
    raw_data: dict = Field(default_factory=dict)


def parse_availability(raw: dict) -> AvailabilityResponse:
    """Parse raw Elektraweb availability response into typed model."""
    normalized = normalize_keys(raw)
    return AvailabilityResponse(**normalized)


def parse_quote(raw: dict) -> QuoteResponse:
    """Parse raw Elektraweb quote/price response into typed model."""
    normalized = normalize_keys(raw)
    return QuoteResponse(**normalized)


def parse_reservation_create(raw: dict) -> ReservationResponse:
    """Parse raw Elektraweb create reservation response into typed model."""
    normalized = normalize_keys(raw)
    return ReservationResponse(**normalized)


def parse_reservation_detail(raw: dict) -> ReservationDetailResponse:
    """Parse raw Elektraweb reservation detail response into typed model."""
    normalized = normalize_keys(raw)
    return ReservationDetailResponse(**normalized, raw_data=raw)
```

**File to create**: `src/velox/adapters/elektraweb/mapper.py`

---

## Step 3: Implement Endpoint Methods

Create `src/velox/adapters/elektraweb/endpoints.py`:

```python
"""Elektraweb API endpoint methods — typed wrappers around the HTTP client."""

from datetime import date

import structlog

from velox.adapters.elektraweb.client import get_elektraweb_client
from velox.adapters.elektraweb.mapper import (
    AvailabilityResponse,
    QuoteResponse,
    ReservationResponse,
    ReservationDetailResponse,
    parse_availability,
    parse_quote,
    parse_reservation_create,
    parse_reservation_detail,
)

logger = structlog.get_logger(__name__)


async def availability(
    hotel_id: int,
    checkin: date,
    checkout: date,
    adults: int,
    chd_count: int = 0,
    chd_ages: list[int] | None = None,
    currency: str = "EUR",
) -> AvailabilityResponse:
    """
    Check room availability for given dates.

    Elektraweb API: GET /hotel/{hotel_id}/availability

    Args:
        hotel_id: PMS hotel ID (e.g., 21966)
        checkin: Check-in date
        checkout: Check-out date
        adults: Number of adults
        chd_count: Number of children
        chd_ages: List of children ages
        currency: ISO 4217 currency code

    Returns:
        AvailabilityResponse with available rooms and their sell counts
    """
    client = get_elektraweb_client()

    params = {
        "checkin": checkin.isoformat(),
        "checkout": checkout.isoformat(),
        "adults": adults,
        "chdCount": chd_count,
        "currency": currency,
    }
    if chd_ages:
        params["chdAges"] = ",".join(str(a) for a in chd_ages)

    logger.info("Checking availability", hotel_id=hotel_id, checkin=str(checkin), checkout=str(checkout))

    raw = await client.get(f"/hotel/{hotel_id}/availability", params=params)
    return parse_availability(raw)


async def quote(
    hotel_id: int,
    checkin: date,
    checkout: date,
    adults: int,
    chd_count: int = 0,
    chd_ages: list[int] | None = None,
    currency: str = "EUR",
    language: str = "TR",
    nationality: str = "TR",
    only_best_offer: bool = False,
    cancel_policy_type: str | None = None,
) -> QuoteResponse:
    """
    Get price quotes/offers for given dates and room configuration.

    Elektraweb API: GET /hotel/{hotel_id}/price/

    Args:
        hotel_id: PMS hotel ID
        checkin: Check-in date
        checkout: Check-out date
        adults: Number of adults
        chd_count: Number of children
        chd_ages: List of children ages
        currency: ISO 4217 currency code
        language: "TR" or "EN"
        nationality: ISO 3166-1 alpha-2 country code
        only_best_offer: Return only the best offer per room type
        cancel_policy_type: "FREE_CANCEL" or "NON_REFUNDABLE" (optional filter)

    Returns:
        QuoteResponse with list of offers
    """
    client = get_elektraweb_client()

    params = {
        "checkin": checkin.isoformat(),
        "checkout": checkout.isoformat(),
        "adults": adults,
        "chdCount": chd_count,
        "currency": currency,
        "language": language,
        "nationality": nationality,
        "onlyBestOffer": only_best_offer,
    }
    if chd_ages:
        params["chdAges"] = ",".join(str(a) for a in chd_ages)
    if cancel_policy_type:
        params["cancelPolicyType"] = cancel_policy_type

    logger.info("Getting quote", hotel_id=hotel_id, checkin=str(checkin), checkout=str(checkout))

    raw = await client.get(f"/hotel/{hotel_id}/price/", params=params)
    return parse_quote(raw)


async def create_reservation(hotel_id: int, draft: dict) -> ReservationResponse:
    """
    Create a reservation in Elektraweb PMS.

    Elektraweb API: POST /hotel/{hotel_id}/createReservation
    Fallback paths (tenant override):
        - /hotel/{hotel_id}/reservation/create
        - /hotel/{hotel_id}/reservations/create

    Args:
        hotel_id: PMS hotel ID
        draft: Reservation draft dict with fields:
            checkin_date, checkout_date, room_type_id, board_type_id,
            rate_type_id, rate_code_id, price_agency_id, currency,
            total_price, adults, chd_ages, guest_name, phone, email, notes

    Returns:
        ReservationResponse with reservation_id and voucher_no
    """
    client = get_elektraweb_client()

    # Try primary path first, then fallbacks
    paths = [
        f"/hotel/{hotel_id}/createReservation",
        f"/hotel/{hotel_id}/reservation/create",
        f"/hotel/{hotel_id}/reservations/create",
    ]

    last_error: Exception | None = None
    for path in paths:
        try:
            logger.info("Creating reservation", hotel_id=hotel_id, path=path)
            raw = await client.post(path, json_body=draft)
            return parse_reservation_create(raw)
        except Exception as e:
            logger.warning("Reservation create path failed, trying next", path=path, error=str(e))
            last_error = e

    logger.error("All reservation create paths failed", hotel_id=hotel_id)
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to create reservation for hotel {hotel_id}")


async def get_reservation(
    hotel_id: int,
    reservation_id: str | None = None,
    voucher_no: str | None = None,
) -> ReservationDetailResponse:
    """
    Fetch reservation details from Elektraweb.

    Uses POST/GET fallback strategy with tenant path variations.

    Args:
        hotel_id: PMS hotel ID
        reservation_id: PMS reservation ID (optional)
        voucher_no: Voucher number (optional)
        At least one of reservation_id or voucher_no must be provided.

    Returns:
        ReservationDetailResponse with reservation details
    """
    client = get_elektraweb_client()

    body = {"hotelId": hotel_id}
    if reservation_id:
        body["reservationId"] = reservation_id
    if voucher_no:
        body["voucherNo"] = voucher_no

    # Try multiple paths (tenant fallback strategy)
    paths_and_methods = [
        ("POST", f"/hotel/{hotel_id}/getReservation"),
        ("GET", f"/hotel/{hotel_id}/reservation/{reservation_id or ''}"),
        ("POST", f"/hotel/{hotel_id}/reservation/get"),
    ]

    last_error: Exception | None = None
    for method, path in paths_and_methods:
        try:
            logger.info("Fetching reservation", hotel_id=hotel_id, path=path, method=method)
            if method == "POST":
                raw = await client.post(path, json_body=body)
            else:
                params = {}
                if voucher_no:
                    params["voucherNo"] = voucher_no
                raw = await client.get(path, params=params if params else None)
            return parse_reservation_detail(raw)
        except Exception as e:
            logger.warning("Reservation fetch path failed", path=path, error=str(e))
            last_error = e

    logger.error("All reservation fetch paths failed", hotel_id=hotel_id)
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to get reservation for hotel {hotel_id}")


async def modify_reservation(hotel_id: int, reservation_id: str, updates: dict) -> dict:
    """
    Modify an existing reservation in Elektraweb.

    Elektraweb API: POST /hotel/{hotel_id}/updateReservation

    Args:
        hotel_id: PMS hotel ID
        reservation_id: PMS reservation ID to modify
        updates: Dict of fields to update

    Returns:
        Raw response dict from Elektraweb
    """
    client = get_elektraweb_client()

    body = {"reservationId": reservation_id, **updates}

    logger.info("Modifying reservation", hotel_id=hotel_id, reservation_id=reservation_id)
    return await client.post(f"/hotel/{hotel_id}/updateReservation", json_body=body)


async def cancel_reservation(hotel_id: int, reservation_id: str, reason: str) -> dict:
    """
    Cancel a reservation in Elektraweb.

    Elektraweb API: POST /hotel/{hotel_id}/cancelReservation

    Args:
        hotel_id: PMS hotel ID
        reservation_id: PMS reservation ID to cancel
        reason: Cancellation reason text

    Returns:
        Raw response dict from Elektraweb
    """
    client = get_elektraweb_client()

    body = {"reservationId": reservation_id, "reason": reason}

    logger.info("Cancelling reservation", hotel_id=hotel_id, reservation_id=reservation_id)
    return await client.post(f"/hotel/{hotel_id}/cancelReservation", json_body=body)
```

**File to create**: `src/velox/adapters/elektraweb/endpoints.py`

---

## Step 4: Wire Up Elektraweb Client Shutdown

Modify `src/velox/main.py` to close the Elektraweb client on shutdown:

```python
from velox.adapters.elektraweb.client import close_elektraweb_client

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ... startup code ...
    yield
    # Shutdown
    await close_db_pool()
    await close_elektraweb_client()
    # TODO: Close Redis connection
```

**File to modify**: `src/velox/main.py`

---

## Step 5: Export Adapter Module

Update `src/velox/adapters/elektraweb/__init__.py`:

```python
"""Elektraweb PMS adapter package."""

from velox.adapters.elektraweb.client import get_elektraweb_client, close_elektraweb_client
from velox.adapters.elektraweb.endpoints import (
    availability,
    quote,
    create_reservation,
    get_reservation,
    modify_reservation,
    cancel_reservation,
)
from velox.adapters.elektraweb.mapper import normalize_keys, kebab_to_snake

__all__ = [
    "get_elektraweb_client",
    "close_elektraweb_client",
    "availability",
    "quote",
    "create_reservation",
    "get_reservation",
    "modify_reservation",
    "cancel_reservation",
    "normalize_keys",
    "kebab_to_snake",
]
```

**File to modify**: `src/velox/adapters/elektraweb/__init__.py`

---

## Verification Checklist

- [ ] `src/velox/adapters/elektraweb/client.py` exists with `ElektrawebClient` class
- [ ] Client has JWT authentication via `POST /login` with API key
- [ ] Token is cached and refreshed on 401 responses
- [ ] Retry logic: 3 attempts with exponential backoff [1s, 3s, 5s]
- [ ] Request timeout is 10 seconds
- [ ] `src/velox/adapters/elektraweb/mapper.py` exists with:
  - `kebab_to_snake()` function that converts "room-type-id" to "room_type_id"
  - `normalize_keys()` function that recursively normalizes all keys
  - Pydantic response models: `AvailabilityResponse`, `QuoteResponse`, `ReservationResponse`, `ReservationDetailResponse`
- [ ] `src/velox/adapters/elektraweb/endpoints.py` exists with:
  - `availability()` — GET /hotel/{id}/availability
  - `quote()` — GET /hotel/{id}/price/
  - `create_reservation()` — POST with fallback paths
  - `get_reservation()` — POST/GET with fallback paths
  - `modify_reservation()` — POST /hotel/{id}/updateReservation
  - `cancel_reservation()` — POST /hotel/{id}/cancelReservation
- [ ] All endpoint methods accept typed parameters and return typed responses
- [ ] Tenant fallback paths are tried in order for create and get reservation
- [ ] Elektraweb client is closed on app shutdown
- [ ] `__init__.py` exports all public APIs

---

## Files Created in This Task
| File | Purpose |
|------|---------|
| `src/velox/adapters/elektraweb/client.py` | HTTP client with JWT auth, retry, timeout |
| `src/velox/adapters/elektraweb/mapper.py` | Field normalization + response Pydantic models |
| `src/velox/adapters/elektraweb/endpoints.py` | Typed API endpoint wrappers |

## Files Modified in This Task
| File | Change |
|------|--------|
| `src/velox/adapters/elektraweb/__init__.py` | Export public APIs |
| `src/velox/main.py` | Close Elektraweb client on shutdown |
