"""Schemas for meal plan confirmation and recipe access."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

MealPlanStatus = Literal["draft", "confirmed"]


class ConfirmItemPayload(BaseModel):
    """One meal plan ingredient bound to one inventory batch."""

    meal_plan_ingredient_id: UUID
    inventory_item_id: UUID
    actual_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = Field(min_length=1, max_length=32)

    @field_validator("unit")
    @classmethod
    def strip_unit(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("unit must not be blank")
        return normalized


class MealPlanConfirmPayload(BaseModel):
    """Confirmation body; each meal plan ingredient may appear only once."""

    items: list[ConfirmItemPayload] = Field(min_length=1, max_length=200)

    @field_validator("items")
    @classmethod
    def reject_duplicate_ingredients(
        cls, items: list[ConfirmItemPayload]
    ) -> list[ConfirmItemPayload]:
        seen: set[UUID] = set()
        for item in items:
            if item.meal_plan_ingredient_id in seen:
                raise ValueError("meal_plan_ingredient_id must not repeat")
            seen.add(item.meal_plan_ingredient_id)
        return items


class DeductedItem(BaseModel):
    """Aggregated deduction for one inventory batch."""

    inventory_item_id: UUID
    delta_quantity: Decimal
    unit: str

    @field_serializer("delta_quantity")
    def serialize_delta(self, value: Decimal) -> str:
        return format(value, "f")


class MissingItem(BaseModel):
    """Meal plan ingredient that was not fully covered by the request."""

    meal_plan_ingredient_id: UUID
    display_name: str
    required_quantity: Decimal
    actual_quantity: Decimal | None
    unit: str

    @field_serializer("required_quantity", "actual_quantity")
    def serialize_quantity(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return format(value, "f")


class MealPlanConfirmResponse(BaseModel):
    """Stable business result; also stored verbatim in result_snapshot."""

    model_config = ConfigDict(from_attributes=True)

    meal_plan_id: UUID
    status: MealPlanStatus
    confirmed_at: datetime
    deducted: list[DeductedItem]
    missing: list[MissingItem]


class RecipeResponse(BaseModel):
    """Read-only recipe projection."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    name: str
    description: str
    servings: int
    estimated_minutes: int
    source_type: str


class MealPlanIngredientDetailResponse(BaseModel):
    """One persisted ingredient line in a meal-plan detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventory_item_id: UUID | None
    display_name: str
    required_quantity: Decimal
    actual_quantity: Decimal | None
    unit: str
    is_missing: bool

    @field_serializer("required_quantity", "actual_quantity")
    def serialize_quantity(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return format(value, "f")


class MealPlanItemDetailResponse(BaseModel):
    """A dish and its persisted ingredient allocations."""

    id: UUID
    recipe_id: UUID | None
    recipe_snapshot: Any
    sort_order: int
    # None means the linked recipe is no longer visible to this plan owner.
    recipe: RecipeResponse | None
    ingredients: list[MealPlanIngredientDetailResponse]


class MealPlanDetailResponse(BaseModel):
    """Read-only projection of a user's meal plan and all its dishes."""

    id: UUID
    plan_date: date
    title: str
    request_constraints: Any
    status: MealPlanStatus
    ai_provider: str
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[MealPlanItemDetailResponse]
