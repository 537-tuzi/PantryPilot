# 测试数据库与维护账号

自动化测试只能写入独立的 `pantrypilot_test` 数据库；不得将
`TEST_DATABASE_URL` 指向开发库 `pantrypilot`。测试前先使用应用账号对测试库执行
`alembic upgrade head`，再运行 `pytest`。

少数真实提交并发测试需要在测试结束后定向清理自己创建的记录。它们只能通过独立的
`pantrypilot_test_maintenance` 账号使用 `TEST_MAINTENANCE_DATABASE_URL` 完成，绝不
回退到 `pantrypilot_app`。未配置该变量时，这两项测试会明确跳过，而不会使用应用账号
删除任何流水。

## 一键准备（推荐）

```bash
bash scripts/dev.sh test-db    # 建库 → 授权维护账号 → 迁移测试库
bash scripts/dev.sh test       # 准备测试库并在容器内跑 pytest
```

`test-db` 内部固定按 **建库 → 授权维护账号 → 迁移测试库** 的顺序执行。
顺序不可颠倒：授权脚本按表级权限授权，**必须先有业务表存在**，
否则会报 `relation "users" does not exist`。

需要的两个变量写在仓库根目录 `.env`（不要提交到 Git）：

```
TEST_DATABASE_URL=postgresql+psycopg://pantry:pantry@localhost:5432/pantrypilot_test
TEST_MAINTENANCE_DATABASE_URL=postgresql+psycopg://pantrypilot_test_maintenance:<密码>@localhost:5432/pantrypilot_test
```

容器内运行时，`scripts/dev.sh` 会自动把这两个连接串的主机名改写为 compose 服务名 `db`，
无需手工区分宿主机与容器。

## 手工准备（需要排查时）

```bash
# 1. 建测试库
docker compose -f deploy/docker-compose.yml exec -T db \
  psql -U pantry -d postgres -c "CREATE DATABASE pantrypilot_test"

# 2. 对测试库执行迁移（业务表必须先存在）
docker compose -f deploy/docker-compose.yml --profile test run --rm -T backend-test alembic upgrade head

# 3. 授权维护账号（在迁移之后执行）
docker compose -f deploy/docker-compose.yml exec -T db \
  psql -U pantry -d postgres -v maintenance_password='本地安全输入的密码' \
  -f /scripts/provision-test-maintenance-role.sql
```

## 初始化维护账号

PostgreSQL 管理员在本机安全设置密码后，执行
[`scripts/provision-test-maintenance-role.sql`](../scripts/provision-test-maintenance-role.sql)。
脚本不包含真实密码，也不会修改开发库或 `pantrypilot_app` 权限。

账号的最小权限是：

- 仅能连接 `pantrypilot_test`、使用 `public` schema；
- 仅可对并发测试产生的 `users`、`inventory_items`、`recipes`、`meal_plans`、
  `meal_plan_items`、`meal_plan_ingredients` 执行定向 `SELECT`/`DELETE`；
- 对 `inventory_transactions` 只有 `SELECT`，没有 `INSERT`、`UPDATE`、`DELETE` 或
  `TRUNCATE`；
- 非超级用户、无建库/建角色权限、不属于 `pantrypilot_owner`。

维护账号的连接还必须在 `pg_hba.conf` 中限制为本机到 `pantrypilot_test` 的访问；修改后
由数据库管理员 reload PostgreSQL 配置。不要把维护账号密码、完整连接串或 `.env` 提交到 Git。
