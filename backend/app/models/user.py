from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory import InventoryItem, InventoryTransaction
    from app.models.meal_plan import MealPlan
    from app.models.meal_plan_confirmation import MealPlanConfirmation
    from app.models.preference import UserPreference
    from app.models.recipe import Recipe
    from app.models.shopping import ShoppingItem


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    preference: Mapped[UserPreference | None] = relationship(back_populates="user", uselist=False)
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates="user")
    inventory_transactions: Mapped[list[InventoryTransaction]] = relationship(back_populates="user")
    recipes: Mapped[list[Recipe]] = relationship(back_populates="user")
    meal_plans: Mapped[list[MealPlan]] = relationship(back_populates="user")
    shopping_items: Mapped[list[ShoppingItem]] = relationship(back_populates="user")
    meal_plan_confirmations: Mapped[list[MealPlanConfirmation]] = relationship(
        back_populates="user"
    )
