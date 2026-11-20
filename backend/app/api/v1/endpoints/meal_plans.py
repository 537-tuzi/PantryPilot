"""Meal plan endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.errors import ValidationError
from app.db.session import get_db
from app.schemas.meal_plan import (
    MealPlanConfirmPayload,
    MealPlanConfirmResponse,
    MealPlanDetailResponse,
)
from app.services.meal_plan_service import MealPlanService

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


@router.get(
    "/{plan_id}",
    response_model=MealPlanDetailResponse,
    summary="Get one meal plan with dishes and ingredient allocations",
)
def get_meal_plan_detail(
    plan_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> MealPlanDetailResponse:
    return MealPlanService().get_detail(db, current_user.id, plan_id)


@router.post(
    "/{plan_id}/confirm",
    response_model=MealPlanConfirmResponse,
    summary="Confirm a draft meal plan and deduct inventory",
)
def confirm_meal_plan(
    plan_id: UUID,
    payload: MealPlanConfirmPayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> MealPlanConfirmResponse:
    try:
        normalized_key = str(UUID(idempotency_key.strip()))
    except ValueError:
        raise ValidationError("Idempotency-Key must be a valid UUID") from None
    return MealPlanService().confirm(db, current_user.id, plan_id, normalized_key, payload)
