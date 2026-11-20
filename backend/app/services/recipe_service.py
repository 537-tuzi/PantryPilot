"""Recipe reads with public/private access rules."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.meal_plan import RecipeResponse


class RecipeService:
    def __init__(self, recipes: RecipeRepository | None = None) -> None:
        self._recipes = recipes or RecipeRepository()

    def get_visible(self, db: Session, user_id: UUID, recipe_id: UUID) -> RecipeResponse:
        """Public recipes are readable by everyone; private ones only by their owner."""
        recipe = self._recipes.get_visible(db, user_id, recipe_id)
        if recipe is None:
            raise ResourceNotFoundError("Recipe was not found")
        return RecipeResponse.model_validate(recipe)
