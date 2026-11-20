"""Request and response schemas for user-scoped shopping items."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

ShoppingStatus = Literal["pending", "purchased", "cancelled"]


class ShoppingItemCreatePayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = Field(min_length=1, max_length=32)
    ingredient_id: UUID | None = None

    @field_validator("display_name", "unit")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized


class ShoppingItemStatusUpdatePayload(BaseModel):
    status: ShoppingStatus


class ShoppingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    ingredient_id: UUID | None
    quantity: Decimal
    unit: str
    status: ShoppingStatus
    source_meal_plan_id: UUID | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("quantity")
    def serialize_quantity(self, value: Decimal) -> str:
        return format(value, "f")


class ShoppingItemListResponse(BaseModel):
    items: list[ShoppingItemResponse]
    page: int
    page_size: int
    total: int


class ShoppingImportFromMealPlanPayload(BaseModel):
    meal_plan_id: UUID


class ShoppingImportFromMealPlanResponse(BaseModel):
    meal_plan_id: UUID
    created_count: int
    skipped_count: int
