from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    dietary_preferences: Mapped[Any] = mapped_column(JSONB, nullable=False)
    allergens: Mapped[Any] = mapped_column(JSONB, nullable=False)
    disliked_ingredients: Mapped[Any] = mapped_column(JSONB, nullable=False)
    default_servings: Mapped[int] = mapped_column(Integer, nullable=False)
    default_budget: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    default_cooking_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped[User] = relationship(back_populates="preference")
