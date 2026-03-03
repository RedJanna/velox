# Task 09: Admin API

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/security_privacy.md`

## Objective
Implement the admin REST API with JWT authentication, role-based access control, and Redis-based rate limiting. The admin API allows hotel staff to manage hotels, view conversations, approve/reject holds, and manage escalation tickets through a web panel.

## Prerequisites
- Tasks 01-08 completed
- Database tables exist: `hotels`, `conversations`, `messages`, `stay_holds`, `restaurant_holds`, `transfer_holds`, `approval_requests`, `tickets`, `admin_users`
- Settings available: `admin_jwt_secret`, `admin_jwt_algorithm`, `admin_jwt_expire_minutes`, `rate_limit_*`
- Constants: `Role` enum (ADMIN, SALES, OPS, CHEF), `HoldStatus`, `TicketPriority`
- Redis connection available at `app.state.redis`
- DB pool available at `app.state.db_pool`

---

## Step 1: Implement JWT Authentication Middleware

### File: `src/velox/api/middleware/auth.py`

```python
"""JWT authentication and role-based access control for admin routes."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from velox.config.settings import settings
from velox.config.constants import Role
```

### 1.1 Define token models

```python
class TokenData(BaseModel):
    """Decoded JWT token payload."""
    user_id: int
    hotel_id: int
    username: str
    role: Role
    display_name: str | None = None


class TokenResponse(BaseModel):
    """JWT token response for login endpoint."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    hotel_id: int
```

### 1.2 Implement token creation

```python
def create_access_token(data: TokenData) -> str:
    """
    Create a JWT access token with expiration.
    Uses HS256 algorithm with settings.admin_jwt_secret.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.admin_jwt_expire_minutes)
    payload = {
        "sub": str(data.user_id),
        "hotel_id": data.hotel_id,
        "username": data.username,
        "role": data.role.value,
        "display_name": data.display_name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
```

### 1.3 Implement token verification dependency

```python
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    """
    FastAPI dependency that extracts and validates JWT from Authorization header.
    Raises 401 if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.admin_jwt_secret,
            algorithms=[settings.admin_jwt_algorithm],
        )
        user_id = int(payload.get("sub", 0))
        if user_id == 0:
            raise credentials_exception

        return TokenData(
            user_id=user_id,
            hotel_id=payload["hotel_id"],
            username=payload["username"],
            role=Role(payload["role"]),
            display_name=payload.get("display_name"),
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise credentials_exception from exc
```

### 1.4 Implement role-based access control

```python
def require_role(*allowed_roles: Role):
    """
    Factory that returns a FastAPI dependency enforcing role-based access.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(Role.ADMIN))])
        async def admin_only_endpoint(...):

    Or as a parameter dependency:
        async def endpoint(user: TokenData = Depends(require_role(Role.ADMIN, Role.SALES))):
    """
    async def role_checker(
        current_user: Annotated[TokenData, Depends(get_current_user)],
    ) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker
```

### 1.5 Role permissions matrix

Define which roles can access which resources:

```python
# ADMIN: full access to everything
# SALES: view conversations, manage stays, manage transfers, view tickets
# OPS: view conversations, manage restaurants, manage transfers, manage tickets (assigned)
# CHEF: view restaurant holds, manage restaurant holds (assigned)

ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "hotels:read", "hotels:write",
        "conversations:read",
        "holds:read", "holds:approve", "holds:reject",
        "tickets:read", "tickets:write",
    },
    Role.SALES: {
        "conversations:read",
        "holds:read", "holds:approve", "holds:reject",
        "tickets:read",
    },
    Role.OPS: {
        "conversations:read",
        "holds:read", "holds:approve", "holds:reject",
        "tickets:read", "tickets:write",
    },
    Role.CHEF: {
        "holds:read", "holds:approve",
    },
}


def check_permission(user: TokenData, permission: str) -> None:
    """Raise 403 if user's role does not have the required permission."""
    if permission not in ROLE_PERMISSIONS.get(user.role, set()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' not granted to role '{user.role}'",
        )
```

---

## Step 2: Implement Rate Limiter Middleware

### File: `src/velox/api/middleware/rate_limiter.py`

```python
"""Redis-based rate limiting middleware."""

import time
from fastapi import HTTPException, Request, status
from velox.config.settings import settings
```

### 2.1 Implement sliding window rate limiter

```python
class RateLimiter:
    """
    Redis-based sliding window rate limiter.
    Supports per-phone and per-IP limiting.
    """

    @staticmethod
    async def check_rate_limit(
        redis,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if the request is within rate limit.
        Uses Redis sorted sets for sliding window.

        Args:
            redis: Redis connection
            key: Rate limit key (e.g., "rl:phone:<hash>:min")
            max_requests: Maximum allowed requests in the window
            window_seconds: Time window in seconds

        Returns:
            True if within limit, False if exceeded.
        """
        now = time.time()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry on the key
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]

        return current_count < max_requests

    @staticmethod
    async def check_phone_rate_limit(redis, phone_hash: str) -> None:
        """
        Enforce per-phone rate limits:
        - 30 requests per minute
        - 200 requests per hour

        Raises HTTPException 429 if exceeded.
        """
        # Per-minute check
        minute_key = f"rl:phone:{phone_hash}:min"
        if not await RateLimiter.check_rate_limit(
            redis, minute_key,
            settings.rate_limit_per_phone_per_minute, 60,
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many messages per minute",
            )

        # Per-hour check
        hour_key = f"rl:phone:{phone_hash}:hour"
        if not await RateLimiter.check_rate_limit(
            redis, hour_key,
            settings.rate_limit_per_phone_per_hour, 3600,
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many messages per hour",
            )

    @staticmethod
    async def check_webhook_rate_limit(redis, ip_address: str) -> None:
        """
        Enforce per-IP webhook rate limit:
        - 100 requests per minute

        Raises HTTPException 429 if exceeded.
        """
        key = f"rl:webhook:{ip_address}:min"
        if not await RateLimiter.check_rate_limit(
            redis, key,
            settings.rate_limit_webhook_per_minute, 60,
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many webhook requests",
            )
```

### 2.2 Implement middleware for automatic rate limiting

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies rate limiting to webhook endpoints.
    Apply to the FastAPI app in main.py.
    """

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit webhook endpoints
        if request.url.path.startswith("/api/v1/webhook"):
            redis = request.app.state.redis
            client_ip = request.client.host if request.client else "unknown"
            try:
                await RateLimiter.check_webhook_rate_limit(redis, client_ip)
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                )

        response = await call_next(request)
        return response
```

---

## Step 3: Implement Admin Login Endpoint

### File: `src/velox/api/routes/admin.py`

```python
"""Admin panel REST API routes."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from velox.api.middleware.auth import (
    TokenData,
    TokenResponse,
    check_permission,
    create_access_token,
    get_current_user,
    require_role,
)
from velox.config.constants import HoldStatus, Role

router = APIRouter(prefix="/admin", tags=["admin"])
```

### 3.1 Login endpoint

```python
class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=TokenResponse)
async def admin_login(body: LoginRequest, request: Request):
    """
    Authenticate admin user and return JWT token.
    Verifies username + password against admin_users table using passlib bcrypt.
    """
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, hotel_id, username, password_hash, role, display_name, is_active
            FROM admin_users WHERE username = $1
            """,
            body.username,
        )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Verify password with passlib
    from passlib.hash import bcrypt
    if not bcrypt.verify(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = TokenData(
        user_id=row["id"],
        hotel_id=row["hotel_id"],
        username=row["username"],
        role=Role(row["role"]),
        display_name=row["display_name"],
    )

    access_token = create_access_token(token_data)
    from velox.config.settings import settings

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.admin_jwt_expire_minutes * 60,
        role=token_data.role.value,
        hotel_id=token_data.hotel_id,
    )
```

---

## Step 4: Implement Hotel Management Endpoints

### 4.1 List hotels

```python
@router.get("/hotels")
async def list_hotels(
    request: Request,
    user: TokenData = Depends(get_current_user),
):
    """
    GET /api/v1/admin/hotels
    ADMIN: list all hotels
    Others: list only their hotel
    """
    check_permission(user, "hotels:read")
    db = request.app.state.db_pool

    if user.role == Role.ADMIN:
        query = "SELECT id, hotel_id, name_tr, name_en, hotel_type, is_active, created_at FROM hotels ORDER BY id"
        async with db.acquire() as conn:
            rows = await conn.fetch(query)
    else:
        query = "SELECT id, hotel_id, name_tr, name_en, hotel_type, is_active, created_at FROM hotels WHERE hotel_id = $1"
        async with db.acquire() as conn:
            rows = await conn.fetch(query, user.hotel_id)

    return [dict(row) for row in rows]
```

### 4.2 Hotel detail

```python
@router.get("/hotels/{hotel_id}")
async def get_hotel(
    hotel_id: int,
    request: Request,
    user: TokenData = Depends(get_current_user),
):
    """
    GET /api/v1/admin/hotels/{hotel_id}
    Returns hotel detail including full profile_json.
    """
    check_permission(user, "hotels:read")
    # Non-admin users can only view their own hotel
    if user.role != Role.ADMIN and user.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="Access denied to this hotel")

    db = request.app.state.db_pool
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM hotels WHERE hotel_id = $1", hotel_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return dict(row)
```

### 4.3 Update hotel profile

```python
class HotelProfileUpdate(BaseModel):
    profile_json: dict  # Full or partial profile update


@router.put("/hotels/{hotel_id}/profile")
async def update_hotel_profile(
    hotel_id: int,
    body: HotelProfileUpdate,
    request: Request,
    user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    PUT /api/v1/admin/hotels/{hotel_id}/profile
    Updates the hotel profile_json. ADMIN only.
    After updating DB, also reload the in-memory hotel profile.
    """
    db = request.app.state.db_pool
    async with db.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE hotels SET profile_json = $1, updated_at = now()
            WHERE hotel_id = $2
            """,
            body.profile_json,
            hotel_id,
        )

    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Reload in-memory profile (if hotel profile loader is implemented)
    # await request.app.state.profile_loader.reload(hotel_id)

    return {"status": "updated", "hotel_id": hotel_id}
```

---

## Step 5: Implement Conversation Endpoints

### 5.1 List conversations

```python
@router.get("/conversations")
async def list_conversations(
    request: Request,
    user: TokenData = Depends(get_current_user),
    hotel_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/admin/conversations
    Filterable by hotel, status, date range. Paginated.
    Non-ADMIN users are scoped to their hotel_id.
    """
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool

    # Build dynamic query
    conditions = []
    params = []
    param_idx = 1

    # Hotel scope
    effective_hotel_id = hotel_id if user.role == Role.ADMIN and hotel_id else user.hotel_id
    conditions.append(f"c.hotel_id = ${param_idx}")
    params.append(effective_hotel_id)
    param_idx += 1

    if status_filter:
        conditions.append(f"c.current_state = ${param_idx}")
        params.append(status_filter)
        param_idx += 1

    if date_from:
        conditions.append(f"c.created_at >= ${param_idx}")
        params.append(date_from)
        param_idx += 1

    if date_to:
        conditions.append(f"c.created_at <= ${param_idx}")
        params.append(date_to)
        param_idx += 1

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * per_page

    query = f"""
        SELECT c.id, c.hotel_id, c.phone_display, c.language, c.current_state,
               c.current_intent, c.risk_flags, c.is_active,
               c.last_message_at, c.created_at,
               (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
        FROM conversations c
        WHERE {where_clause}
        ORDER BY c.last_message_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([per_page, offset])

    async with db.acquire() as conn:
        rows = await conn.fetch(query, *params)
        # Also get total count
        count_query = f"SELECT COUNT(*) FROM conversations c WHERE {where_clause}"
        total = await conn.fetchval(count_query, *params[:param_idx - 1])

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
```

### 5.2 Conversation detail with messages

```python
@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    request: Request,
    user: TokenData = Depends(get_current_user),
):
    """
    GET /api/v1/admin/conversations/{id}
    Returns conversation detail with all messages.
    """
    check_permission(user, "conversations:read")
    db = request.app.state.db_pool

    async with db.acquire() as conn:
        conv = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1", conversation_id,
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Scope check
        if user.role != Role.ADMIN and conv["hotel_id"] != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")

        messages = await conn.fetch(
            """
            SELECT id, role, content, internal_json, tool_calls, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            """,
            conversation_id,
        )

    return {
        "conversation": dict(conv),
        "messages": [dict(m) for m in messages],
    }
```

---

## Step 6: Implement Holds Management Endpoints

### 6.1 List all holds (unified view)

```python
@router.get("/holds")
async def list_holds(
    request: Request,
    user: TokenData = Depends(get_current_user),
    hold_type: str | None = Query(None, description="stay, restaurant, or transfer"),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/admin/holds
    Lists all holds (stay + restaurant + transfer) in a unified view.
    Filterable by type and status.
    """
    check_permission(user, "holds:read")
    db = request.app.state.db_pool

    hotel_filter = "" if user.role == Role.ADMIN else f"AND hotel_id = {user.hotel_id}"
    status_clause = f"AND status = '{status_filter}'" if status_filter else ""

    queries = []
    if hold_type in (None, "stay"):
        queries.append(f"""
            SELECT hold_id, 'stay' AS type, hotel_id, status, draft_json,
                   approved_by, created_at, conversation_id
            FROM stay_holds WHERE 1=1 {hotel_filter} {status_clause}
        """)
    if hold_type in (None, "restaurant"):
        queries.append(f"""
            SELECT hold_id, 'restaurant' AS type, hotel_id, status,
                   json_build_object('date', date, 'time', time, 'party_size', party_size, 'guest_name', guest_name, 'area', area) AS draft_json,
                   approved_by, created_at, conversation_id
            FROM restaurant_holds WHERE 1=1 {hotel_filter} {status_clause}
        """)
    if hold_type in (None, "transfer"):
        queries.append(f"""
            SELECT hold_id, 'transfer' AS type, hotel_id, status,
                   json_build_object('route', route, 'date', date, 'time', time, 'pax_count', pax_count, 'guest_name', guest_name, 'price_eur', price_eur) AS draft_json,
                   approved_by, created_at, conversation_id
            FROM transfer_holds WHERE 1=1 {hotel_filter} {status_clause}
        """)

    union_query = " UNION ALL ".join(queries) + f" ORDER BY created_at DESC LIMIT {per_page} OFFSET {(page - 1) * per_page}"

    async with db.acquire() as conn:
        rows = await conn.fetch(union_query)

    return {"items": [dict(row) for row in rows], "page": page, "per_page": per_page}
```

**Important**: The above approach uses string formatting for illustration. In production, use parameterized queries to avoid SQL injection. Refactor the hotel_id and status filters to use `$N` parameters.

### 6.2 Approve a hold

```python
class ApproveRequest(BaseModel):
    notes: str | None = None


@router.post("/holds/{hold_id}/approve")
async def approve_hold(
    hold_id: str,
    body: ApproveRequest,
    request: Request,
    user: TokenData = Depends(get_current_user),
):
    """
    POST /api/v1/admin/holds/{hold_id}/approve
    Approves a hold. Triggers next step based on hold type:
    - STAY: calls booking.create_reservation via Elektraweb adapter
    - RESTAURANT: updates status to APPROVED, sends confirmation
    - TRANSFER: updates status to APPROVED, sends confirmation

    After approval, injects a system message into the conversation
    so the LLM can react on the next guest message.
    """
    check_permission(user, "holds:approve")
    db = request.app.state.db_pool

    # Determine hold type by prefix
    if hold_id.startswith("S_HOLD_"):
        table = "stay_holds"
        hold_type = "stay"
    elif hold_id.startswith("R_HOLD_"):
        table = "restaurant_holds"
        hold_type = "restaurant"
    elif hold_id.startswith("TR_HOLD_"):
        table = "transfer_holds"
        hold_type = "transfer"
    else:
        raise HTTPException(status_code=400, detail="Unknown hold_id prefix")

    async with db.acquire() as conn:
        # Fetch the hold
        row = await conn.fetchrow(
            f"SELECT * FROM {table} WHERE hold_id = $1", hold_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Hold not found")

        if row["status"] != HoldStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=409,
                detail=f"Hold is not pending approval (current: {row['status']})",
            )

        # Hotel scope check
        if user.role != Role.ADMIN and row["hotel_id"] != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update hold status
        await conn.execute(
            f"""
            UPDATE {table}
            SET status = $1, approved_by = $2, approved_at = now(), updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.APPROVED,
            user.username,
            hold_id,
        )

        # Update approval_requests table
        await conn.execute(
            """
            UPDATE approval_requests
            SET status = 'APPROVED', decided_by_role = $1, decided_by_name = $2, decided_at = now()
            WHERE reference_id = $3 AND status = 'REQUESTED'
            """,
            user.role.value,
            user.username,
            hold_id,
        )

    # Trigger next step based on hold type
    # This will be handled by the webhook handler (Task 10)
    # For now, publish an event to be processed
    # await request.app.state.event_bus.publish("hold.approved", {
    #     "hold_id": hold_id, "hold_type": hold_type, "approved_by": user.username
    # })

    return {"status": "approved", "hold_id": hold_id, "hold_type": hold_type}
```

### 6.3 Reject a hold

```python
class RejectRequest(BaseModel):
    reason: str


@router.post("/holds/{hold_id}/reject")
async def reject_hold(
    hold_id: str,
    body: RejectRequest,
    request: Request,
    user: TokenData = Depends(get_current_user),
):
    """
    POST /api/v1/admin/holds/{hold_id}/reject
    Rejects a hold with a reason. Sends message to guest with alternatives.
    """
    check_permission(user, "holds:reject")
    db = request.app.state.db_pool

    if hold_id.startswith("S_HOLD_"):
        table = "stay_holds"
    elif hold_id.startswith("R_HOLD_"):
        table = "restaurant_holds"
    elif hold_id.startswith("TR_HOLD_"):
        table = "transfer_holds"
    else:
        raise HTTPException(status_code=400, detail="Unknown hold_id prefix")

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            f"SELECT * FROM {table} WHERE hold_id = $1", hold_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Hold not found")

        if row["status"] != HoldStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=409,
                detail=f"Hold is not pending approval (current: {row['status']})",
            )

        if user.role != Role.ADMIN and row["hotel_id"] != user.hotel_id:
            raise HTTPException(status_code=403, detail="Access denied")

        await conn.execute(
            f"""
            UPDATE {table}
            SET status = $1, rejected_reason = $2, updated_at = now()
            WHERE hold_id = $3
            """,
            HoldStatus.REJECTED,
            body.reason,
            hold_id,
        )

        await conn.execute(
            """
            UPDATE approval_requests
            SET status = 'REJECTED', decided_by_role = $1, decided_by_name = $2, decided_at = now()
            WHERE reference_id = $3 AND status = 'REQUESTED'
            """,
            user.role.value,
            user.username,
            hold_id,
        )

    return {"status": "rejected", "hold_id": hold_id, "reason": body.reason}
```

---

## Step 7: Implement Ticket Management Endpoints

### 7.1 List tickets

```python
@router.get("/tickets")
async def list_tickets(
    request: Request,
    user: TokenData = Depends(get_current_user),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/admin/tickets
    Lists tickets with status and priority filters.
    Non-ADMIN users see only tickets assigned to their role.
    """
    check_permission(user, "tickets:read")
    db = request.app.state.db_pool

    conditions = []
    params = []
    param_idx = 1

    # Hotel scope
    conditions.append(f"hotel_id = ${param_idx}")
    params.append(user.hotel_id)
    param_idx += 1

    # Non-ADMIN: only see tickets for their role
    if user.role != Role.ADMIN:
        conditions.append(f"assigned_to_role = ${param_idx}")
        params.append(user.role.value)
        param_idx += 1

    if status_filter:
        conditions.append(f"status = ${param_idx}")
        params.append(status_filter)
        param_idx += 1

    if priority:
        conditions.append(f"priority = ${param_idx}")
        params.append(priority)
        param_idx += 1

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * per_page

    query = f"""
        SELECT ticket_id, hotel_id, conversation_id, reason,
               transcript_summary, priority, dedupe_key, status,
               assigned_to_role, assigned_to_name, resolved_at, created_at
        FROM tickets
        WHERE {where_clause}
        ORDER BY
            CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            created_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([per_page, offset])

    async with db.acquire() as conn:
        rows = await conn.fetch(query, *params)
        count_query = f"SELECT COUNT(*) FROM tickets WHERE {where_clause}"
        total = await conn.fetchval(count_query, *params[:param_idx - 1])

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
```

### 7.2 Update ticket

```python
class TicketUpdate(BaseModel):
    status: str | None = None  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    assigned_to_role: str | None = None
    assigned_to_name: str | None = None


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    request: Request,
    user: TokenData = Depends(get_current_user),
):
    """
    PUT /api/v1/admin/tickets/{ticket_id}
    Update ticket status, assignment.
    ADMIN can update any ticket. OPS can update tickets assigned to them.
    """
    check_permission(user, "tickets:write")
    db = request.app.state.db_pool

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tickets WHERE ticket_id = $1", ticket_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Scope check for non-ADMIN
        if user.role != Role.ADMIN:
            if row["hotel_id"] != user.hotel_id:
                raise HTTPException(status_code=403, detail="Access denied")
            if row["assigned_to_role"] != user.role.value:
                raise HTTPException(status_code=403, detail="Ticket not assigned to your role")

        # Build update
        updates = ["updated_at = now()"]
        params = []
        param_idx = 1

        if body.status:
            updates.append(f"status = ${param_idx}")
            params.append(body.status)
            param_idx += 1
            if body.status in ("RESOLVED", "CLOSED"):
                updates.append("resolved_at = now()")

        if body.assigned_to_role:
            updates.append(f"assigned_to_role = ${param_idx}")
            params.append(body.assigned_to_role)
            param_idx += 1

        if body.assigned_to_name:
            updates.append(f"assigned_to_name = ${param_idx}")
            params.append(body.assigned_to_name)
            param_idx += 1

        if not params:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(updates)
        params.append(ticket_id)
        query = f"UPDATE tickets SET {set_clause} WHERE ticket_id = ${param_idx}"

        await conn.execute(query, *params)

    return {"status": "updated", "ticket_id": ticket_id}
```

---

## Step 8: Register Router and Middleware in main.py

### File: `src/velox/main.py` (modify)

```python
from velox.api.routes.admin import router as admin_router
from velox.api.middleware.rate_limiter import RateLimitMiddleware

# In lifespan or after app creation:
app.include_router(admin_router, prefix="/api/v1")

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)
```

---

## Step 9: Update `__init__.py` Files

### File: `src/velox/api/routes/__init__.py`
```python
# Routes package
```

### File: `src/velox/api/middleware/__init__.py`
```python
# Middleware package
```

---

## Validation Checklist

1. **Login**: POST to `/api/v1/admin/login` with valid credentials returns a JWT token.
2. **Auth middleware**: Requests without `Authorization: Bearer <token>` header return 401.
3. **Expired token**: Tokens past `admin_jwt_expire_minutes` return 401.
4. **RBAC**: ADMIN can access all endpoints. SALES cannot update hotel profiles (403). CHEF can only view restaurant holds.
5. **Hotel scoping**: Non-ADMIN users only see data from their `hotel_id`.
6. **Rate limiting**: After 100 webhook requests in 1 minute from the same IP, the 101st returns 429.
7. **Hold approval**: Approving a `PENDING_APPROVAL` hold changes status to `APPROVED` and updates `approval_requests`.
8. **Hold rejection**: Rejecting sets status to `REJECTED` with a reason.
9. **Double approve**: Approving an already-approved hold returns 409 Conflict.
10. **Ticket management**: Tickets can be filtered by status/priority. Updates work correctly.
11. **Pagination**: All list endpoints support `page` and `per_page` with correct total counts.

---

## File Summary

| File | Action |
|------|--------|
| `src/velox/api/middleware/auth.py` | **Create** |
| `src/velox/api/middleware/rate_limiter.py` | **Create** |
| `src/velox/api/routes/admin.py` | **Create** |
| `src/velox/api/middleware/__init__.py` | **Modify** (ensure importable) |
| `src/velox/api/routes/__init__.py` | **Modify** (ensure importable) |
| `src/velox/main.py` | **Modify** (register router + middleware) |

## Expected Outcome
- Admin panel can authenticate via JWT and access role-scoped endpoints
- Hotels, conversations, holds, and tickets are all manageable through the REST API
- Rate limiting protects webhook endpoints from abuse
- RBAC ensures each role only accesses what they should
