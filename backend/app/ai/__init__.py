"""AI 层：上下文、Prompt、Provider 适配、输出解析与业务校验。

归属：C 组（AI/质量工程）。

硬约束（文档/06）：
- 本层不得直接提交库存事务；
- 模型输出必须经过 Output Parser（Schema）与 Business Validator 两道校验；
- 用户输入一律视为不可信数据。
"""

from app.ai.contracts import (
    IngredientDraft,
    MealPlan,
    MissingIngredient,
    RecipeCandidate,
)

__all__ = [
    "IngredientDraft",
    "MealPlan",
    "MissingIngredient",
    "RecipeCandidate",
]
