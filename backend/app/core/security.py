"""Password hashing and JWT helpers used by the authentication boundary."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.errors import UnauthenticatedError

password_hasher = PasswordHasher(type=Type.ID)


def hash_password(password: str) -> str:
    """Hash a password with Argon2id. Never log the input or result."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password without exposing verification errors to callers."""
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Report whether an existing Argon2id hash needs current parameters."""
    try:
        return password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


def create_access_token(user_id: UUID, *, expires_delta: timedelta | None = None) -> str:
    """Create a signed, expiring access token for one user."""
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID:
    """Return the authenticated user id or raise the uniform 401 application error."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return UUID(str(payload["sub"]))
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise UnauthenticatedError("Invalid or expired access token") from exc
