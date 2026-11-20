"""Schemas for inventory items and their status."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

InventoryStatus = Literal["normal", "expiring", "expired"]
InventoryReason = Literal["add", "adjust", "consume"]


class InventoryCreatePayload(BaseModel):
    """Create payload; quantity must be positive so a new item is never born empty."""

    display_name: str = Field(min_length=1, max_length=200)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = Field(min_length=1, max_length=32)
    ingredient_id: UUID | None = None
    purchase_date: date | None = None
    expiry_date: date | None = None
    storage_location: str | None = Field(default=None, max_length=100)

    @field_validator("display_name", "unit")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized

    @field_validator("storage_location")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class InventoryUpdatePayload(BaseModel):
    """Partial update; only fields present in the request are applied."""

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    quantity: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    purchase_date: date | None = None
    expiry_date: date | None = None
    storage_location: str | None = Field(default=None, max_length=100)
    reason: InventoryReason | None = None
    expected_version: int = Field(ge=1)

    @field_validator("display_name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized


class InventoryResponse(BaseModel):
    """Inventory item with a computed status; quantity is serialized as a string."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID | None
    display_name: str
    quantity: Decimal
    unit: str
    purchase_date: date | None
    expiry_date: date | None
    storage_location: str | None
    status: InventoryStatus
    version: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("quantity")
    def serialize_quantity(self, value: Decimal) -> str:
        return format(value, "f")


class InventoryListResponse(BaseModel):
    """Paginated inventory list."""

    items: list[InventoryResponse]
    page: int
    page_size: int
    total: int
