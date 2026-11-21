"""Shopping-list endpoints scoped to the authenticated user."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.shopping import (
    ShoppingImportFromMealPlanPayload,
    ShoppingImportFromMealPlanResponse,
    ShoppingItemCreatePayload,
    ShoppingItemListResponse,
    ShoppingItemResponse,
    ShoppingItemStatusUpdatePayload,
    ShoppingStatus,
)
from app.services.shopping_service import ShoppingService

router = APIRouter(prefix="/shopping-items", tags=["shopping-items"])


@router.get("", response_model=ShoppingItemListResponse)
def list_shopping_items(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    shopping_status: Annotated[ShoppingStatus | None, Query(alias="status")] = None,
) -> ShoppingItemListResponse:
    return ShoppingService().list_items(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        status=shopping_status,
    )


@router.post("", response_model=ShoppingItemResponse, status_code=status.HTTP_201_CREATED)
def create_shopping_item(
    payload: ShoppingItemCreatePayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ShoppingItemResponse:
    return ShoppingService().create(db, current_user.id, payload)


@router.post(
    "/import-from-meal-plan",
    response_model=ShoppingImportFromMealPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_from_meal_plan(
    payload: ShoppingImportFromMealPlanPayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ShoppingImportFromMealPlanResponse:
    return ShoppingService().import_from_meal_plan(db, current_user.id, payload.meal_plan_id)


@router.patch("/{item_id}", response_model=ShoppingItemResponse)
def update_shopping_item_status(
    item_id: UUID,
    payload: ShoppingItemStatusUpdatePayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ShoppingItemResponse:
    return ShoppingService().update_status(db, current_user.id, item_id, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    ShoppingService().delete(db, current_user.id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
