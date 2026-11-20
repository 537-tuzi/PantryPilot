"""Create the initial PantryPilot business schema.

Revision ID: 20261120_0001
Revises:
Create Date: 2026-11-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261120_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "ingredient_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("default_unit", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingredient_catalog")),
        sa.UniqueConstraint("canonical_name", name=op.f("uq_ingredient_catalog_canonical_name")),
    )
    op.create_index(
        "uq_ingredient_catalog_canonical_name_normalized",
        "ingredient_catalog",
        [sa.text("lower(btrim(canonical_name))")],
        unique=True,
    )
    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dietary_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("allergens", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("disliked_ingredients", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("default_servings", sa.Integer(), nullable=False),
        sa.Column("default_budget", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("default_cooking_minutes", sa.Integer(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_preferences_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_preferences")),
    )
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("storage_location", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_inventory_items_quantity_nonnegative")),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient_catalog.id"], name=op.f("fk_inventory_items_ingredient_id_ingredient_catalog"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_inventory_items_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_items")),
    )
    op.create_index("ix_inventory_items_user_id_expiry_date", "inventory_items", ["user_id", "expiry_date"], unique=False)
    op.create_index("ix_inventory_items_user_id_ingredient_id", "inventory_items", ["user_id", "ingredient_id"], unique=False)
    op.create_table(
        "recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("source_type IN ('manual', 'ai', 'import')", name=op.f("ck_recipes_source_type_allowed_values")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_recipes_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipes")),
    )
    op.create_table(
        "meal_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("request_constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("ai_provider", sa.Text(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("status IN ('draft', 'confirmed')", name=op.f("ck_meal_plans_status_allowed_values")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_meal_plans_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plans")),
    )
    op.create_index("ix_meal_plans_user_id_plan_date_status", "meal_plans", ["user_id", "plan_date", "status"], unique=False)
    op.create_table(
        "meal_plan_confirmations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meal_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("result_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"], name=op.f("fk_meal_plan_confirmations_meal_plan_id_meal_plans"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_meal_plan_confirmations_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plan_confirmations")),
        sa.UniqueConstraint("user_id", "idempotency_key", name="user_idempotency_key"),
    )
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("is_optional", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient_catalog.id"], name=op.f("fk_recipe_ingredients_ingredient_id_ingredient_catalog"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], name=op.f("fk_recipe_ingredients_recipe_id_recipes"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_ingredients")),
    )
    op.create_table(
        "meal_plan_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meal_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recipe_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"], name=op.f("fk_meal_plan_items_meal_plan_id_meal_plans"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], name=op.f("fk_meal_plan_items_recipe_id_recipes"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plan_items")),
    )
    op.create_table(
        "meal_plan_ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meal_plan_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("required_quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("actual_quantity", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("is_missing", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"], name=op.f("fk_meal_plan_ingredients_inventory_item_id_inventory_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["meal_plan_item_id"], ["meal_plan_items.id"], name=op.f("fk_meal_plan_ingredients_meal_plan_item_id_meal_plan_items"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plan_ingredients")),
    )
    op.create_table(
        "shopping_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_meal_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("status IN ('pending', 'purchased', 'cancelled')", name=op.f("ck_shopping_items_status_allowed_values")),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient_catalog.id"], name=op.f("fk_shopping_items_ingredient_id_ingredient_catalog"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_meal_plan_id"], ["meal_plans.id"], name=op.f("fk_shopping_items_source_meal_plan_id_meal_plans"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_shopping_items_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopping_items")),
    )
    op.create_index("ix_shopping_items_user_id_status_created_at", "shopping_items", ["user_id", "status", "created_at"], unique=False)
    op.create_table(
        "inventory_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delta_quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("reason IN ('add', 'adjust', 'consume', 'meal_plan_deduction')", name=op.f("ck_inventory_transactions_reason_allowed_values")),
        sa.CheckConstraint("source_type IN ('manual', 'ai', 'import')", name=op.f("ck_inventory_transactions_source_type_allowed_values")),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"], name=op.f("fk_inventory_transactions_inventory_item_id_inventory_items"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["operation_id"], ["meal_plan_confirmations.id"], name=op.f("fk_inventory_transactions_operation_id_meal_plan_confirmations"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_inventory_transactions_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_transactions")),
    )
    op.create_index("ix_inventory_transactions_operation_id", "inventory_transactions", ["operation_id"], unique=False)
    op.create_index("ix_inventory_transactions_user_id_inventory_item_id_created_at", "inventory_transactions", ["user_id", "inventory_item_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inventory_transactions_user_id_inventory_item_id_created_at", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_operation_id", table_name="inventory_transactions")
    op.drop_table("inventory_transactions")
    op.drop_index("ix_shopping_items_user_id_status_created_at", table_name="shopping_items")
    op.drop_table("shopping_items")
    op.drop_table("meal_plan_ingredients")
    op.drop_table("meal_plan_items")
    op.drop_table("recipe_ingredients")
    op.drop_table("meal_plan_confirmations")
    op.drop_index("ix_meal_plans_user_id_plan_date_status", table_name="meal_plans")
    op.drop_table("meal_plans")
    op.drop_table("recipes")
    op.drop_index("ix_inventory_items_user_id_ingredient_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_user_id_expiry_date", table_name="inventory_items")
    op.drop_table("inventory_items")
    op.drop_table("user_preferences")
    op.drop_index("uq_ingredient_catalog_canonical_name_normalized", table_name="ingredient_catalog")
    op.drop_table("ingredient_catalog")
    op.drop_table("users")
