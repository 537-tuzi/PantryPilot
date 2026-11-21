"""User-scoped persistence queries for dietary preferences."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preference import UserPreference


class PreferenceRepository:
    def get_for_user(self, db: Session, user_id: UUID) -> UserPreference | None:
        return db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))

    def add(self, db: Session, preference: UserPreference) -> None:
        db.add(preference)
