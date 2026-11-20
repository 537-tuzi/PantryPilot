from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory import InventoryItem
    from app.models.recipe import RecipeIngredient
    from app.models.shopping import ShoppingItem


class IngredientCatalog(TimestampMixin, Base):
    __tablename__ = "ingredient_catalog"
    __table_args__ = (
        Index(
            "uq_ingredient_catalog_canonical_name_normalized",
            func.lower(func.btrim(text("canonical_name"))),
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    default_unit: Mapped[str] = mapped_column(Text, nullable=False)

    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates="ingredient")
    recipe_ingredients: Mapped[list[RecipeIngredient]] = relationship(back_populates="ingredient")
    shopping_items: Mapped[list[ShoppingItem]] = relationship(back_populates="ingredient")
