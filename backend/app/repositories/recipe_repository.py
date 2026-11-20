"""Recipe lookups. Access rules are enforced by the service layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recipe import Recipe


class RecipeRepository:
    def get(self, db: Session, recipe_id: UUID) -> Recipe | None:
        return db.scalar(select(Recipe).where(Recipe.id == recipe_id))

    def get_visible(self, db: Session, user_id: UUID, recipe_id: UUID) -> Recipe | None:
        """Public recipes (user_id IS NULL) plus the caller's own recipes."""
        statement = select(Recipe).where(
            Recipe.id == recipe_id,
            (Recipe.user_id.is_(None)) | (Recipe.user_id == user_id),
        )
        return db.scalar(statement)
