# 测试数据库与维护账号

自动化测试只能写入独立的 `pantrypilot_test` 数据库；不得将
`TEST_DATABASE_URL` 指向开发库 `pantrypilot`。测试前由迁移账号或表所有者
对测试库执行 `alembic upgrade head`，再运行 `pytest`；应用账号不负责迁移。

少数真实提交并发测试需要在测试结束后定向清理自己创建的记录。它们只能通过独立的
`pantrypilot_test_maintenance` 账号使用 `TEST_MAINTENANCE_DATABASE_URL` 完成，绝不
回退到 `pantrypilot_app`。未配置该变量时，这两项测试会明确跳过，而不会使用应用账号
删除任何流水。

## 初始化维护账号

PostgreSQL 管理员执行脚本后，用 `\password` 交互设置密码（不写进 shell 历史）：

```sql
\i scripts/provision-test-maintenance-role.sql
\password pantrypilot_test_maintenance
```

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

## 应用账号与权限回归

生产库与测试库都可以用同一份模板初始化应用账号：

```sql
psql -d postgres -v dbname=pantrypilot -f scripts/provision-app-role.sql
\password pantrypilot_app
```

应用账号对业务表可读写，但对 `inventory_transactions` 只有 `SELECT`/`INSERT`，
没有 `UPDATE`、`DELETE`、`TRUNCATE`，也不具备 schema 的 `CREATE` 权限。

把应用账号连接串写入 `TEST_APP_DATABASE_URL` 后，`tests/api/test_db_privileges.py`
会验证上述限制；未配置时该用例会跳过，不会回退到所有者账号。
