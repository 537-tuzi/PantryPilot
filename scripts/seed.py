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
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo


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

from sqlalchemy import bindparam, inspect, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
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
    # 「今天」必须与应用一致：容器系统时区是 UTC，而临期判定按 APP_TIMEZONE 的
    # 今天计算（docs/adr/0001-app-timezone.md）。用 date.today() 会在 UTC 16:00
    # 之后（即上海时间次日 0 点起）差一天，导致演示数据的到期日偏移。
    today = datetime.now(ZoneInfo(settings.app_timezone)).date()

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
                    INSERT INTO users (id, username, email, password_hash, is_active, created_at, updated_at)
                    VALUES (:id, :username, :email, :password_hash, true, now(), now())
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email,
                        password_hash = EXCLUDED.password_hash,
                        is_active = true,
                        updated_at = now()
                    """
                ),
                {
                    # 主键由 Python 侧生成（模型用 default=uuid4，数据库没有默认值），
                    # 裸 SQL 插入必须自己提供 id
                    "id": uuid4(),
                    "username": DEMO_USERNAME,
                    "email": DEMO_EMAIL,
                    # 使用与应用登录一致的 Argon2id 哈希，不写入明文密码。
                    "password_hash": hash_password(DEMO_PASSWORD),
                },
            )
            print("已写入演示账户")

        if table_exists(inspector, "ingredient_catalog"):
            for name, category, unit, *_ in INGREDIENTS:
                conn.execute(
                    text(
                        """
                        INSERT INTO ingredient_catalog (id, canonical_name, category, default_unit)
                        VALUES (:id, :name, :category, :unit)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"id": uuid4(), "name": name, "category": category, "unit": unit},
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
            # 重跑幂等：先清掉**本脚本上次写入的批次**（演示账户 + 同名同单位），
            # 再写入关联食材库的批次。
            #
            # 范围刻意收窄到「名称 + 单位」与 INGREDIENTS 匹配的批次：
            # 演示账户上手工添加的条目不属于本脚本的产物，不该被 seed 顺手清掉。
            # 清理顺序必须是先流水后库存 —— inventory_transactions.inventory_item_id
            # 是 ON DELETE RESTRICT。
            seeded_pairs = [(name, unit) for name, _category, unit, *_rest in INGREDIENTS]
            seeded_items = conn.execute(
                text(
                    """
                    SELECT id FROM inventory_items
                    WHERE user_id = :user_id AND (display_name, unit) IN :pairs
                    """
                ).bindparams(bindparam("pairs", expanding=True)),
                {"user_id": user_id, "pairs": seeded_pairs},
            ).scalars().all()

            if seeded_items:
                if table_exists(inspector, "inventory_transactions"):
                    conn.execute(
                        text(
                            "DELETE FROM inventory_transactions "
                            "WHERE inventory_item_id = ANY(:ids)"
                        ),
                        {"ids": list(seeded_items)},
                    )
                conn.execute(
                    text("DELETE FROM inventory_items WHERE id = ANY(:ids)"),
                    {"ids": list(seeded_items)},
                )
                print(f"已清理上次写入的演示批次 {len(seeded_items)} 条")

            for name, _category, unit, qty, location, offset in INGREDIENTS:
                # 关联食材库，使分类筛选（inner join ingredient_id）真实可用；
                # 食材库表缺失时降级为不关联（保持脚本跳过缺失表的约定）
                ingredient_id = None
                if table_exists(inspector, "ingredient_catalog"):
                    ingredient_id = conn.execute(
                        text("SELECT id FROM ingredient_catalog WHERE canonical_name = :name"),
                        {"name": name},
                    ).scalar()
                item_id = uuid4()
                conn.execute(
                    text(
                        """
                        INSERT INTO inventory_items
                            (id, user_id, ingredient_id, display_name, quantity, unit,
                             purchase_date, expiry_date, storage_location, version,
                             created_at, updated_at)
                        VALUES
                            (:id, :user_id, :ingredient_id, :name, :qty, :unit,
                             :purchase_date, :expiry_date, :location, 1, now(), now())
                        """
                    ),
                    {
                        "id": item_id,
                        "user_id": user_id,
                        "ingredient_id": ingredient_id,
                        "name": name,
                        "qty": qty,
                        "unit": unit,
                        "purchase_date": today,
                        "expiry_date": today + timedelta(days=offset),
                        "location": location,
                    },
                )
                # 每次入库都要写流水：本仓的不变量是 sum(delta_quantity) == quantity。
                # 缺流水会让演示数据的审计链断裂（详见 docs/adr/0002 与库存流水约束）。
                if table_exists(inspector, "inventory_transactions"):
                    conn.execute(
                        text(
                            """
                            INSERT INTO inventory_transactions
                                (id, user_id, inventory_item_id, delta_quantity, unit,
                                 reason, source_type, created_at, updated_at)
                            VALUES
                                (:id, :user_id, :inventory_item_id, :delta, :unit,
                                 'add', 'manual', now(), now())
                            """
                        ),
                        {
                            "id": uuid4(),
                            "user_id": user_id,
                            "inventory_item_id": item_id,
                            "delta": qty,
                            "unit": unit,
                        },
                    )
            print("已写入库存批次（含临期与过期样例，关联食材库）及其入库流水")


if __name__ == "__main__":
    print(f"目标数据库：{settings.database_url.split('@')[-1]}")
    seed()
