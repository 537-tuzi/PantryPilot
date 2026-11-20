"""Dashboard summary tests against the isolated PostgreSQL test database."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.domain.expiry import current_date
from app.models.inventory import InventoryItem
from app.models.user import User


def make_user(db: Session, suffix: str) -> User:
    user = User(
        username=f"dashboard_{suffix}_{uuid4().hex[:6]}",
        email=f"dashboard_{suffix}_{uuid4().hex[:6]}@example.test",
        password_hash="not-a-real-hash",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def add_inventory(
    db: Session,
    user: User,
    *,
    expiry_date: date | None,
    quantity: str = "1.000",
    unit: str = "g",
    archived: bool = False,
) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
        display_name=f"Item {uuid4().hex[:8]}",
        quantity=Decimal(quantity),
        unit=unit,
        expiry_date=expiry_date,
        archived_at=datetime.now(UTC) if archived else None,
        version=1,
    )
    db.add(item)
    db.flush()
    return item


def test_dashboard_counts_owned_active_batches_by_expiry_boundary(
    db_session: Session, client: TestClient, monkeypatch
) -> None:
    today = date(2026, 11, 21)
    monkeypatch.setattr("app.services.dashboard_service.current_date", lambda: today)
    user_a = make_user(db_session, "a")
    user_b = make_user(db_session, "b")
    unchanged = add_inventory(db_session, user_a, expiry_date=None, quantity="9.000", unit="kg")
    add_inventory(db_session, user_a, expiry_date=today - timedelta(days=1))
    add_inventory(db_session, user_a, expiry_date=today)
    add_inventory(db_session, user_a, expiry_date=today + timedelta(days=1))
    add_inventory(db_session, user_a, expiry_date=today + timedelta(days=3))
    add_inventory(db_session, user_a, expiry_date=today + timedelta(days=4))
    add_inventory(db_session, user_a, expiry_date=today, quantity="0.000")
    add_inventory(db_session, user_a, expiry_date=today, archived=True)
    add_inventory(db_session, user_b, expiry_date=today - timedelta(days=1))

    response = client.get("/api/v1/dashboard/summary", headers=headers(user_a))

    assert response.status_code == 200, response.text
    assert response.json() == {
        "statistics_date": "2026-11-21",
        "inventory_count": 6,
        "expiring_count": 3,
        "expired_count": 1,
    }
    db_session.refresh(unchanged)
    assert unchanged.quantity == Decimal("9.000")
    assert unchanged.version == 1


def test_dashboard_is_read_only_and_uses_shanghai_date(monkeypatch) -> None:
    class ShanghaiClock:
        @staticmethod
        def now(timezone):
            return datetime(2026, 11, 20, 16, 30, tzinfo=UTC).astimezone(timezone)

    monkeypatch.setattr("app.domain.expiry.datetime", ShanghaiClock)
    assert current_date() == date(2026, 11, 21)
