"""Read-only aggregate queries for the dashboard."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryItem
from app.repositories.inventory_repository import InventoryRepository


class DashboardRepository:
    def summary(self, db: Session, user_id: UUID, today: date) -> tuple[int, int, int]:
        base_conditions = [
            InventoryItem.user_id == user_id,
            InventoryItem.archived_at.is_(None),
            InventoryItem.quantity > Decimal("0"),
        ]
        expiring_conditions = and_(
            *InventoryRepository.status_conditions("expiring", today)
        )
        expired_conditions = and_(*InventoryRepository.status_conditions("expired", today))
        statement = select(
            func.count(InventoryItem.id).label("inventory_count"),
            func.count(InventoryItem.id).filter(expiring_conditions).label("expiring_count"),
            func.count(InventoryItem.id).filter(expired_conditions).label("expired_count"),
        ).where(*base_conditions)
        row = db.execute(statement).one()
        return int(row.inventory_count), int(row.expiring_count), int(row.expired_count)
