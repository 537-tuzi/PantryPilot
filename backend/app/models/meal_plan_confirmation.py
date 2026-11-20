from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory import InventoryTransaction
    from app.models.meal_plan import MealPlan
    from app.models.user import User


class MealPlanConfirmation(TimestampMixin, Base):
    __tablename__ = "meal_plan_confirmations"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="user_idempotency_key"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    meal_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("meal_plans.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    request_hash: Mapped[str] = mapped_column(Text, nullable=False)
    result_snapshot: Mapped[Any] = mapped_column(JSONB, nullable=False)
    user: Mapped[User] = relationship(back_populates="meal_plan_confirmations")
    meal_plan: Mapped[MealPlan] = relationship(back_populates="confirmations")
    inventory_transactions: Mapped[list[InventoryTransaction]] = relationship(back_populates="confirmation")
