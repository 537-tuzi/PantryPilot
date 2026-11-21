"""模型输出契约。

与 文档/06 §4 一一对应，是 AI 层与业务层之间的唯一接口。
字段不确定时必须留空或写入 uncertainties，不得猜测。
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class StorageLocation(StrEnum):
    """存储位置。取值与 文档/03 §5 字段校验一致。"""

    COLD = "冷藏"
    FROZEN = "冷冻"
    AMBIENT = "常温"
    CUSTOM = "自定义"


class IngredientDraft(BaseModel):
    """自然语言录入草稿。"""

    name: str = Field(min_length=1, max_length=80)
    quantity: Decimal | None = None
    unit: str | None = None
    category: str | None = None
    purchase_date: date | None = None
    expiry_date: date | None = None
    storage_location: StorageLocation | None = None
    uncertainties: list[str] = Field(default_factory=list)


class RecipeIngredient(BaseModel):
    """菜谱用料。"""

    name: str
    quantity: Decimal | None = None
    unit: str | None = None
    optional: bool = False


class RecipeCandidate(BaseModel):
    """候选菜谱。"""

    name: str
    servings: int = Field(ge=1, le=12)
    estimated_minutes: int = Field(ge=1)
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)


class MissingIngredient(BaseModel):
    """库存中不存在、需要采购的用料。"""

    name: str
    quantity: Decimal | None = None
    unit: str | None = None


class MealPlan(BaseModel):
    """膳食计划候选结果。"""

    title: str
    recipes: list[RecipeCandidate] = Field(default_factory=list)
    missing_items: list[MissingIngredient] = Field(default_factory=list)
    constraint_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
