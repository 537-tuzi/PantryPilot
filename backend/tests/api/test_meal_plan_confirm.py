"""Meal plan confirmation tests against the real PostgreSQL test database."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import ResourceNotFoundError
from app.core.security import create_access_token
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.meal_plan import MealPlan, MealPlanIngredient, MealPlanItem
from app.models.meal_plan_confirmation import MealPlanConfirmation
from app.models.recipe import Recipe
from app.models.user import User
from app.services.meal_plan_service import MealPlanService
from app.services.recipe_service import RecipeService

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
TEST_MAINTENANCE_DATABASE_URL = os.getenv("TEST_MAINTENANCE_DATABASE_URL")


def make_user(db: Session, suffix: str | None = None) -> User:
    tag = suffix or uuid4().hex[:10]
    user = User(
        username=f"user_{tag}",
        email=f"user_{tag}@example.com",
        password_hash="not-a-real-hash",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def make_inventory(
    db: Session, user: User, quantity: str = "10.000", unit: str = "g", name: str = "Tomato"
) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
        display_name=name,
        quantity=Decimal(quantity),
        unit=unit,
        version=1,
    )
    db.add(item)
    db.flush()
    return item


def make_plan(
    db: Session,
    user: User,
    lines: list[tuple[InventoryItem | None, str, str, str]],
    provider: str = "mock-ai",
) -> tuple[MealPlan, list[MealPlanIngredient]]:
    """lines: (inventory_item, display_name, required_quantity, unit)."""
    recipe = Recipe(
        user_id=user.id,
        name="Test recipe",
        description="",
        servings=1,
        estimated_minutes=10,
        steps=[],
        source_type="ai",
    )
    db.add(recipe)
    db.flush()

    plan = MealPlan(
        user_id=user.id,
        plan_date=date(2026, 11, 20),
        title="Test plan",
        request_constraints={},
        status="draft",
        ai_provider=provider,
    )
    db.add(plan)
    db.flush()

    plan_item = MealPlanItem(
        meal_plan_id=plan.id,
        recipe_id=recipe.id,
        recipe_snapshot={},
        sort_order=0,
    )
    db.add(plan_item)
    db.flush()

    ingredients: list[MealPlanIngredient] = []
    for inventory_item, display_name, required, unit in lines:
        ingredient = MealPlanIngredient(
            meal_plan_item_id=plan_item.id,
            inventory_item_id=inventory_item.id if inventory_item else None,
            display_name=display_name,
            required_quantity=Decimal(required),
            unit=unit,
            is_missing=False,
        )
        db.add(ingredient)
        ingredients.append(ingredient)
    db.flush()
    return plan, ingredients


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid4())}


def confirm(
    client: TestClient,
    user: User,
    plan: MealPlan,
    items: list[dict],
    key: str | None = None,
) -> object:
    headers = auth_headers(user)
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post(
        f"/api/v1/meal-plans/{plan.id}/confirm", json={"items": items}, headers=headers
    )


def item_payload(ingredient: MealPlanIngredient, quantity: str, unit: str | None = None) -> dict:
    return {
        "meal_plan_ingredient_id": str(ingredient.id),
        "inventory_item_id": str(ingredient.inventory_item_id),
        "actual_quantity": quantity,
        "unit": unit or ingredient.unit,
    }


def transaction_rows(db: Session, user: User) -> list[InventoryTransaction]:
    db.expire_all()
    statement = (
        select(InventoryTransaction)
        .where(InventoryTransaction.user_id == user.id)
        .order_by(InventoryTransaction.inventory_item_id)
    )
    return list(db.scalars(statement))


# 1. 正常确认
def test_confirm_success(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "4.000", "g")])

    response = confirm(client, user, plan, [item_payload(ingredients[0], "4.000")])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["deducted"][0]["delta_quantity"] == "-4.000"

    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("6.000")
    assert db_session.get(MealPlan, plan.id).status == "confirmed"
    assert db_session.get(MealPlan, plan.id).confirmed_at is not None
    assert db_session.get(MealPlanIngredient, ingredients[0].id).actual_quantity == Decimal("4.000")


# 2. 多条库存记录扣减
def test_confirm_multiple_inventory_batches(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    first = make_inventory(db_session, user, "10.000", "g", "Tomato")
    second = make_inventory(db_session, user, "5.000", "g", "Basil")
    plan, ingredients = make_plan(
        db_session,
        user,
        [(first, "Tomato", "2.000", "g"), (second, "Basil", "1.000", "g")],
    )

    response = confirm(
        client,
        user,
        plan,
        [item_payload(ingredients[0], "2.000"), item_payload(ingredients[1], "1.000")],
    )

    assert response.status_code == 200, response.text
    assert len(response.json()["deducted"]) == 2
    db_session.expire_all()
    assert db_session.get(InventoryItem, first.id).quantity == Decimal("8.000")
    assert db_session.get(InventoryItem, second.id).quantity == Decimal("4.000")


# 3 & 4. 同一库存批次被多个菜品共享，汇总数量正确
def test_shared_batch_is_aggregated_once(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    shared = make_inventory(db_session, user, "10.000", "g", "Tomato")

    recipe = Recipe(
        user_id=user.id,
        name="Shared",
        description="",
        servings=1,
        estimated_minutes=5,
        steps=[],
        source_type="ai",
    )
    db_session.add(recipe)
    db_session.flush()
    plan = MealPlan(
        user_id=user.id,
        plan_date=date(2026, 11, 20),
        title="Shared",
        request_constraints={},
        status="draft",
        ai_provider="mock-ai",
    )
    db_session.add(plan)
    db_session.flush()

    ingredients = []
    for order in range(2):
        plan_item = MealPlanItem(
            meal_plan_id=plan.id, recipe_id=recipe.id, recipe_snapshot={}, sort_order=order
        )
        db_session.add(plan_item)
        db_session.flush()
        ingredient = MealPlanIngredient(
            meal_plan_item_id=plan_item.id,
            inventory_item_id=shared.id,
            display_name="Tomato",
            required_quantity=Decimal("2.000"),
            unit="g",
            is_missing=False,
        )
        db_session.add(ingredient)
        ingredients.append(ingredient)
    db_session.flush()

    response = confirm(
        client,
        user,
        plan,
        [item_payload(ingredients[0], "2.000"), item_payload(ingredients[1], "3.000")],
    )

    assert response.status_code == 200, response.text
    deducted = response.json()["deducted"]
    assert len(deducted) == 1
    assert deducted[0]["delta_quantity"] == "-5.000"

    db_session.expire_all()
    assert db_session.get(InventoryItem, shared.id).quantity == Decimal("5.000")
    rows = transaction_rows(db_session, user)
    assert len(rows) == 1
    assert rows[0].delta_quantity == Decimal("-5.000")


# 5. 一个食材使用多个库存批次
def test_one_ingredient_across_batches(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    batch_a = make_inventory(db_session, user, "1.000", "g", "Flour")
    batch_b = make_inventory(db_session, user, "3.000", "g", "Flour")
    plan, ingredients = make_plan(
        db_session,
        user,
        [(batch_a, "Flour", "1.000", "g"), (batch_b, "Flour", "2.000", "g")],
    )

    response = confirm(
        client,
        user,
        plan,
        [item_payload(ingredients[0], "1.000"), item_payload(ingredients[1], "2.000")],
    )

    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert db_session.get(InventoryItem, batch_a.id).quantity == Decimal("0.000")
    assert db_session.get(InventoryItem, batch_b.id).quantity == Decimal("1.000")


# 6. 库存不足整体回滚
def test_insufficient_stock_rolls_back_everything(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    enough = make_inventory(db_session, user, "10.000", "g", "Tomato")
    short = make_inventory(db_session, user, "0.500", "g", "Basil")
    plan, ingredients = make_plan(
        db_session,
        user,
        [(enough, "Tomato", "2.000", "g"), (short, "Basil", "5.000", "g")],
    )

    response = confirm(
        client,
        user,
        plan,
        [item_payload(ingredients[0], "2.000"), item_payload(ingredients[1], "5.000")],
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INSUFFICIENT_STOCK"

    db_session.expire_all()
    assert db_session.get(InventoryItem, enough.id).quantity == Decimal("10.000")
    assert db_session.get(InventoryItem, short.id).quantity == Decimal("0.500")
    assert db_session.get(MealPlan, plan.id).status == "draft"
    assert transaction_rows(db_session, user) == []
    assert (
        db_session.scalar(
            select(MealPlanConfirmation).where(MealPlanConfirmation.meal_plan_id == plan.id)
        )
        is None
    )


# 7. 单位不匹配
def test_unit_mismatch_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000", "g")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "2.000", "g")])

    response = confirm(client, user, plan, [item_payload(ingredients[0], "2.000", "kg")])

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("10.000")


# 8. 实际用量超过 required_quantity 允许
def test_actual_exceeds_required_is_allowed(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "2.000", "g")])

    response = confirm(client, user, plan, [item_payload(ingredients[0], "5.000")])

    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("5.000")
    assert db_session.get(MealPlanIngredient, ingredients[0].id).is_missing is False


# 9. 实际用量超过可用库存
def test_actual_exceeds_available_stock(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "1.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "2.000", "g")])

    response = confirm(client, user, plan, [item_payload(ingredients[0], "2.000")])

    assert response.status_code == 409
    assert response.json()["code"] == "INSUFFICIENT_STOCK"


# 10. 相同 Key 重复提交
def test_idempotent_replay(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "4.000", "g")])
    key = str(uuid4())

    first = confirm(client, user, plan, [item_payload(ingredients[0], "4.000")], key)
    second = confirm(client, user, plan, [item_payload(ingredients[0], "4.000")], key)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()

    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("6.000")
    assert len(transaction_rows(db_session, user)) == 1
    assert (
        len(
            db_session.scalars(
                select(MealPlanConfirmation).where(MealPlanConfirmation.idempotency_key == key)
            ).all()
        )
        == 1
    )


# 11. 相同 Key 不同请求内容
def test_same_key_different_payload_conflicts(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "4.000", "g")])
    key = str(uuid4())

    first = confirm(client, user, plan, [item_payload(ingredients[0], "4.000")], key)
    second = confirm(client, user, plan, [item_payload(ingredients[0], "3.000")], key)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "STATE_CONFLICT"


# 12. 已确认计划使用不同 Key 再次确认
def test_already_confirmed_with_new_key_conflicts(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "4.000", "g")])

    first = confirm(client, user, plan, [item_payload(ingredients[0], "4.000")], str(uuid4()))
    second = confirm(client, user, plan, [item_payload(ingredients[0], "1.000")], str(uuid4()))

    assert first.status_code == 200
    assert second.status_code == 409
    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("6.000")


# 13. 并发相同 Key 不会重复扣减
def test_repeated_same_key_only_deducts_once(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "4.000", "g")])
    key = str(uuid4())
    payload = [item_payload(ingredients[0], "4.000")]

    results = [confirm(client, user, plan, payload, key) for _ in range(3)]

    assert {response.status_code for response in results} == {200}
    assert results[0].json() == results[-1].json()
    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("6.000")
    assert len(transaction_rows(db_session, user)) == 1


def test_unique_constraint_blocks_duplicate_confirmation(db_session: Session) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, _ = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])
    key = str(uuid4())

    for _ in range(1):
        db_session.add(
            MealPlanConfirmation(
                user_id=user.id,
                meal_plan_id=plan.id,
                idempotency_key=key,
                request_hash="hash",
                result_snapshot={},
            )
        )
        db_session.flush()

    db_session.add(
        MealPlanConfirmation(
            user_id=user.id,
            meal_plan_id=plan.id,
            idempotency_key=key,
            request_hash="hash",
            result_snapshot={},
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# 14. 不同 Key 并发确认同一计划由 FOR UPDATE 串行化
@pytest.mark.skipif(
    not TEST_DATABASE_URL or not TEST_MAINTENANCE_DATABASE_URL,
    reason="TEST_DATABASE_URL and TEST_MAINTENANCE_DATABASE_URL are required",
)
def test_row_lock_serializes_concurrent_confirmations(db_session: Session) -> None:
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, future=True)
    setup_sessionmaker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    setup = setup_sessionmaker()
    try:
        user = make_user(setup, uuid4().hex[:10])
        plan, _ = make_plan(setup, user, [], provider="manual")
        setup.commit()
        plan_id = plan.id
        user_id = user.id

        holder = setup_sessionmaker()
        waiter = setup_sessionmaker()
        try:
            holder.execute(
                text("SELECT id FROM meal_plans WHERE id = :plan_id FOR UPDATE"),
                {"plan_id": plan_id},
            )
            with pytest.raises(Exception) as excinfo:
                waiter.execute(
                    text("SELECT id FROM meal_plans WHERE id = :plan_id FOR UPDATE NOWAIT"),
                    {"plan_id": plan_id},
                )
            assert "lock" in str(excinfo.value).lower()
            holder.rollback()
            waiter.rollback()
        finally:
            holder.close()
            waiter.close()

        maintenance_engine = create_engine(
            TEST_MAINTENANCE_DATABASE_URL, pool_pre_ping=True, future=True
        )
        cleanup_sessionmaker = sessionmaker(bind=maintenance_engine)
        cleanup = cleanup_sessionmaker()
        try:
            cleanup.execute(
                text(
                    "DELETE FROM meal_plan_ingredients WHERE meal_plan_item_id IN "
                    "(SELECT id FROM meal_plan_items WHERE meal_plan_id = :plan_id)"
                ),
                {"plan_id": plan_id},
            )
            cleanup.execute(
                text("DELETE FROM meal_plan_items WHERE meal_plan_id = :plan_id"),
                {"plan_id": plan_id},
            )
            cleanup.execute(
                text("DELETE FROM meal_plans WHERE id = :plan_id"), {"plan_id": plan_id}
            )
            cleanup.execute(
                text("DELETE FROM recipes WHERE user_id = :user_id"), {"user_id": user_id}
            )
            cleanup.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            cleanup.commit()
        finally:
            cleanup.close()
            maintenance_engine.dispose()
    finally:
        setup.close()
        engine.dispose()


# 15. 用户 A 无法确认用户 B 的计划
def test_cannot_confirm_other_users_plan(db_session: Session, client: TestClient) -> None:
    owner = make_user(db_session)
    intruder = make_user(db_session)
    inventory_item = make_inventory(db_session, owner, "10.000")
    plan, ingredients = make_plan(db_session, owner, [(inventory_item, "Tomato", "1.000", "g")])

    response = confirm(client, intruder, plan, [item_payload(ingredients[0], "1.000")])

    assert response.status_code == 404
    db_session.expire_all()
    assert db_session.get(MealPlan, plan.id).status == "draft"
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("10.000")


# 16. 用户 A 无法扣减用户 B 的库存
def test_cannot_deduct_other_users_inventory(db_session: Session, client: TestClient) -> None:
    owner_a = make_user(db_session)
    owner_b = make_user(db_session)
    inventory_b = make_inventory(db_session, owner_b, "10.000", "g", "Basil")
    plan_a, ingredients = make_plan(db_session, owner_a, [(inventory_b, "Basil", "1.000", "g")])

    response = confirm(client, owner_a, plan_a, [item_payload(ingredients[0], "1.000")])

    assert response.status_code == 404
    db_session.expire_all()
    assert db_session.get(InventoryItem, inventory_b.id).quantity == Decimal("10.000")
    assert db_session.get(MealPlan, plan_a.id).status == "draft"


# 17. 公共菜谱读取
def test_public_recipe_is_readable(db_session: Session) -> None:
    reader = make_user(db_session)
    recipe = Recipe(
        user_id=None,
        name="Public",
        description="",
        servings=2,
        estimated_minutes=15,
        steps=[],
        source_type="manual",
    )
    db_session.add(recipe)
    db_session.flush()

    result = RecipeService().get_visible(db_session, reader.id, recipe.id)

    assert result.id == recipe.id
    assert result.user_id is None


# 18. 私人菜谱越权访问
def test_private_recipe_is_hidden(db_session: Session) -> None:
    owner = make_user(db_session)
    intruder = make_user(db_session)
    recipe = Recipe(
        user_id=owner.id,
        name="Private",
        description="",
        servings=1,
        estimated_minutes=5,
        steps=[],
        source_type="manual",
    )
    db_session.add(recipe)
    db_session.flush()

    assert RecipeService().get_visible(db_session, owner.id, recipe.id).id == recipe.id
    with pytest.raises(ResourceNotFoundError):
        RecipeService().get_visible(db_session, intruder.id, recipe.id)


# 19 & 22. 失败时 confirmation / 库存 / 流水 / 计划状态全部回滚
def test_failure_leaves_no_confirmation(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "0.100")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "2.000", "g")])
    key = str(uuid4())

    response = confirm(client, user, plan, [item_payload(ingredients[0], "2.000")], key)
    assert response.status_code == 409

    db_session.expire_all()
    assert db_session.get(MealPlan, plan.id).status == "draft"
    assert db_session.get(MealPlan, plan.id).confirmed_at is None
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("0.100")
    assert transaction_rows(db_session, user) == []
    assert (
        db_session.scalar(
            select(MealPlanConfirmation).where(MealPlanConfirmation.idempotency_key == key)
        )
        is None
    )
    assert db_session.get(MealPlanIngredient, ingredients[0].id).actual_quantity is None


# 20. 流水 operation_id 关联正确
def test_transactions_share_operation_id(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    first = make_inventory(db_session, user, "10.000", "g", "Tomato")
    second = make_inventory(db_session, user, "10.000", "g", "Basil")
    plan, ingredients = make_plan(
        db_session,
        user,
        [(first, "Tomato", "1.000", "g"), (second, "Basil", "2.000", "g")],
    )

    response = confirm(
        client,
        user,
        plan,
        [item_payload(ingredients[0], "1.000"), item_payload(ingredients[1], "2.000")],
    )
    assert response.status_code == 200

    db_session.expire_all()
    confirmation = db_session.scalar(
        select(MealPlanConfirmation).where(MealPlanConfirmation.meal_plan_id == plan.id)
    )
    rows = transaction_rows(db_session, user)
    assert len(rows) == 2
    assert {row.operation_id for row in rows} == {confirmation.id}
    assert {row.reason for row in rows} == {"meal_plan_deduction"}
    assert {row.source_type for row in rows} == {"ai"}


def test_manual_plan_uses_manual_source_type(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(
        db_session, user, [(inventory_item, "Tomato", "1.000", "g")], provider="manual"
    )

    response = confirm(client, user, plan, [item_payload(ingredients[0], "1.000")])

    assert response.status_code == 200
    db_session.expire_all()
    assert {row.source_type for row in transaction_rows(db_session, user)} == {"manual"}


def test_import_plan_uses_import_source_type(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(
        db_session, user, [(inventory_item, "Tomato", "1.000", "g")], provider="import"
    )

    response = confirm(client, user, plan, [item_payload(ingredients[0], "1.000")])

    assert response.status_code == 200
    db_session.expire_all()
    assert {row.source_type for row in transaction_rows(db_session, user)} == {"import"}


@pytest.mark.parametrize("provider", ["", "   "])
def test_blank_ai_provider_is_rejected_without_deducting_inventory(
    db_session: Session, client: TestClient, provider: str
) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(
        db_session, user, [(inventory_item, "Tomato", "2.000", "g")], provider=provider
    )

    response = confirm(client, user, plan, [item_payload(ingredients[0], "2.000")])

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    db_session.expire_all()
    assert db_session.get(MealPlan, plan.id).status == "draft"
    assert db_session.get(InventoryItem, inventory_item.id).quantity == Decimal("10.000")
    assert db_session.get(InventoryItem, inventory_item.id).version == 1
    assert transaction_rows(db_session, user) == []
    assert (
        db_session.scalar(
            select(MealPlanConfirmation).where(MealPlanConfirmation.meal_plan_id == plan.id)
        )
        is None
    )


# 21. 缺失食材状态
def test_missing_ingredients_reported(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    full = make_inventory(db_session, user, "10.000", "g", "Tomato")
    partial = make_inventory(db_session, user, "10.000", "g", "Basil")
    absent = make_inventory(db_session, user, "10.000", "g", "Oregano")
    plan, ingredients = make_plan(
        db_session,
        user,
        [
            (full, "Tomato", "2.000", "g"),
            (partial, "Basil", "5.000", "g"),
            (absent, "Oregano", "1.000", "g"),
        ],
    )

    response = confirm(
        client,
        user,
        plan,
        [item_payload(ingredients[0], "2.000"), item_payload(ingredients[1], "1.000")],
    )

    assert response.status_code == 200, response.text
    missing = response.json()["missing"]
    assert len(missing) == 2
    missing_names = {entry["display_name"] for entry in missing}
    assert missing_names == {"Basil", "Oregano"}

    db_session.expire_all()
    assert db_session.get(MealPlanIngredient, ingredients[0].id).is_missing is False
    assert db_session.get(MealPlanIngredient, ingredients[1].id).is_missing is True
    assert db_session.get(MealPlanIngredient, ingredients[2].id).is_missing is True
    assert db_session.get(MealPlanIngredient, ingredients[2].id).actual_quantity is None


def test_duplicate_ingredient_ids_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])
    payload = item_payload(ingredients[0], "1.000")

    response = confirm(client, user, plan, [payload, payload])

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_invalid_idempotency_key_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])

    response = confirm(
        client, user, plan, [item_payload(ingredients[0], "1.000")], key="not-a-uuid"
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_zero_quantity_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])

    response = confirm(client, user, plan, [item_payload(ingredients[0], "0")])

    assert response.status_code == 400


def test_archived_inventory_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])
    inventory_item.archived_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
    db_session.flush()

    response = confirm(client, user, plan, [item_payload(ingredients[0], "1.000")])

    assert response.status_code == 409
    assert response.json()["code"] == "STATE_CONFLICT"


def test_cross_user_plan_ingredient_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    foreign = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, _ = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])
    foreign_plan, foreign_ingredients = make_plan(
        db_session, foreign, [(make_inventory(db_session, foreign, "10.000"), "X", "1.000", "g")]
    )

    response = confirm(client, user, plan, [item_payload(foreign_ingredients[0], "1.000")])

    assert response.status_code == 400
    assert UUID(str(foreign_plan.id)) == foreign_plan.id


def test_ingredient_inventory_mismatch_rejected(db_session: Session, client: TestClient) -> None:
    user = make_user(db_session)
    first = make_inventory(db_session, user, "10.000", "g", "Tomato")
    second = make_inventory(db_session, user, "10.000", "g", "Basil")
    plan, ingredients = make_plan(db_session, user, [(first, "Tomato", "1.000", "g")])

    payload = item_payload(ingredients[0], "1.000")
    payload["inventory_item_id"] = str(second.id)

    response = confirm(client, user, plan, [payload])

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_service_direct_call_returns_snapshot(db_session: Session) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "1.000", "g")])

    from app.schemas.meal_plan import ConfirmItemPayload, MealPlanConfirmPayload

    payload = MealPlanConfirmPayload(
        items=[
            ConfirmItemPayload(
                meal_plan_ingredient_id=ingredients[0].id,
                inventory_item_id=inventory_item.id,
                actual_quantity=Decimal("1.000"),
                unit="g",
            )
        ]
    )
    snapshot = MealPlanService().confirm(db_session, user.id, plan.id, str(uuid4()), payload)

    assert snapshot.status == "confirmed"
    assert snapshot.deducted[0].delta_quantity == Decimal("-1.000")


def test_get_meal_plan_detail_returns_dishes_and_ingredients(
    db_session: Session, client: TestClient
) -> None:
    user = make_user(db_session)
    inventory_item = make_inventory(db_session, user, "10.000", "g", "Tomato")
    plan, ingredients = make_plan(db_session, user, [(inventory_item, "Tomato", "2.000", "g")])

    confirmed = confirm(client, user, plan, [item_payload(ingredients[0], "2.000")])
    assert confirmed.status_code == 200

    response = client.get(f"/api/v1/meal-plans/{plan.id}", headers=auth_headers(user))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(plan.id)
    assert body["status"] == "confirmed"
    assert body["items"][0]["recipe"]["id"]
    ingredient = body["items"][0]["ingredients"][0]
    assert ingredient == {
        "id": str(ingredients[0].id),
        "inventory_item_id": str(inventory_item.id),
        "display_name": "Tomato",
        "required_quantity": "2.000",
        "actual_quantity": "2.000",
        "unit": "g",
        "is_missing": False,
    }


def test_get_meal_plan_detail_hides_other_users_plan(
    db_session: Session, client: TestClient
) -> None:
    owner = make_user(db_session)
    reader = make_user(db_session)
    inventory_item = make_inventory(db_session, owner)
    plan, _ = make_plan(db_session, owner, [(inventory_item, "Tomato", "1.000", "g")])

    response = client.get(f"/api/v1/meal-plans/{plan.id}", headers=auth_headers(reader))

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_get_meal_plan_detail_exposes_public_recipe_but_not_foreign_private_recipe(
    db_session: Session, client: TestClient
) -> None:
    owner = make_user(db_session)
    foreign = make_user(db_session)
    inventory_item = make_inventory(db_session, owner)
    plan, _ = make_plan(db_session, owner, [(inventory_item, "Tomato", "1.000", "g")])
    plan_item = db_session.scalar(select(MealPlanItem).where(MealPlanItem.meal_plan_id == plan.id))
    assert plan_item is not None

    public_recipe = db_session.get(Recipe, plan_item.recipe_id)
    assert public_recipe is not None
    public_recipe.user_id = None
    public_response = client.get(f"/api/v1/meal-plans/{plan.id}", headers=auth_headers(owner))
    assert public_response.status_code == 200
    assert public_response.json()["items"][0]["recipe"]["user_id"] is None

    foreign_recipe = Recipe(
        user_id=foreign.id,
        name="Foreign private recipe",
        description="",
        servings=1,
        estimated_minutes=5,
        steps=[],
        source_type="manual",
    )
    db_session.add(foreign_recipe)
    db_session.flush()
    plan_item.recipe_id = foreign_recipe.id
    db_session.flush()

    private_response = client.get(f"/api/v1/meal-plans/{plan.id}", headers=auth_headers(owner))
    assert private_response.status_code == 200
    assert private_response.json()["items"][0]["recipe"] is None
