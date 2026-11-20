"""Inventory use cases. Every read and write is scoped to the authenticated user."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError, StateConflictError, ValidationError
from app.domain.expiry import EXPIRING_WINDOW_DAYS, current_date, inventory_status
from app.domain.inventory import reason_direction_error
from app.models.inventory import InventoryItem, InventoryTransaction
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.inventory import (
    InventoryCreatePayload,
    InventoryListResponse,
    InventoryResponse,
    InventoryUpdatePayload,
)


class InventoryService:
    def __init__(self, inventory: InventoryRepository | None = None) -> None:
        self._inventory = inventory or InventoryRepository()

    def create(
        self, db: Session, user_id: UUID, payload: InventoryCreatePayload
    ) -> InventoryResponse:
        if payload.ingredient_id is not None and not self._inventory.ingredient_exists(
            db, payload.ingredient_id
        ):
            raise ResourceNotFoundError("Ingredient was not found in the catalog")

        item = InventoryItem(
            user_id=user_id,
            ingredient_id=payload.ingredient_id,
            display_name=payload.display_name,
            quantity=payload.quantity,
            unit=payload.unit,
            purchase_date=payload.purchase_date,
            expiry_date=payload.expiry_date,
            storage_location=payload.storage_location,
            version=1,
        )
        self._inventory.add(db, item)
        db.flush()
        self._inventory.add_transaction(
            db,
            InventoryTransaction(
                user_id=user_id,
                inventory_item_id=item.id,
                delta_quantity=payload.quantity,
                unit=payload.unit,
                reason="add",
                source_type="manual",
            ),
        )
        db.commit()
        db.refresh(item)
        return self._to_response(item, current_date())

    def get(self, db: Session, user_id: UUID, item_id: UUID) -> InventoryResponse:
        item = self._inventory.get(db, user_id, item_id)
        if item is None:
            raise ResourceNotFoundError("Inventory item was not found")
        return self._to_response(item, current_date())

    def update(
        self,
        db: Session,
        user_id: UUID,
        item_id: UUID,
        payload: InventoryUpdatePayload,
    ) -> InventoryResponse:
        item = self._inventory.get(db, user_id, item_id)
        if item is None:
            raise ResourceNotFoundError("Inventory item was not found")
        if payload.expected_version != item.version:
            raise StateConflictError("Inventory item was modified by another request")

        provided = payload.model_fields_set
        values: dict[str, object] = {}

        if "display_name" in provided:
            if payload.display_name is None:
                raise ValidationError("display_name must not be null")
            values["display_name"] = payload.display_name
        metadata_changed = False
        if "purchase_date" in provided:
            values["purchase_date"] = payload.purchase_date
            metadata_changed = True
        if "expiry_date" in provided:
            values["expiry_date"] = payload.expiry_date
            metadata_changed = True
        if "storage_location" in provided:
            values["storage_location"] = payload.storage_location
            metadata_changed = True

        quantity_delta: Decimal | None = None
        if "quantity" in provided:
            if payload.quantity is None:
                raise ValidationError("quantity must not be null")
            if payload.quantity != item.quantity:
                quantity_delta = payload.quantity - item.quantity
                values["quantity"] = payload.quantity

        if quantity_delta is not None:
            if payload.reason is None:
                raise ValidationError("reason is required when quantity changes")
            direction_error = reason_direction_error(payload.reason, quantity_delta)
            if direction_error is not None:
                raise ValidationError(direction_error)
        elif metadata_changed and payload.reason is None:
            raise ValidationError("reason is required when updating dates or storage location")

        if not values:
            return self._to_response(item, current_date())

        affected = self._inventory.update_fields(
            db,
            user_id=user_id,
            item_id=item_id,
            expected_version=item.version,
            values=values,
        )
        if affected == 0:
            raise StateConflictError("Inventory item was modified by another request")

        if quantity_delta is not None:
            self._inventory.add_transaction(
                db,
                InventoryTransaction(
                    user_id=user_id,
                    inventory_item_id=item.id,
                    delta_quantity=quantity_delta,
                    unit=item.unit,
                    reason=payload.reason,
                    source_type="manual",
                ),
            )
        elif metadata_changed:
            # 仅日期/存储位置变化：delta=0 不影响库存汇总，只为审计留痕。
            self._inventory.add_transaction(
                db,
                InventoryTransaction(
                    user_id=user_id,
                    inventory_item_id=item.id,
                    delta_quantity=Decimal("0.000"),
                    unit=item.unit,
                    reason="adjust",
                    source_type="manual",
                ),
            )
        db.commit()
        db.refresh(item)
        return self._to_response(item, current_date())

    def archive(self, db: Session, user_id: UUID, item_id: UUID) -> None:
        item = self._inventory.get(db, user_id, item_id, include_archived=True)
        if item is None:
            raise ResourceNotFoundError("Inventory item was not found")
        if item.archived_at is not None:
            # 重复归档按幂等成功处理，并保留原始 archived_at。
            return

        affected = self._inventory.update_fields(
            db,
            user_id=user_id,
            item_id=item_id,
            expected_version=item.version,
            values={"archived_at": datetime.now(UTC)},
        )
        if affected == 0:
            db.refresh(item)
            if item.archived_at is not None:
                return
            raise StateConflictError("Inventory item was modified by another request")
        db.commit()

    def list_items(
        self,
        db: Session,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
        name: str | None = None,
        category: str | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> InventoryListResponse:
        today = current_date()
        items, total = self._inventory.list_items(
            db,
            user_id,
            today=today,
            page=page,
            page_size=page_size,
            name=name,
            category=category,
            status=status,
            include_archived=include_archived,
        )
        return InventoryListResponse(
            items=[self._to_response(item, today) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def list_expiring(self, db: Session, user_id: UUID) -> list[InventoryResponse]:
        today = current_date()
        items = self._inventory.list_expiring(
            db, user_id, today=today, window_days=EXPIRING_WINDOW_DAYS
        )
        return [self._to_response(item, today) for item in items]

    @staticmethod
    def _to_response(item: InventoryItem, today: date) -> InventoryResponse:
        return InventoryResponse(
            id=item.id,
            ingredient_id=item.ingredient_id,
            display_name=item.display_name,
            quantity=item.quantity,
            unit=item.unit,
            purchase_date=item.purchase_date,
            expiry_date=item.expiry_date,
            storage_location=item.storage_location,
            status=inventory_status(item.expiry_date, today),
            version=item.version,
            archived_at=item.archived_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
