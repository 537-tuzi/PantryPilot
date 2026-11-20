from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory import InventoryItem
    from app.models.meal_plan_confirmation import MealPlanConfirmation
    from app.models.recipe import Recipe
    from app.models.shopping import ShoppingItem
    from app.models.user import User


class MealPlan(TimestampMixin, Base):
    __tablename__ = "meal_plans"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'confirmed')", name="status_allowed_values"),
        Index("ix_meal_plans_user_id_plan_date_status", "user_id", "plan_date", "status"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    request_constraints: Mapped[Any] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    ai_provider: Mapped[str] = mapped_column(Text, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="meal_plans")
    items: Mapped[list[MealPlanItem]] = relationship(back_populates="meal_plan")
    confirmations: Mapped[list[MealPlanConfirmation]] = relationship(back_populates="meal_plan")
    shopping_items: Mapped[list[ShoppingItem]] = relationship(back_populates="source_meal_plan")


class MealPlanItem(TimestampMixin, Base):
    __tablename__ = "meal_plan_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    meal_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("meal_plans.id", ondelete="RESTRICT"), nullable=False
    )
    recipe_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    recipe_snapshot: Mapped[Any] = mapped_column(JSONB, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    meal_plan: Mapped[MealPlan] = relationship(back_populates="items")
    recipe: Mapped[Recipe | None] = relationship(back_populates="meal_plan_items")
    ingredients: Mapped[list[MealPlanIngredient]] = relationship(back_populates="meal_plan_item")


class MealPlanIngredient(TimestampMixin, Base):
    __tablename__ = "meal_plan_ingredients"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    meal_plan_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("meal_plan_items.id", ondelete="RESTRICT"), nullable=False
    )
    inventory_item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    actual_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    is_missing: Mapped[bool] = mapped_column(Boolean, nullable=False)

    meal_plan_item: Mapped[MealPlanItem] = relationship(back_populates="ingredients")
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates="meal_plan_ingredients")
