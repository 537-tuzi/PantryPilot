# 测试数据库与维护账号

自动化测试只能写入独立的 `pantrypilot_test` 数据库；不得将
`TEST_DATABASE_URL` 指向开发库 `pantrypilot`。测试前先使用应用账号对测试库执行
`alembic upgrade head`，再运行 `pytest`。

少数真实提交并发测试需要在测试结束后定向清理自己创建的记录。它们只能通过独立的
`pantrypilot_test_maintenance` 账号使用 `TEST_MAINTENANCE_DATABASE_URL` 完成，绝不
回退到 `pantrypilot_app`。未配置该变量时，这两项测试会明确跳过，而不会使用应用账号
删除任何流水。

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
