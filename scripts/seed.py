"""插入合成演示数据（演示账户与合成食材）。

约定（文档/07 §2）：自动化测试与演示一律使用合成账户、合成食材，
不得导入真实个人数据。

用法：
    python scripts/seed.py            # 使用环境变量中的 DATABASE_URL
    docker compose -f deploy/docker-compose.yml exec backend python scripts/seed.py

说明：脚本按 文档/05 §2 的表结构写入，并对不存在的表/字段做跳过处理，
便于在模型尚未全部落地时也能运行。
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path


def _bootstrap_import_path() -> None:
    """把后端包目录加入 sys.path。

    兼容三种运行方式：
      - 仓库布局： <repo>/scripts/seed.py + <repo>/backend/app
      - 容器布局： /app/scripts/seed.py    + /app/app
      - 直接在 backend 目录下运行
    """
    here = Path(__file__).resolve()
    for candidate in (here.parents[1] / "backend", here.parents[1], Path.cwd()):
        if (candidate / "app" / "__init__.py").exists():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("未找到后端包目录（app/），请在仓库根目录或 backend 目录下运行")


_bootstrap_import_path()

from sqlalchemy import inspect, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import engine  # noqa: E402

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"  # 仅用于本地演示，公开仓库与线上环境必须更换

INGREDIENTS = [
    # 名称、分类、默认单位、库存数量、存储位置、到期日偏移（天）
    ("牛奶", "乳制品", "盒", 1, "冷藏", 1),
    ("菠菜", "蔬菜", "g", 300, "冷藏", 2),
    ("鸡蛋", "蛋类", "个", 6, "冷藏", 3),
    ("番茄", "蔬菜", "g", 500, "常温", 11),
    ("牛肉", "肉类", "g", 400, "冷冻", 18),
    ("酸奶", "乳制品", "杯", 2, "冷藏", -2),
]


def table_exists(inspector: object, name: str) -> bool:
    """判断表是否存在。"""
    return name in inspector.get_table_names()  # type: ignore[attr-defined]


def seed() -> None:
    """写入合成数据。"""
    inspector = inspect(engine)
    today = date.today()

    known = ("users", "ingredient_catalog", "inventory_items")
    if not any(table_exists(inspector, name) for name in known):
        print(
            "未发现业务表（users / ingredient_catalog / inventory_items）。"
            "业务模型尚未落地时属正常情况；模型就绪后请先执行 alembic upgrade head 再重跑本脚本。"
        )
        return

    with engine.begin() as conn:
        if table_exists(inspector, "users"):
            conn.execute(
                text(
                    """
                    INSERT INTO users (username, email, password_hash, is_active, created_at, updated_at)
                    VALUES (:username, :email, :password_hash, true, now(), now())
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "username": DEMO_USERNAME,
                    "email": DEMO_EMAIL,
                    # 占位哈希；正式实现应使用 app.core.security 的哈希函数
                    "password_hash": "REPLACE_WITH_ARGON2_HASH",
                },
            )
            print("已写入演示账户（需在正式实现中补齐密码哈希）")

        if table_exists(inspector, "ingredient_catalog"):
            for name, category, unit, *_ in INGREDIENTS:
                conn.execute(
                    text(
                        """
                        INSERT INTO ingredient_catalog (canonical_name, category, default_unit)
                        VALUES (:name, :category, :unit)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"name": name, "category": category, "unit": unit},
                )
            print("已写入食材目录")

        if table_exists(inspector, "inventory_items"):
            user_id = conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": DEMO_USERNAME},
            ).scalar()
            if user_id is None:
                print("未找到演示账户，跳过库存写入")
                return
            for name, _category, unit, qty, location, offset in INGREDIENTS:
                conn.execute(
                    text(
                        """
                        INSERT INTO inventory_items
                            (user_id, display_name, quantity, unit, purchase_date, expiry_date,
                             storage_location, created_at, updated_at)
                        VALUES
                            (:user_id, :name, :qty, :unit, :purchase_date, :expiry_date,
                             :location, now(), now())
                        """
                    ),
                    {
                        "user_id": user_id,
                        "name": name,
                        "qty": qty,
                        "unit": unit,
                        "purchase_date": today,
                        "expiry_date": today + timedelta(days=offset),
                        "location": location,
                    },
                )
            print("已写入库存批次（含临期与过期样例）")


if __name__ == "__main__":
    print(f"目标数据库：{settings.database_url.split('@')[-1]}")
    seed()
