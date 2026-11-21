from enum import StrEnum


class MealPlanStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"


class ShoppingStatus(StrEnum):
    PENDING = "pending"
    PURCHASED = "purchased"
    CANCELLED = "cancelled"


class SourceType(StrEnum):
    MANUAL = "manual"
    AI = "ai"
    IMPORT = "import"


class InventoryTransactionReason(StrEnum):
    ADD = "add"
    ADJUST = "adjust"
    CONSUME = "consume"
    MEAL_PLAN_DEDUCTION = "meal_plan_deduction"
