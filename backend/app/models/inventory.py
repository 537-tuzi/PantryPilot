from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin
from app.models.enums import InventoryTransactionReason, SourceType

if TYPE_CHECKING:
    from app.models.ingredient import IngredientCatalog
    from app.models.meal_plan import MealPlanIngredient
    from app.models.meal_plan_confirmation import MealPlanConfirmation
    from app.models.user import User


class InventoryItem(TimestampMixin, Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_nonnegative"),
        Index("ix_inventory_items_user_id_expiry_date", "user_id", "expiry_date"),
        Index("ix_inventory_items_user_id_ingredient_id", "user_id", "ingredient_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    ingredient_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ingredient_catalog.id", ondelete="SET NULL"), nullable=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="inventory_items")
    ingredient: Mapped[IngredientCatalog | None] = relationship(back_populates="inventory_items")
    transactions: Mapped[list[InventoryTransaction]] = relationship(back_populates="inventory_item")
    meal_plan_ingredients: Mapped[list[MealPlanIngredient]] = relationship(back_populates="inventory_item")


class InventoryTransaction(TimestampMixin, Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('add', 'adjust', 'consume', 'meal_plan_deduction')", name="reason_allowed_values"
        ),
        CheckConstraint("source_type IN ('manual', 'ai', 'import')", name="source_type_allowed_values"),
        Index("ix_inventory_transactions_user_id_inventory_item_id_created_at", "user_id", "inventory_item_id", "created_at"),
        Index("ix_inventory_transactions_operation_id", "operation_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    inventory_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False
    )
    delta_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    operation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("meal_plan_confirmations.id", ondelete="RESTRICT"), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="inventory_transactions")
    inventory_item: Mapped[InventoryItem] = relationship(back_populates="transactions")
    confirmation: Mapped[MealPlanConfirmation | None] = relationship(back_populates="inventory_transactions")
