from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.ingredient import IngredientCatalog
    from app.models.meal_plan import MealPlanItem
    from app.models.user import User


class Recipe(TimestampMixin, Base):
    __tablename__ = "recipes"
    __table_args__ = (CheckConstraint("source_type IN ('manual', 'ai', 'import')", name="source_type_allowed_values"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    servings: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    steps: Mapped[Any] = mapped_column(JSONB, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped[User | None] = relationship(back_populates="recipes")
    ingredients: Mapped[list[RecipeIngredient]] = relationship(back_populates="recipe")
    meal_plan_items: Mapped[list[MealPlanItem]] = relationship(back_populates="recipe")


class RecipeIngredient(TimestampMixin, Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False)
    ingredient_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ingredient_catalog.id", ondelete="SET NULL"), nullable=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[IngredientCatalog | None] = relationship(back_populates="recipe_ingredients")
