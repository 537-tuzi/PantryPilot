"""Endpoints for the authenticated user's profile and preferences."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.preference import PreferencePayload, PreferenceResponse
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("", response_model=UserResponse)
def get_current_user(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/preferences", response_model=PreferenceResponse)
def get_preferences(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PreferenceResponse:
    return PreferenceService().get(db, current_user.id)


@router.put("/preferences", response_model=PreferenceResponse)
def put_preferences(
    payload: PreferencePayload,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PreferenceResponse:
    return PreferenceService().put(db, current_user.id, payload)
