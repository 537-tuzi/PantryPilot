"""Request and response schemas for registration and login."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CredentialsBase(BaseModel):
    """Credentials shared by registration and email-based login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class RegisterRequest(CredentialsBase):
    """Registration input. The password rules are intentionally not returned to clients."""

    username: str = Field(min_length=1, max_length=100)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Username must not be blank")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(character.islower() for character in value):
            raise ValueError("Password must contain a lowercase letter")
        if not any(character.isupper() for character in value):
            raise ValueError("Password must contain an uppercase letter")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must contain a digit")
        return value


class LoginRequest(CredentialsBase):
    """Email and password login input."""


class UserResponse(BaseModel):
    """Safe user representation; it deliberately has no password_hash field."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    is_active: bool


class TokenResponse(BaseModel):
    """Bearer token returned after registration or successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
