"""User-scoped persistence queries for shopping items."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ingredient import IngredientCatalog
from app.models.shopping import ShoppingItem


class ShoppingRepository:
    def list_items(
        self,
        db: Session,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> tuple[list[ShoppingItem], int]:
        conditions = [ShoppingItem.user_id == user_id]
        if status is not None:
            conditions.append(ShoppingItem.status == status)

        statement = (
            select(ShoppingItem)
            .where(*conditions)
            .order_by(ShoppingItem.created_at.desc(), ShoppingItem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count()).select_from(ShoppingItem).where(*conditions)
        return list(db.scalars(statement)), int(db.scalar(count_statement) or 0)

    def get(self, db: Session, user_id: UUID, item_id: UUID) -> ShoppingItem | None:
        return db.scalar(
            select(ShoppingItem).where(ShoppingItem.id == item_id, ShoppingItem.user_id == user_id)
        )

    def ingredient_exists(self, db: Session, ingredient_id: UUID) -> bool:
        return (
            db.scalar(select(IngredientCatalog.id).where(IngredientCatalog.id == ingredient_id))
            is not None
        )

    def list_imported_for_plan(
        self, db: Session, user_id: UUID, meal_plan_id: UUID
    ) -> list[ShoppingItem]:
        statement = select(ShoppingItem).where(
            ShoppingItem.user_id == user_id,
            ShoppingItem.source_meal_plan_id == meal_plan_id,
        )
        return list(db.scalars(statement))

    @staticmethod
    def add(db: Session, item: ShoppingItem) -> None:
        db.add(item)

    @staticmethod
    def delete(db: Session, item: ShoppingItem) -> None:
        db.delete(item)
