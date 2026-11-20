"""Schemas for the current user's dietary preferences."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PreferencePayload(BaseModel):
    """All fields are required because the persisted model has no undocumented defaults."""

    dietary_preferences: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    disliked_ingredients: list[str] = Field(default_factory=list)
    default_servings: int = Field(ge=1, le=100)
    default_budget: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    default_cooking_minutes: int = Field(ge=1, le=1440)

    @field_validator("dietary_preferences", "allergens", "disliked_ingredients")
    @classmethod
    def normalize_string_list(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Preference values must not be blank")
        return normalized


class PreferenceResponse(PreferencePayload):
    """Persisted preference response for the authenticated user."""

    model_config = ConfigDict(from_attributes=True)
