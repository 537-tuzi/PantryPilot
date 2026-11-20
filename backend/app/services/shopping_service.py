"""Shopping-list use cases, including user-initiated missing-ingredient imports."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError, StateConflictError
from app.domain.shopping import can_transition
from app.models.shopping import ShoppingItem
from app.repositories.meal_plan_repository import MealPlanRepository
from app.repositories.shopping_repository import ShoppingRepository
from app.schemas.shopping import (
    ShoppingImportFromMealPlanResponse,
    ShoppingItemCreatePayload,
    ShoppingItemListResponse,
    ShoppingItemResponse,
    ShoppingItemStatusUpdatePayload,
)


@dataclass
class _ImportCandidate:
    display_name: str
    ingredient_id: UUID | None
    quantity: Decimal
    unit: str


def _item_key(ingredient_id: UUID | None, display_name: str, unit: str) -> tuple[str, str, str]:
    """Use a catalog ID when present; otherwise compare only normalized exact names."""
    if ingredient_id is not None:
        return ("ingredient", str(ingredient_id), unit)
    return ("display_name", display_name.strip().casefold(), unit)


class ShoppingService:
    def __init__(
        self,
        shopping: ShoppingRepository | None = None,
        plans: MealPlanRepository | None = None,
    ) -> None:
        self._shopping = shopping or ShoppingRepository()
        self._plans = plans or MealPlanRepository()

    def list_items(
        self,
        db: Session,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
        status: str | None,
    ) -> ShoppingItemListResponse:
        items, total = self._shopping.list_items(
            db, user_id, page=page, page_size=page_size, status=status
        )
        return ShoppingItemListResponse(
            items=[self._to_response(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def create(
        self, db: Session, user_id: UUID, payload: ShoppingItemCreatePayload
    ) -> ShoppingItemResponse:
        if payload.ingredient_id is not None and not self._shopping.ingredient_exists(
            db, payload.ingredient_id
        ):
            raise ResourceNotFoundError("Ingredient was not found in the catalog")

        item = ShoppingItem(
            user_id=user_id,
            display_name=payload.display_name,
            ingredient_id=payload.ingredient_id,
            quantity=payload.quantity,
            unit=payload.unit,
            status="pending",
        )
        self._shopping.add(db, item)
        self._commit(db)
        db.refresh(item)
        return self._to_response(item)

    def update_status(
        self,
        db: Session,
        user_id: UUID,
        item_id: UUID,
        payload: ShoppingItemStatusUpdatePayload,
    ) -> ShoppingItemResponse:
        item = self._get_owned(db, user_id, item_id)
        if not can_transition(item.status, payload.status):
            raise StateConflictError(
                f"Cannot change shopping item status from {item.status} to {payload.status}"
            )
        if item.status == payload.status:
            return self._to_response(item)

        item.status = payload.status
        self._commit(db)
        db.refresh(item)
        return self._to_response(item)

    def delete(self, db: Session, user_id: UUID, item_id: UUID) -> None:
        """Soft delete: cancel the item so its history remains queryable."""
        item = self._get_owned(db, user_id, item_id)
        if item.status == "cancelled":
            return

        item.status = "cancelled"
        self._commit(db)

    def import_from_meal_plan(
        self, db: Session, user_id: UUID, meal_plan_id: UUID
    ) -> ShoppingImportFromMealPlanResponse:
        # Locking the plan serializes imports for the same source plan, so an existing-item
        # check and inserts below form one transactionally consistent operation.
        plan = self._plans.get_for_shopping_import(db, user_id, meal_plan_id)
        if plan is None:
            raise ResourceNotFoundError("Meal plan was not found")
        if plan.status != "confirmed":
            raise StateConflictError("Only confirmed meal plans can be imported")

        candidates: dict[tuple[str, str, str], _ImportCandidate] = {}
        skipped_count = 0
        for plan_item in plan.items:
            for ingredient in plan_item.ingredients:
                if not ingredient.is_missing:
                    continue
                actual_quantity = (
                    ingredient.actual_quantity
                    if ingredient.actual_quantity is not None
                    else Decimal("0")
                )
                gap = ingredient.required_quantity - actual_quantity
                if gap <= 0:
                    skipped_count += 1
                    continue

                inventory_item = ingredient.inventory_item
                ingredient_id = inventory_item.ingredient_id if inventory_item is not None else None
                key = _item_key(ingredient_id, ingredient.display_name, ingredient.unit)
                current = candidates.get(key)
                if current is None:
                    candidates[key] = _ImportCandidate(
                        display_name=ingredient.display_name,
                        ingredient_id=ingredient_id,
                        quantity=gap,
                        unit=ingredient.unit,
                    )
                else:
                    current.quantity += gap

        existing_keys = {
            _item_key(item.ingredient_id, item.display_name, item.unit)
            for item in self._shopping.list_imported_for_plan(db, user_id, plan.id)
        }
        created_count = 0
        try:
            for key, candidate in sorted(candidates.items(), key=lambda entry: entry[0]):
                if key in existing_keys:
                    skipped_count += 1
                    continue
                self._shopping.add(
                    db,
                    ShoppingItem(
                        user_id=user_id,
                        display_name=candidate.display_name,
                        ingredient_id=candidate.ingredient_id,
                        quantity=candidate.quantity,
                        unit=candidate.unit,
                        status="pending",
                        source_meal_plan_id=plan.id,
                    ),
                )
                created_count += 1

            if created_count:
                self._commit(db)
        except Exception:
            db.rollback()
            raise
        return ShoppingImportFromMealPlanResponse(
            meal_plan_id=plan.id,
            created_count=created_count,
            skipped_count=skipped_count,
        )

    def _get_owned(self, db: Session, user_id: UUID, item_id: UUID) -> ShoppingItem:
        item = self._shopping.get(db, user_id, item_id)
        if item is None:
            raise ResourceNotFoundError("Shopping item was not found")
        return item

    @staticmethod
    def _to_response(item: ShoppingItem) -> ShoppingItemResponse:
        return ShoppingItemResponse.model_validate(item)

    @staticmethod
    def _commit(db: Session) -> None:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
