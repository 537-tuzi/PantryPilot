"""User preference use cases. All reads and writes use the authenticated user id."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.models.preference import UserPreference
from app.repositories.preference_repository import PreferenceRepository
from app.schemas.preference import PreferencePayload, PreferenceResponse


class PreferenceService:
    def __init__(self, preferences: PreferenceRepository | None = None) -> None:
        self._preferences = preferences or PreferenceRepository()

    def get(self, db: Session, user_id: UUID) -> PreferenceResponse:
        preference = self._preferences.get_for_user(db, user_id)
        if preference is None:
            raise ResourceNotFoundError("User preferences have not been set")
        return PreferenceResponse.model_validate(preference)

    def put(self, db: Session, user_id: UUID, payload: PreferencePayload) -> PreferenceResponse:
        preference = self._preferences.get_for_user(db, user_id)
        if preference is None:
            preference = UserPreference(user_id=user_id, **payload.model_dump())
            self._preferences.add(db, preference)
        else:
            for field_name, value in payload.model_dump().items():
                setattr(preference, field_name, value)
        db.commit()
        db.refresh(preference)
        return PreferenceResponse.model_validate(preference)
