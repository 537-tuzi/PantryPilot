"""Inventory API integration tests against PostgreSQL.

All cases run inside the isolated pantrypilot_test database. Writes performed through the
API are rolled back by the db_session savepoint fixture.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.ingredient import IngredientCatalog
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.user import User
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.inventory import InventoryCreatePayload, InventoryUpdatePayload
from app.services.inventory_service import InventoryService, current_date, inventory_status

INVENTORY_URL = "/api/v1/inventory"


def register(
    client: TestClient,
    *,
    username: str = "inventory_user",
    email: str = "inventory.user@example.com",
) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "StrongPassword1"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ingredient(db_session: Session) -> IngredientCatalog:
    catalog_item = IngredientCatalog(
        canonical_name=f"tomato-{uuid4().hex[:8]}",
        category="vegetable",
        default_unit="kg",
    )
    db_session.add(catalog_item)
    db_session.commit()
    return catalog_item


def create_item(
    client: TestClient,
    token: str,
    *,
    ingredient_id: str | None = None,
    quantity: str = "2.500",
    expiry_date: str | None = None,
    display_name: str = "Tomato",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "display_name": display_name,
        "quantity": quantity,
        "unit": "kg",
    }
    if ingredient_id is not None:
        payload["ingredient_id"] = ingredient_id
    if expiry_date is not None:
        payload["expiry_date"] = expiry_date
    response = client.post(INVENTORY_URL, headers=auth_headers(token), json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def patch_item(client: TestClient, token: str, item_id: str, body: dict[str, object]):
    return client.patch(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(token), json=body)


def transactions_of(db_session: Session, item_id: str | UUID) -> list[InventoryTransaction]:
    return list(
        db_session.scalars(
            select(InventoryTransaction)
            .where(InventoryTransaction.inventory_item_id == item_id)
            .order_by(InventoryTransaction.created_at.asc())
        )
    )


def test_create_records_initial_transaction_and_returns_string_quantity(
    client: TestClient, db_session: Session, ingredient: IngredientCatalog
) -> None:
    token = register(client)
    expiry = str(current_date() + timedelta(days=10))

    body = create_item(
        client,
        token,
        ingredient_id=str(ingredient.id),
        quantity="2.500",
        expiry_date=expiry,
    )

    assert body["quantity"] == "2.500"
    assert body["status"] == "normal"
    assert body["version"] == 1
    assert body["archived_at"] is None
    assert body["ingredient_id"] == str(ingredient.id)

    transactions = transactions_of(db_session, str(body["id"]))
    assert len(transactions) == 1
    assert transactions[0].reason == "add"
    assert transactions[0].source_type == "manual"
    assert transactions[0].delta_quantity == Decimal("2.500")
    assert transactions[0].operation_id is None
    assert transactions[0].source_id is None


@pytest.mark.parametrize("quantity", ["0", "0.000", "-1"])
def test_create_rejects_non_positive_quantity(client: TestClient, quantity: str) -> None:
    token = register(client)

    response = client.post(
        INVENTORY_URL,
        headers=auth_headers(token),
        json={"display_name": "Tomato", "quantity": quantity, "unit": "kg"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_rejects_unknown_ingredient(client: TestClient) -> None:
    token = register(client)

    response = client.post(
        INVENTORY_URL,
        headers=auth_headers(token),
        json={
            "display_name": "Tomato",
            "quantity": "1",
            "unit": "kg",
            "ingredient_id": str(uuid4()),
        },
    )

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_list_pagination_and_filters(client: TestClient, ingredient: IngredientCatalog) -> None:
    token = register(client)
    today = current_date()
    create_item(
        client,
        token,
        ingredient_id=str(ingredient.id),
        display_name="Tomato",
        expiry_date=str(today + timedelta(days=1)),
    )
    create_item(client, token, display_name="Potato", expiry_date=str(today - timedelta(days=1)))
    create_item(client, token, display_name="Taro", expiry_date=str(today + timedelta(days=30)))

    expiring = client.get(f"{INVENTORY_URL}?status=expiring", headers=auth_headers(token))
    expired = client.get(f"{INVENTORY_URL}?status=expired", headers=auth_headers(token))
    normal = client.get(f"{INVENTORY_URL}?status=normal", headers=auth_headers(token))
    by_name = client.get(f"{INVENTORY_URL}?name=Taro", headers=auth_headers(token))
    by_category = client.get(f"{INVENTORY_URL}?category=vegetable", headers=auth_headers(token))
    paged = client.get(f"{INVENTORY_URL}?page=1&page_size=2", headers=auth_headers(token))

    assert [item["display_name"] for item in expiring.json()["items"]] == ["Tomato"]
    assert [item["display_name"] for item in expired.json()["items"]] == ["Potato"]
    assert [item["display_name"] for item in normal.json()["items"]] == ["Taro"]
    assert [item["display_name"] for item in by_name.json()["items"]] == ["Taro"]
    assert [item["display_name"] for item in by_category.json()["items"]] == ["Tomato"]
    assert paged.json()["total"] == 3
    assert len(paged.json()["items"]) == 2
    assert paged.json()["page"] == 1
    assert paged.json()["page_size"] == 2


def test_list_rejects_page_size_above_limit(client: TestClient) -> None:
    token = register(client)

    response = client.get(f"{INVENTORY_URL}?page_size=101", headers=auth_headers(token))

    assert response.status_code == 400


def test_inventory_is_isolated_between_users(client: TestClient) -> None:
    first_token = register(client, username="owner_user", email="owner@example.com")
    second_token = register(client, username="intruder_user", email="intruder@example.com")
    body = create_item(client, first_token)
    item_id = str(body["id"])

    detail = client.get(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(second_token))
    listing = client.get(INVENTORY_URL, headers=auth_headers(second_token))
    patch = patch_item(
        client, second_token, item_id, {"expected_version": 1, "display_name": "Stolen"}
    )
    remove = client.delete(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(second_token))

    assert detail.status_code == 404
    assert listing.json()["total"] == 0
    assert patch.status_code == 404
    assert remove.status_code == 404


def test_patch_with_correct_version_increments_version(client: TestClient) -> None:
    token = register(client)
    body = create_item(client, token)
    item_id = str(body["id"])

    first = patch_item(
        client,
        token,
        item_id,
        {"expected_version": 1, "storage_location": "fridge", "reason": "adjust"},
    )
    second = patch_item(
        client,
        token,
        item_id,
        {"expected_version": 2, "storage_location": "freezer", "reason": "adjust"},
    )

    assert first.status_code == 200
    assert first.json()["version"] == 2
    assert second.status_code == 200
    assert second.json()["version"] == 3


def test_patch_requires_expected_version(client: TestClient) -> None:
    token = register(client)
    body = create_item(client, token)
    item_id = str(body["id"])

    response = patch_item(client, token, item_id, {"display_name": "Renamed"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_patch_rejects_stale_expected_version(client: TestClient) -> None:
    token = register(client)
    body = create_item(client, token)
    item_id = str(body["id"])

    first = patch_item(
        client,
        token,
        item_id,
        {"expected_version": 1, "storage_location": "fridge", "reason": "adjust"},
    )
    stale = patch_item(
        client,
        token,
        item_id,
        {"expected_version": 1, "storage_location": "freezer", "reason": "adjust"},
    )

    assert first.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] == "STATE_CONFLICT"


def test_patch_quantity_writes_transaction(client: TestClient, db_session: Session) -> None:
    token = register(client)
    body = create_item(client, token, quantity="2.000")
    item_id = str(body["id"])

    response = patch_item(
        client, token, item_id, {"expected_version": 1, "quantity": "5.500", "reason": "add"}
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == "5.500"
    transactions = transactions_of(db_session, item_id)
    assert [item.reason for item in transactions] == ["add", "add"]
    assert transactions[-1].delta_quantity == Decimal("3.500")


def test_patch_quantity_can_reach_zero_as_depleted(client: TestClient) -> None:
    token = register(client)
    body = create_item(client, token, quantity="2.000")
    item_id = str(body["id"])

    response = patch_item(
        client, token, item_id, {"expected_version": 1, "quantity": "0", "reason": "consume"}
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == "0.000"
    assert response.json()["archived_at"] is None
    assert response.json()["version"] == 2


def test_patch_rejects_quantity_without_reason(client: TestClient) -> None:
    token = register(client)
    body = create_item(client, token)
    item_id = str(body["id"])

    response = patch_item(client, token, item_id, {"expected_version": 1, "quantity": "1.000"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    ("quantity", "reason"),
    [("5.000", "consume"), ("1.000", "add")],
)
def test_patch_rejects_wrong_reason_direction(
    client: TestClient, quantity: str, reason: str
) -> None:
    token = register(client)
    body = create_item(client, token, quantity="2.000")
    item_id = str(body["id"])

    response = patch_item(
        client, token, item_id, {"expected_version": 1, "quantity": quantity, "reason": reason}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_patch_metadata_requires_reason_and_writes_zero_delta(
    client: TestClient, db_session: Session
) -> None:
    token = register(client)
    body = create_item(client, token, quantity="2.000")
    item_id = str(body["id"])

    missing_reason = patch_item(
        client, token, item_id, {"expected_version": 1, "storage_location": "fridge"}
    )
    accepted = patch_item(
        client,
        token,
        item_id,
        {"expected_version": 1, "storage_location": "fridge", "reason": "adjust"},
    )

    assert missing_reason.status_code == 400
    assert accepted.status_code == 200
    assert accepted.json()["storage_location"] == "fridge"
    assert accepted.json()["quantity"] == "2.000"

    transactions = transactions_of(db_session, item_id)
    assert len(transactions) == 2
    assert transactions[-1].delta_quantity == Decimal("0.000")
    assert transactions[-1].reason == "adjust"
    assert transactions[-1].source_type == "manual"

    summary = sum(item.delta_quantity for item in transactions)
    assert summary == Decimal("2.000")


def test_decimal_precision_is_preserved(client: TestClient) -> None:
    token = register(client)
    body = create_item(client, token, quantity="1.005")

    updated = patch_item(
        client,
        token,
        str(body["id"]),
        {"expected_version": 1, "quantity": "1.006", "reason": "adjust"},
    )

    assert body["quantity"] == "1.005"
    assert updated.json()["quantity"] == "1.006"


def test_delete_archives_without_removing_transactions(
    client: TestClient, db_session: Session
) -> None:
    token = register(client)
    body = create_item(client, token)
    item_id = str(body["id"])

    archived = client.delete(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(token))
    hidden = client.get(INVENTORY_URL, headers=auth_headers(token))
    visible = client.get(f"{INVENTORY_URL}?include_archived=true", headers=auth_headers(token))
    detail = client.get(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(token))

    stored = db_session.get(InventoryItem, item_id)

    assert archived.status_code == 204
    assert hidden.json()["total"] == 0
    assert len(visible.json()["items"]) == 1
    assert detail.status_code == 404
    assert stored is not None and stored.archived_at is not None
    assert stored.version == 2
    assert len(transactions_of(db_session, item_id)) == 1


def test_repeated_archive_is_idempotent_and_keeps_timestamp(
    client: TestClient, db_session: Session
) -> None:
    token = register(client)
    body = create_item(client, token)
    item_id = str(body["id"])

    first = client.delete(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(token))
    first_archived_at = db_session.get(InventoryItem, item_id).archived_at

    second = client.delete(f"{INVENTORY_URL}/{item_id}", headers=auth_headers(token))
    db_session.expire_all()
    second_archived_at = db_session.get(InventoryItem, item_id).archived_at

    assert first.status_code == 204
    assert second.status_code == 204
    assert first_archived_at == second_archived_at


def test_expiring_returns_expired_and_expiring_items_in_order(client: TestClient) -> None:
    token = register(client)
    today = current_date()
    create_item(client, token, display_name="Expired", expiry_date=str(today - timedelta(days=2)))
    create_item(client, token, display_name="Soon", expiry_date=str(today + timedelta(days=1)))
    create_item(client, token, display_name="Today", expiry_date=str(today))
    create_item(client, token, display_name="Later", expiry_date=str(today + timedelta(days=30)))
    gone = create_item(
        client, token, display_name="Gone", expiry_date=str(today + timedelta(days=1))
    )
    patch_item(
        client,
        token,
        str(gone["id"]),
        {"expected_version": 1, "quantity": "0", "reason": "consume"},
    )
    archived = create_item(
        client, token, display_name="Archived", expiry_date=str(today + timedelta(days=1))
    )
    client.delete(f"{INVENTORY_URL}/{archived['id']}", headers=auth_headers(token))

    response = client.get(f"{INVENTORY_URL}/expiring", headers=auth_headers(token))

    assert response.status_code == 200
    names = [item["display_name"] for item in response.json()]
    assert names == ["Expired", "Today", "Soon"]
    statuses = {item["display_name"]: item["status"] for item in response.json()}
    assert statuses == {"Expired": "expired", "Today": "expiring", "Soon": "expiring"}


def test_status_boundaries_use_app_timezone() -> None:
    today = current_date()

    assert inventory_status(today - timedelta(days=1), today) == "expired"
    assert inventory_status(today, today) == "expiring"
    assert inventory_status(today + timedelta(days=3), today) == "expiring"
    assert inventory_status(today + timedelta(days=4), today) == "normal"
    assert inventory_status(None, today) == "normal"
    assert current_date() == datetime.now(ZoneInfo(settings.app_timezone)).date()
    assert settings.app_timezone == "Asia/Shanghai"


def test_service_rejects_second_update_with_consumed_version(db_session: Session) -> None:
    """Simulates two requests that both observed version 1."""
    user = User(
        username=f"optimistic_{uuid4().hex[:8]}",
        email=f"optimistic_{uuid4().hex[:8]}@example.com",
        password_hash="$argon2id$test",
    )
    db_session.add(user)
    db_session.commit()

    service = InventoryService()
    created = service.create(
        db_session,
        user.id,
        InventoryCreatePayload(display_name="Optimistic", quantity=Decimal("2.000"), unit="kg"),
    )

    service.update(
        db_session,
        user.id,
        created.id,
        InventoryUpdatePayload(expected_version=1, quantity=Decimal("1.000"), reason="consume"),
    )
    with pytest.raises(Exception) as conflict:
        service.update(
            db_session,
            user.id,
            created.id,
            InventoryUpdatePayload(expected_version=1, quantity=Decimal("0.500"), reason="consume"),
        )
    assert getattr(conflict.value, "code", None) == "STATE_CONFLICT"


def test_update_rolls_back_when_transaction_write_fails() -> None:
    """If writing the ledger fails, the quantity update must not persist.

    Everything runs inside an outer transaction that is rolled back at the end, so no
    DELETE privilege on inventory_transactions is required for cleanup.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    engine = create_engine(url, pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=connection,
                join_transaction_mode="create_savepoint",
            )
            session = session_factory()
            try:
                user = User(
                    username=f"rollback_{uuid4().hex[:8]}",
                    email=f"rollback_{uuid4().hex[:8]}@example.com",
                    password_hash="$argon2id$test",
                )
                session.add(user)
                session.commit()
                user_id = user.id

                service = InventoryService()
                created = service.create(
                    session,
                    user_id,
                    InventoryCreatePayload(
                        display_name="Rollback", quantity=Decimal("5.000"), unit="kg"
                    ),
                )
                item_id = created.id

                repository = InventoryRepository()

                def explode(*_args: object, **_kwargs: object) -> None:
                    raise RuntimeError("ledger write failed")

                repository.add_transaction = explode  # type: ignore[method-assign]
                failing_service = InventoryService(repository)

                with pytest.raises(RuntimeError, match="ledger write failed"):
                    failing_service.update(
                        session,
                        user_id,
                        item_id,
                        InventoryUpdatePayload(
                            expected_version=1, quantity=Decimal("1.000"), reason="consume"
                        ),
                    )
                session.rollback()

                with session_factory() as fresh:
                    stored = fresh.get(InventoryItem, item_id)
                    assert stored is not None
                    assert stored.quantity == Decimal("5.000")
                    assert stored.version == 1
                    ledger = list(
                        fresh.scalars(
                            select(InventoryTransaction).where(
                                InventoryTransaction.inventory_item_id == item_id
                            )
                        )
                    )
                    assert len(ledger) == 1
            finally:
                session.close()
                outer.rollback()
    finally:
        engine.dispose()


def test_optimistic_lock_blocks_concurrent_database_updates() -> None:
    """Two real connections update the same row; only the first version wins."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    maintenance_url = os.environ.get("TEST_MAINTENANCE_DATABASE_URL")
    if not maintenance_url:
        pytest.skip("TEST_MAINTENANCE_DATABASE_URL is required for committed concurrency cleanup")

    engine = create_engine(url, pool_pre_ping=True, future=True)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    first = session_factory()
    second = session_factory()
    user_id: UUID | None = None
    item_id: UUID | None = None
    try:
        user = User(
            username=f"conc_{uuid4().hex[:8]}",
            email=f"conc_{uuid4().hex[:8]}@example.com",
            password_hash="$argon2id$test",
        )
        first.add(user)
        first.commit()
        user_id = user.id

        item = InventoryItem(
            user_id=user_id,
            display_name="Concurrent",
            quantity=Decimal("5.000"),
            unit="kg",
            version=1,
        )
        first.add(item)
        first.commit()
        item_id = item.id

        repository = InventoryRepository()
        first_view = repository.get(first, user_id, item_id)
        second_view = repository.get(second, user_id, item_id)
        assert first_view is not None and second_view is not None
        assert first_view.version == second_view.version == 1

        assert (
            repository.update_fields(
                first,
                user_id=user_id,
                item_id=item_id,
                expected_version=1,
                values={"quantity": Decimal("4.000")},
            )
            == 1
        )
        first.commit()

        assert (
            repository.update_fields(
                second,
                user_id=user_id,
                item_id=item_id,
                expected_version=1,
                values={"quantity": Decimal("3.000")},
            )
            == 0
        )

        first.expire_all()
        remaining = repository.get(first, user_id, item_id)
        assert remaining is not None
        assert remaining.quantity == Decimal("4.000")
        assert remaining.version == 2
    finally:
        second.close()
        first.close()
        if item_id is not None and user_id is not None:
            cleanup_engine = create_engine(maintenance_url, pool_pre_ping=True, future=True)
            try:
                with Session(cleanup_engine) as cleanup:
                    # The app account cannot DELETE ledger rows; this test never writes any,
                    # so only touch the table when a row actually exists.
                    ledger_rows = cleanup.scalar(
                        select(func.count())
                        .select_from(InventoryTransaction)
                        .where(InventoryTransaction.inventory_item_id == item_id)
                    )
                    if ledger_rows:
                        cleanup.execute(
                            delete(InventoryTransaction).where(
                                InventoryTransaction.inventory_item_id == item_id
                            )
                        )
                    cleanup.execute(delete(InventoryItem).where(InventoryItem.id == item_id))
                    cleanup.execute(delete(User).where(User.id == user_id))
                    cleanup.commit()
            finally:
                cleanup_engine.dispose()
        engine.dispose()
