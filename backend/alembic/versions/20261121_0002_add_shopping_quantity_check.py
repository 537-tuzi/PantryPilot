"""Enforce positive quantities for shopping items.

Revision ID: 20261121_0002
Revises: 20261120_0001
Create Date: 2026-11-21
"""

from alembic import op

revision = "20261121_0002"
down_revision = "20261120_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_shopping_items_quantity_positive", "shopping_items", "quantity > 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_shopping_items_quantity_positive", "shopping_items", type_="check")
