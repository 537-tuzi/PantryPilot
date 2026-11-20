"""ORM 模型。

归属：B 组（后端/数据）。新增模型必须与 Alembic 迁移在同一个 PR 内提交。

数据表清单见 文档/05 §2：
users / user_preferences / ingredient_catalog / inventory_items /
inventory_transactions / recipes / recipe_ingredients / meal_plans /
meal_plan_items / meal_plan_ingredients / shopping_items / meal_plan_confirmations
"""

from app.db.base import Base
from app.models.ingredient import IngredientCatalog
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.meal_plan import MealPlan, MealPlanIngredient, MealPlanItem
from app.models.meal_plan_confirmation import MealPlanConfirmation
from app.models.preference import UserPreference
from app.models.recipe import Recipe, RecipeIngredient
from app.models.shopping import ShoppingItem
from app.models.user import User

__all__ = [
    "Base",
    "IngredientCatalog",
    "InventoryItem",
    "InventoryTransaction",
    "MealPlan",
    "MealPlanConfirmation",
    "MealPlanIngredient",
    "MealPlanItem",
    "Recipe",
    "RecipeIngredient",
    "ShoppingItem",
    "User",
    "UserPreference",
]
