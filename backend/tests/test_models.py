from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    IngredientCatalog,
    InventoryItem,
    InventoryTransaction,
    MealPlan,
    MealPlanConfirmation,
    Recipe,
    ShoppingItem,
    User,
)


def create_user(session: Session, suffix: str = "one") -> User:
    user = User(username=f"user_{suffix}", email=f"{suffix}@example.test", password_hash="hash", is_active=True)
    session.add(user)
    session.flush()
    return user


def create_meal_plan(session: Session, user: User) -> MealPlan:
    plan = MealPlan(
        user_id=user.id,
        plan_date=date(2026, 11, 20),
        title="Test plan",
        request_constraints={},
        status="draft",
        ai_provider="test",
    )
    session.add(plan)
    session.flush()
    return plan


def test_models_import_and_public_recipe_can_have_no_user(db_session: Session) -> None:
    recipe = Recipe(
        user_id=None,
        name="Public recipe",
        description="System recipe",
        servings=1,
        estimated_minutes=10,
        steps=[],
        source_type="manual",
    )
    db_session.add(recipe)
    db_session.flush()

    assert recipe.user_id is None


def test_foreign_key_rejects_unknown_user(db_session: Session) -> None:
    item = InventoryItem(
        user_id=uuid4(),
        display_name="Rice",
        quantity=Decimal("1.000"),
        unit="kg",
        version=1,
    )
    db_session.add(item)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_inventory_quantity_cannot_be_negative(db_session: Session) -> None:
    user = create_user(db_session)
    item = InventoryItem(
        user_id=user.id,
        display_name="Rice",
        quantity=Decimal("-0.001"),
        unit="kg",
        version=1,
    )
    db_session.add(item)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_username_must_be_unique(db_session: Session) -> None:
    create_user(db_session, "duplicate")
    db_session.add(User(username="user_duplicate", email="another@example.test", password_hash="hash", is_active=True))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_email_must_be_unique(db_session: Session) -> None:
    create_user(db_session, "duplicate")
    db_session.add(User(username="another_username", email="duplicate@example.test", password_hash="hash", is_active=True))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_meal_plan_status_check(db_session: Session) -> None:
    user = create_user(db_session)
    db_session.add(
        MealPlan(
            user_id=user.id,
            plan_date=date(2026, 11, 20),
            title="Invalid status",
            request_constraints={},
            status="cancelled",
            ai_provider="test",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_shopping_item_status_check(db_session: Session) -> None:
    user = create_user(db_session)
    db_session.add(
        ShoppingItem(
            user_id=user.id,
            display_name="Milk",
            quantity=Decimal("1.000"),
            unit="box",
            status="unknown",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_idempotency_key_is_unique_per_user(db_session: Session) -> None:
    user = create_user(db_session)
    plan = create_meal_plan(db_session, user)
    first = MealPlanConfirmation(
        user_id=user.id,
        meal_plan_id=plan.id,
        idempotency_key="same-key",
        request_hash="hash-a",
        result_snapshot={},
    )
    db_session.add(first)
    db_session.flush()
    db_session.add(
        MealPlanConfirmation(
            user_id=user.id,
            meal_plan_id=plan.id,
            idempotency_key="same-key",
            request_hash="hash-a",
            result_snapshot={},
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_multiple_transactions_can_share_confirmation_operation(db_session: Session) -> None:
    user = create_user(db_session)
    ingredient = IngredientCatalog(canonical_name="rice", category="grain", default_unit="g")
    db_session.add(ingredient)
    db_session.flush()
    inventory_item = InventoryItem(
        user_id=user.id,
        ingredient_id=ingredient.id,
        display_name="Rice",
        quantity=Decimal("500.000"),
        unit="g",
        version=1,
    )
    db_session.add(inventory_item)
    plan = create_meal_plan(db_session, user)
    confirmation = MealPlanConfirmation(
        user_id=user.id,
        meal_plan_id=plan.id,
        idempotency_key="operation-key",
        request_hash="request-hash",
        result_snapshot={},
    )
    db_session.add(confirmation)
    db_session.flush()
    db_session.add_all(
        [
            InventoryTransaction(
                user_id=user.id,
                inventory_item_id=inventory_item.id,
                delta_quantity=Decimal("-100.000"),
                unit="g",
                reason="meal_plan_deduction",
                source_type="manual",
                operation_id=confirmation.id,
            ),
            InventoryTransaction(
                user_id=user.id,
                inventory_item_id=inventory_item.id,
                delta_quantity=Decimal("-50.000"),
                unit="g",
                reason="meal_plan_deduction",
                source_type="manual",
                operation_id=confirmation.id,
            ),
        ]
    )
    db_session.flush()

    count = db_session.scalar(
        select(func.count()).select_from(InventoryTransaction).where(InventoryTransaction.operation_id == confirmation.id)
    )
    assert count == 2
