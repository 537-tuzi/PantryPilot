"""Shopping API tests against the isolated PostgreSQL test database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.ingredient import IngredientCatalog
from app.models.inventory import InventoryItem
from app.models.meal_plan import MealPlan, MealPlanIngredient, MealPlanItem
from app.models.recipe import Recipe
from app.models.shopping import ShoppingItem
from app.models.user import User
from app.repositories.shopping_repository import ShoppingRepository
from app.services.shopping_service import ShoppingService


def make_user(db: Session, suffix: str | None = None) -> User:
    tag = suffix or uuid4().hex[:10]
    user = User(
        username=f"shopping_{tag}",
        email=f"shopping_{tag}@example.test",
        password_hash="not-a-real-hash",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def make_catalog_ingredient(db: Session, name: str = "Tomato") -> IngredientCatalog:
    ingredient = IngredientCatalog(
        canonical_name=f"{name.lower()}_{uuid4().hex[:8]}", category="vegetable", default_unit="g"
    )
    db.add(ingredient)
    db.flush()
    return ingredient


def make_confirmed_plan(db: Session, user: User, title: str = "Shopping source") -> MealPlan:
    recipe = Recipe(
        user_id=user.id,
        name=f"Recipe {uuid4().hex[:8]}",
        description="",
        servings=1,
        estimated_minutes=10,
        steps=[],
        source_type="manual",
    )
    db.add(recipe)
    db.flush()
    plan = MealPlan(
        user_id=user.id,
        plan_date=date(2026, 11, 21),
        title=title,
        request_constraints={},
        status="confirmed",
        ai_provider="manual",
    )
    db.add(plan)
    db.flush()
    plan_item = MealPlanItem(
        meal_plan_id=plan.id, recipe_id=recipe.id, recipe_snapshot={}, sort_order=0
    )
    db.add(plan_item)
    db.flush()
    return plan


def add_plan_ingredient(
    db: Session,
    plan: MealPlan,
    *,
    display_name: str,
    required: str,
    actual: str | None,
    unit: str = "g",
    missing: bool = True,
    inventory: InventoryItem | None = None,
) -> MealPlanIngredient:
    plan_item = db.scalar(select(MealPlanItem).where(MealPlanItem.meal_plan_id == plan.id))
    assert plan_item is not None
    ingredient = MealPlanIngredient(
        meal_plan_item_id=plan_item.id,
        inventory_item_id=inventory.id if inventory is not None else None,
        display_name=display_name,
        required_quantity=Decimal(required),
        actual_quantity=Decimal(actual) if actual is not None else None,
        unit=unit,
        is_missing=missing,
    )
    db.add(ingredient)
    db.flush()
    return ingredient


def make_inventory(
    db: Session, user: User, ingredient: IngredientCatalog, name: str = "Tomato"
) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
        ingredient_id=ingredient.id,
        display_name=name,
        quantity=Decimal("10.000"),
        unit="g",
        version=1,
    )
    db.add(item)
    db.flush()
    return item


def test_create_validates_and_persists_decimal(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    ingredient = make_catalog_ingredient(db_session)

    response = client.post(
        "/api/v1/shopping-items",
        json={
            "display_name": "  Tomato  ",
            "quantity": "2.125",
            "unit": " g ",
            "ingredient_id": str(ingredient.id),
        },
        headers=headers(user),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["display_name"] == "Tomato"
    assert body["quantity"] == "2.125"
    assert body["unit"] == "g"
    assert body["status"] == "pending"
    stored = db_session.get(ShoppingItem, body["id"])
    assert stored is not None and stored.user_id == user.id
    assert stored.quantity == Decimal("2.125")


@pytest.mark.parametrize(
    ("payload", "status_code"),
    [
        ({"display_name": "   ", "quantity": "1", "unit": "g"}, 400),
        ({"display_name": "Tomato", "quantity": "0", "unit": "g"}, 400),
        ({"display_name": "Tomato", "quantity": "-1", "unit": "g"}, 400),
        ({"display_name": "Tomato", "quantity": "1.0001", "unit": "g"}, 400),
    ],
)
def test_create_rejects_invalid_payloads(
    db_session: Session, client: TestClient, payload: dict[str, str], status_code: int
) -> None:
    user = make_user(db_session)
    response = client.post("/api/v1/shopping-items", json=payload, headers=headers(user))
    assert response.status_code == status_code
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_rejects_unknown_ingredient(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    response = client.post(
        "/api/v1/shopping-items",
        json={
            "display_name": "Tomato",
            "quantity": "1.000",
            "unit": "g",
            "ingredient_id": str(uuid4()),
        },
        headers=headers(user),
    )
    assert response.status_code == 404


def test_database_rejects_nonpositive_shopping_quantity(db_session: Session) -> None:
    user = make_user(db_session)
    db_session.add(
        ShoppingItem(
            user_id=user.id,
            display_name="Invalid",
            quantity=Decimal("0.000"),
            unit="g",
            status="pending",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_list_filter_pagination_status_and_isolation(
    db_session: Session, client: TestClient
) -> None:
    user_a = make_user(db_session, "list_a")
    user_b = make_user(db_session, "list_b")
    db_session.add_all(
        [
            ShoppingItem(
                user_id=user_a.id,
                display_name="A pending",
                quantity=Decimal("1"),
                unit="g",
                status="pending",
            ),
            ShoppingItem(
                user_id=user_a.id,
                display_name="A purchased",
                quantity=Decimal("2"),
                unit="g",
                status="purchased",
            ),
            ShoppingItem(
                user_id=user_b.id,
                display_name="B pending",
                quantity=Decimal("3"),
                unit="g",
                status="pending",
            ),
        ]
    )
    db_session.flush()

    response = client.get(
        "/api/v1/shopping-items?page=1&page_size=1&status=pending", headers=headers(user_a)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["page"] == 1 and body["page_size"] == 1
    assert [item["display_name"] for item in body["items"]] == ["A pending"]

    oversized = client.get("/api/v1/shopping-items?page_size=101", headers=headers(user_a))
    assert oversized.status_code == 400


def test_status_update_delete_and_cross_user_protection(
    db_session: Session, client: TestClient
) -> None:
    user_a = make_user(db_session, "edit_a")
    user_b = make_user(db_session, "edit_b")
    item = ShoppingItem(
        user_id=user_a.id, display_name="Milk", quantity=Decimal("1"), unit="box", status="pending"
    )
    other = ShoppingItem(
        user_id=user_b.id, display_name="Other", quantity=Decimal("1"), unit="box", status="pending"
    )
    db_session.add_all([item, other])
    db_session.flush()

    update = client.patch(
        f"/api/v1/shopping-items/{item.id}", json={"status": "purchased"}, headers=headers(user_a)
    )
    assert update.status_code == 200
    assert update.json()["status"] == "purchased"
    invalid = client.patch(
        f"/api/v1/shopping-items/{item.id}", json={"status": "invalid"}, headers=headers(user_a)
    )
    assert invalid.status_code == 400
    forbidden_update = client.patch(
        f"/api/v1/shopping-items/{other.id}", json={"status": "cancelled"}, headers=headers(user_a)
    )
    assert forbidden_update.status_code == 404
    forbidden_delete = client.delete(f"/api/v1/shopping-items/{other.id}", headers=headers(user_a))
    assert forbidden_delete.status_code == 404

    deleted = client.delete(f"/api/v1/shopping-items/{item.id}", headers=headers(user_a))
    assert deleted.status_code == 204
    assert db_session.get(ShoppingItem, item.id) is None
    second_delete = client.delete(f"/api/v1/shopping-items/{item.id}", headers=headers(user_a))
    assert second_delete.status_code == 404


def test_import_confirmed_missing_ingredients_and_replay(
    db_session: Session, client: TestClient
) -> None:
    user = make_user(db_session)
    catalog = make_catalog_ingredient(db_session)
    inventory = make_inventory(db_session, user, catalog)
    plan = make_confirmed_plan(db_session, user)
    add_plan_ingredient(
        db_session,
        plan,
        display_name="Tomato",
        required="5.000",
        actual="2.000",
        inventory=inventory,
    )
    add_plan_ingredient(
        db_session,
        plan,
        display_name="Basil",
        required="3.000",
        actual=None,
        unit="g",
    )

    first = client.post(
        "/api/v1/shopping-items/import-from-meal-plan",
        json={"meal_plan_id": str(plan.id)},
        headers=headers(user),
    )
    assert first.status_code == 201, first.text
    assert first.json() == {"meal_plan_id": str(plan.id), "created_count": 2, "skipped_count": 0}
    created = list(
        db_session.scalars(
            select(ShoppingItem)
            .where(ShoppingItem.user_id == user.id)
            .order_by(ShoppingItem.display_name)
        )
    )
    actual_items = [
        (item.display_name, item.quantity, item.ingredient_id, item.status) for item in created
    ]
    assert actual_items == [
        ("Basil", Decimal("3.000"), None, "pending"),
        ("Tomato", Decimal("3.000"), catalog.id, "pending"),
    ]
    assert all(item.source_meal_plan_id == plan.id for item in created)

    replay = client.post(
        "/api/v1/shopping-items/import-from-meal-plan",
        json={"meal_plan_id": str(plan.id)},
        headers=headers(user),
    )
    assert replay.status_code == 201
    assert replay.json()["created_count"] == 0
    assert replay.json()["skipped_count"] == 2


def test_import_enforces_plan_ownership_status_and_positive_gap(
    db_session: Session, client: TestClient
) -> None:
    owner = make_user(db_session, "plan_owner")
    intruder = make_user(db_session, "plan_intruder")
    plan = make_confirmed_plan(db_session, owner)
    add_plan_ingredient(
        db_session, plan, display_name="No gap", required="2.000", actual="2.000", missing=True
    )
    add_plan_ingredient(
        db_session,
        plan,
        display_name="Not missing",
        required="4.000",
        actual=None,
        missing=False,
    )

    cross_user = client.post(
        "/api/v1/shopping-items/import-from-meal-plan",
        json={"meal_plan_id": str(plan.id)},
        headers=headers(intruder),
    )
    assert cross_user.status_code == 404
    no_gap = client.post(
        "/api/v1/shopping-items/import-from-meal-plan",
        json={"meal_plan_id": str(plan.id)},
        headers=headers(owner),
    )
    assert no_gap.status_code == 201
    assert no_gap.json()["created_count"] == 0
    assert no_gap.json()["skipped_count"] == 1
    assert (
        db_session.scalar(
            select(func.count())
            .select_from(ShoppingItem)
            .where(ShoppingItem.source_meal_plan_id == plan.id)
        )
        == 0
    )

    plan.status = "draft"
    db_session.flush()
    draft = client.post(
        "/api/v1/shopping-items/import-from-meal-plan",
        json={"meal_plan_id": str(plan.id)},
        headers=headers(owner),
    )
    assert draft.status_code == 409


def test_import_rolls_back_when_a_write_fails(db_session: Session) -> None:
    user = make_user(db_session)
    plan = make_confirmed_plan(db_session, user, "Rollback source")
    add_plan_ingredient(db_session, plan, display_name="First", required="1.000", actual=None)
    add_plan_ingredient(db_session, plan, display_name="Second", required="1.000", actual=None)
    repository = ShoppingRepository()
    original_add = repository.add
    calls = 0

    def fail_second_add(session: Session, item: ShoppingItem) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated import failure")
        original_add(session, item)

    repository.add = fail_second_add  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated import failure"):
        ShoppingService(shopping=repository).import_from_meal_plan(db_session, user.id, plan.id)

    # The outer fixture transaction is rolled back by the service; a fresh database connection
    # must therefore observe no committed rows for this import.
    assert db_session.bind is not None
    with Session(db_session.bind.engine) as verification:
        count = verification.scalar(
            select(func.count())
            .select_from(ShoppingItem)
            .where(ShoppingItem.source_meal_plan_id == plan.id)
        )
    assert count == 0
