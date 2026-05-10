"""Admin API routes for response review and reporting."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from velox.api.middleware.auth import (
    TokenData,
    check_permission,
    get_current_user,
    resolve_hotel_scope,
)
from velox.core.response_review import ResponseReviewService
from velox.models.response_review import (
    ResponseReviewClassification,
    ResponseReviewClassifyRequest,
    ResponseReviewCreateRequest,
    ResponseReviewDetail,
    ResponseReviewErrorType,
    ResponseReviewListResponse,
    ResponseReviewStatus,
)

router = APIRouter(prefix="/admin/response-reviews", tags=["admin-response-reviews"])

HotelIdQuery = Annotated[int | None, Query()]
StatusFilterQuery = Annotated[ResponseReviewStatus | None, Query(alias="status")]
ClassificationQuery = Annotated[ResponseReviewClassification | None, Query()]
ErrorTypeQuery = Annotated[ResponseReviewErrorType | None, Query()]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]


def _display_name(user: TokenData) -> str | None:
    return user.display_name.strip() if user.display_name and user.display_name.strip() else None


def _service(request: Request) -> ResponseReviewService:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Veritabanı hazır değil.")
    return ResponseReviewService(pool)


@router.post("", response_model=ResponseReviewDetail)
async def create_response_review(
    payload: ResponseReviewCreateRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> ResponseReviewDetail:
    """Report one Operations Desk response and create a review queue item."""
    check_permission(user, "response_reviews:write")
    effective_hotel_id = resolve_hotel_scope(user, payload.hotel_id)
    try:
        return await _service(request).create_review(
            payload,
            hotel_id=effective_hotel_id,
            reporter_user_id=user.user_id,
            reporter_username=user.username,
            reporter_display_name=_display_name(user),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Response Review migration uygulanmamış.",
        ) from exc


@router.get("", response_model=ResponseReviewListResponse)
async def list_response_reviews(
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: HotelIdQuery = None,
    status_filter: StatusFilterQuery = None,
    classification: ClassificationQuery = None,
    error_type: ErrorTypeQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> ResponseReviewListResponse:
    """List response reviews for the active hotel scope."""
    check_permission(user, "response_reviews:read")
    effective_hotel_id = resolve_hotel_scope(user, hotel_id)
    try:
        return await _service(request).list_reviews(
            hotel_id=effective_hotel_id,
            status_filter=status_filter,
            classification=classification,
            error_type=error_type,
            limit=limit,
            offset=offset,
        )
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Response Review migration uygulanmamış.",
        ) from exc


@router.get("/{review_id}", response_model=ResponseReviewDetail)
async def get_response_review(
    review_id: UUID,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: HotelIdQuery = None,
) -> ResponseReviewDetail:
    """Return one response review detail."""
    check_permission(user, "response_reviews:read")
    effective_hotel_id = resolve_hotel_scope(user, hotel_id)
    try:
        detail = await _service(request).get_review(review_id=review_id, hotel_id=effective_hotel_id)
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Response Review migration uygulanmamış.",
        ) from exc
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapor kaydı bulunamadı.")
    return detail


@router.post("/{review_id}/classify", response_model=ResponseReviewDetail)
async def classify_response_review(
    review_id: UUID,
    payload: ResponseReviewClassifyRequest,
    request: Request,
    user: Annotated[TokenData, Depends(get_current_user)],
    hotel_id: HotelIdQuery = None,
) -> ResponseReviewDetail:
    """Classify one response review and export it into feedback files."""
    check_permission(user, "response_reviews:write")
    effective_hotel_id = resolve_hotel_scope(user, hotel_id)
    try:
        return await _service(request).classify_review(
            review_id,
            payload,
            hotel_id=effective_hotel_id,
            reviewer_user_id=user.user_id,
            reviewer_username=user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Response Review migration uygulanmamış.",
        ) from exc
