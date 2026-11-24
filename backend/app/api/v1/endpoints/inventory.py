"""Inventory endpoints. All routes are scoped to the authenticated user."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.inventory import (
    InventoryCreatePayload,
    InventoryListResponse,
    InventoryResponse,
    InventoryUpdatePayload,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])

InventoryStatusFilter = Literal["normal", "expiring", "expired"]


@router.get("", response_model=InventoryListResponse)
def list_inventory(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    name: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[str | None, Query(max_length=100)] = None,
    inventory_status: Annotated[InventoryStatusFilter | None, Query(alias="status")] = None,
    include_archived: Annotated[bool, Query()] = False,
) -> InventoryListResponse:
    return InventoryService().list_items(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        name=name,
        category=category,
        status=inventory_status,
        include_archived=include_archived,
    )


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryCreatePayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InventoryResponse:
    return InventoryService().create(db, current_user.id, payload)


@router.get("/expiring", response_model=list[InventoryResponse])
def list_expiring_inventory(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[InventoryResponse]:
    return InventoryService().list_expiring(db, current_user.id)


@router.get("/categories", response_model=list[str])
def list_inventory_categories(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[str]:
    return InventoryService().list_categories(db)


@router.get("/{item_id}", response_model=InventoryResponse)
def get_inventory_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InventoryResponse:
    return InventoryService().get(db, current_user.id, item_id)


@router.patch("/{item_id}", response_model=InventoryResponse)
def update_inventory_item(
    item_id: UUID,
    payload: InventoryUpdatePayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InventoryResponse:
    return InventoryService().update(db, current_user.id, item_id, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_inventory_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    InventoryService().archive(db, current_user.id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
