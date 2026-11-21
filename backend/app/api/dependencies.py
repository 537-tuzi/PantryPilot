"""FastAPI dependencies shared by authenticated API endpoints."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import UnauthenticatedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the active user exclusively from the signed Bearer token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthenticatedError("Authentication is required")
    user_id = decode_access_token(credentials.credentials)
    user = UserRepository().get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise UnauthenticatedError("Authentication is required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
