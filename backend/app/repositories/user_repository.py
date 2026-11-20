"""Persistence queries for users. Authentication lookups are intentionally narrow."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def add(self, db: Session, user: User) -> None:
        db.add(user)
