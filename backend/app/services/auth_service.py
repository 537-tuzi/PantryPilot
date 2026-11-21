"""Registration and login use cases and their transaction boundaries."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, ForbiddenError, UnauthenticatedError
from app.core.security import (
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, users: UserRepository | None = None) -> None:
        self._users = users or UserRepository()

    def register(self, db: Session, payload: RegisterRequest) -> TokenResponse:
        duplicate_username = self._users.get_by_username(db, payload.username)
        duplicate_email = self._users.get_by_email(db, payload.email)
        if duplicate_username or duplicate_email:
            raise ConflictError("Username or email is already registered")

        user = User(
            username=payload.username,
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            is_active=True,
        )
        self._users.add(db, user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("Username or email is already registered") from exc
        db.refresh(user)
        return self._token_response(user)

    def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
        user = self._users.get_by_email(db, str(payload.email))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise UnauthenticatedError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("User account is disabled")
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(payload.password)
            db.commit()
            db.refresh(user)
        return self._token_response(user)

    @staticmethod
    def _token_response(user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        )
