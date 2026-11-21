"""User-scoped persistence for meal plans, their ingredients and confirmations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.meal_plan import MealPlan, MealPlanIngredient, MealPlanItem
from app.models.meal_plan_confirmation import MealPlanConfirmation


class MealPlanRepository:
    """Every query is filtered by user_id so callers cannot cross user boundaries."""

    def get_for_update(self, db: Session, user_id: UUID, plan_id: UUID) -> MealPlan | None:
        """Lock the plan row so two confirmations of the same plan serialize."""
        statement = (
            select(MealPlan)
            .where(MealPlan.id == plan_id, MealPlan.user_id == user_id)
            .with_for_update()
        )
        return db.scalar(statement)

    def get_for_shopping_import(
        self, db: Session, user_id: UUID, plan_id: UUID
    ) -> MealPlan | None:
        """Lock one owned plan and load the persisted ingredient lines for an import."""
        statement = (
            select(MealPlan)
            .options(
                selectinload(MealPlan.items)
                .selectinload(MealPlanItem.ingredients)
                .selectinload(MealPlanIngredient.inventory_item),
            )
            .where(MealPlan.id == plan_id, MealPlan.user_id == user_id)
            .with_for_update()
        )
        return db.scalar(statement)

    def get_detail(self, db: Session, user_id: UUID, plan_id: UUID) -> MealPlan | None:
        """Return a user-scoped plan with its dishes and persisted ingredient lines."""
        statement = (
            select(MealPlan)
            .options(
                selectinload(MealPlan.items).selectinload(MealPlanItem.ingredients),
            )
            .where(MealPlan.id == plan_id, MealPlan.user_id == user_id)
        )
        return db.scalar(statement)

    def get_confirmation(
        self, db: Session, user_id: UUID, idempotency_key: str
    ) -> MealPlanConfirmation | None:
        statement = select(MealPlanConfirmation).where(
            MealPlanConfirmation.user_id == user_id,
            MealPlanConfirmation.idempotency_key == idempotency_key,
        )
        return db.scalar(statement)

    def add_confirmation(self, db: Session, confirmation: MealPlanConfirmation) -> None:
        db.add(confirmation)

    def list_ingredients(
        self, db: Session, plan_id: UUID, ingredient_ids: list[UUID] | None = None
    ) -> list[MealPlanIngredient]:
        statement = (
            select(MealPlanIngredient)
            .join(MealPlanItem, MealPlanIngredient.meal_plan_item_id == MealPlanItem.id)
            .where(MealPlanItem.meal_plan_id == plan_id)
        )
        if ingredient_ids is not None:
            statement = statement.where(MealPlanIngredient.id.in_(ingredient_ids))
        return list(db.scalars(statement.order_by(MealPlanIngredient.id)))

    def mark_confirmed(self, db: Session, plan: MealPlan, confirmed_at: object) -> None:
        plan.status = "confirmed"
        plan.confirmed_at = confirmed_at
