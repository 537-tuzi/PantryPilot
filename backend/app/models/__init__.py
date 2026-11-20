"""SQLAlchemy ORM models registered for Alembic metadata discovery."""

from app.models.ingredient import IngredientCatalog
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.meal_plan import MealPlan, MealPlanIngredient, MealPlanItem
from app.models.meal_plan_confirmation import MealPlanConfirmation
from app.models.preference import UserPreference
from app.models.recipe import Recipe, RecipeIngredient
from app.models.shopping import ShoppingItem
from app.models.user import User

__all__ = [
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
