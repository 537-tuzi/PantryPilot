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
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import engine
from app.domain.expiry import current_date
from sqlalchemy import inspect, text

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
    if settings.app_env.strip().lower() not in {"development", "dev", "local", "test"}:
        raise SystemExit("拒绝在非开发/测试环境写入演示账户")

    inspector = inspect(engine)
    today = current_date()

    with engine.begin() as conn:
        user_id = None
        if table_exists(inspector, "users"):
            user_id = conn.execute(
                text(
                    """
                    INSERT INTO users
                        (id, username, email, password_hash, is_active, created_at, updated_at)
                    VALUES
                        (:id, :username, :email, :password_hash, true, now(), now())
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email,
                        password_hash = EXCLUDED.password_hash,
                        is_active = true,
                        updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "id": uuid4(),
                    "username": DEMO_USERNAME,
                    "email": DEMO_EMAIL,
                    # 使用与应用登录一致的 Argon2id 哈希，不写入明文密码。
                    "password_hash": hash_password(DEMO_PASSWORD),
                },
            ).scalar()
            print("已写入演示账户")

        if table_exists(inspector, "ingredient_catalog"):
            for name, category, unit, *_ in INGREDIENTS:
                conn.execute(
                    text(
                        """
                        INSERT INTO ingredient_catalog
                            (id, canonical_name, category, default_unit)
                        VALUES
                            (:id, :name, :category, :unit)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"id": uuid4(), "name": name, "category": category, "unit": unit},
                )
            print("已写入食材目录")

        if user_id is not None and table_exists(inspector, "inventory_items"):
            existing = conn.execute(
                text("SELECT count(*) FROM inventory_items WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).scalar()
            if existing:
                print("演示账户已有库存，跳过库存写入")
                return

            ledger_enabled = table_exists(inspector, "inventory_transactions")
            for name, _category, unit, qty, location, offset in INGREDIENTS:
                item_id = uuid4()
                conn.execute(
                    text(
                        """
                        INSERT INTO inventory_items
                            (id, user_id, display_name, quantity, unit, purchase_date,
                             expiry_date, storage_location, version, created_at, updated_at)
                        VALUES
                            (:id, :user_id, :name, :qty, :unit, :purchase_date,
                             :expiry_date, :location, 1, now(), now())
                        """
                    ),
                    {
                        "id": item_id,
                        "user_id": user_id,
                        "name": name,
                        "qty": qty,
                        "unit": unit,
                        "purchase_date": today,
                        "expiry_date": today + timedelta(days=offset),
                        "location": location,
                    },
                )
                if ledger_enabled:
                    conn.execute(
                        text(
                            """
                            INSERT INTO inventory_transactions
                                (id, user_id, inventory_item_id, delta_quantity, unit,
                                 reason, source_type)
                            VALUES
                                (:id, :user_id, :item_id, :qty, :unit,
                                 'add', 'manual')
                            """
                        ),
                        {
                            "id": uuid4(),
                            "user_id": user_id,
                            "item_id": item_id,
                            "qty": qty,
                            "unit": unit,
                        },
                    )
            print("已写入库存批次与初始流水（含临期与过期样例）")


if __name__ == "__main__":
    print(f"目标数据库：{settings.database_url.split('@')[-1]}")
    seed()
