"""ORM 模型。

归属：B 组（后端/数据）。新增模型必须与 Alembic 迁移在同一个 PR 内提交。

数据表清单见 文档/05 §2：
users / user_preferences / ingredient_catalog / inventory_items /
inventory_transactions / recipes / recipe_ingredients / meal_plans /
meal_plan_items / meal_plan_ingredients / shopping_items
"""

from app.db.base import Base

__all__ = ["Base"]
