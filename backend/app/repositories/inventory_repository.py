"""User-scoped persistence queries for inventory items and transactions."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.ingredient import IngredientCatalog
from app.models.inventory import InventoryItem, InventoryTransaction


class InventoryRepository:
    """Every query is filtered by user_id so callers cannot cross user boundaries."""

    def get(
        self,
        db: Session,
        user_id: UUID,
        item_id: UUID,
        *,
        include_archived: bool = False,
    ) -> InventoryItem | None:
        statement = select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.user_id == user_id,
        )
        if not include_archived:
            statement = statement.where(InventoryItem.archived_at.is_(None))
        return db.scalar(statement)

    def ingredient_exists(self, db: Session, ingredient_id: UUID) -> bool:
        return (
            db.scalar(select(IngredientCatalog.id).where(IngredientCatalog.id == ingredient_id))
            is not None
        )

    def list_items(
        self,
        db: Session,
        user_id: UUID,
        *,
        today: date,
        page: int,
        page_size: int,
        name: str | None = None,
        category: str | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> tuple[list[InventoryItem], int]:
        conditions = [InventoryItem.user_id == user_id]
        if not include_archived:
            conditions.append(InventoryItem.archived_at.is_(None))
        if name:
            conditions.append(InventoryItem.display_name.ilike(f"%{name}%"))
        if category:
            conditions.append(IngredientCatalog.category == category)
        conditions.extend(self._status_conditions(status, today))

        statement = select(InventoryItem)
        count_statement = select(func.count()).select_from(InventoryItem)
        if category:
            statement = statement.join(
                IngredientCatalog, InventoryItem.ingredient_id == IngredientCatalog.id
            )
            count_statement = count_statement.join(
                IngredientCatalog, InventoryItem.ingredient_id == IngredientCatalog.id
            )

        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)
        ordered = (
            statement.order_by(
                InventoryItem.expiry_date.asc().nulls_last(),
                InventoryItem.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(db.scalars(ordered))
        total = db.scalar(count_statement) or 0
        return items, total

    def list_expiring(
        self,
        db: Session,
        user_id: UUID,
        *,
        today: date,
        window_days: int,
    ) -> list[InventoryItem]:
        statement = (
            select(InventoryItem)
            .where(
                InventoryItem.user_id == user_id,
                InventoryItem.archived_at.is_(None),
                InventoryItem.quantity > Decimal("0"),
                InventoryItem.expiry_date.is_not(None),
                InventoryItem.expiry_date <= today + timedelta(days=window_days),
            )
            .order_by(InventoryItem.expiry_date.asc())
        )
        return list(db.scalars(statement))

    def add(self, db: Session, item: InventoryItem) -> None:
        db.add(item)

    def add_transaction(self, db: Session, transaction: InventoryTransaction) -> None:
        db.add(transaction)

    def update_fields(
        self,
        db: Session,
        *,
        user_id: UUID,
        item_id: UUID,
        expected_version: int,
        values: dict[str, Any],
    ) -> int:
        """Optimistic update guarded by version; returns affected rows."""
        statement = (
            update(InventoryItem)
            .where(
                InventoryItem.id == item_id,
                InventoryItem.user_id == user_id,
                InventoryItem.version == expected_version,
            )
            .values(**values, version=expected_version + 1)
        )
        result = db.execute(statement.execution_options(synchronize_session=False))
        return int(result.rowcount or 0)

    def list_transactions(
        self, db: Session, user_id: UUID, item_id: UUID
    ) -> list[InventoryTransaction]:
        statement = (
            select(InventoryTransaction)
            .where(
                InventoryTransaction.user_id == user_id,
                InventoryTransaction.inventory_item_id == item_id,
            )
            .order_by(InventoryTransaction.created_at.asc())
        )
        return list(db.scalars(statement))

    @staticmethod
    def _status_conditions(status: str | None, today: date) -> list[Any]:
        if status == "expired":
            return [InventoryItem.expiry_date.is_not(None), InventoryItem.expiry_date < today]
        if status == "expiring":
            return [
                InventoryItem.expiry_date.is_not(None),
                InventoryItem.expiry_date >= today,
                InventoryItem.expiry_date <= today + timedelta(days=3),
            ]
        if status == "normal":
            return [
                or_(
                    InventoryItem.expiry_date.is_(None),
                    InventoryItem.expiry_date > today + timedelta(days=3),
                )
            ]
        return []
