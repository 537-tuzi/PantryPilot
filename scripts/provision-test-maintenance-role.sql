-- PantryPilot 测试库维护账号（须由 PostgreSQL 管理员在 psql 中执行）
--
-- 用法示例（不要把密码写入仓库或 shell 历史）：
--   psql -d postgres -v maintenance_password='本地安全输入的密码' \
--     -f scripts/provision-test-maintenance-role.sql
--
-- 本脚本只配置 pantrypilot_test 的维护账号，不改动 pantrypilot、
-- pantrypilot_app 或任何业务表结构。维护账号不是表所有者，也不属于
-- pantrypilot_owner；inventory_transactions 永远不给 UPDATE、DELETE 或 TRUNCATE。

\if :{?maintenance_password}
\else
  \echo 'maintenance_password is required; no changes were applied.'
  \quit
\endif

SELECT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'pantrypilot_test_maintenance'
) AS maintenance_role_exists \gset
\if :maintenance_role_exists
\else
  CREATE ROLE pantrypilot_test_maintenance
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
\endif

ALTER ROLE pantrypilot_test_maintenance PASSWORD :'maintenance_password';
SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pantrypilot_owner') AS owner_role_exists \gset
\if :owner_role_exists
  REVOKE pantrypilot_owner FROM pantrypilot_test_maintenance;
\endif
REVOKE ALL ON DATABASE pantrypilot_test FROM pantrypilot_test_maintenance;
GRANT CONNECT ON DATABASE pantrypilot_test TO pantrypilot_test_maintenance;

\connect pantrypilot_test

REVOKE ALL ON SCHEMA public FROM pantrypilot_test_maintenance;
GRANT USAGE ON SCHEMA public TO pantrypilot_test_maintenance;

-- 并发测试的定向清理只需要以下表的 SELECT/DELETE。
-- 该列表故意不包含 ingredient_catalog、shopping_items、user_preferences 等无关表。
GRANT SELECT, DELETE ON TABLE
  users,
  inventory_items,
  recipes,
  meal_plans,
  meal_plan_items,
  meal_plan_ingredients
TO pantrypilot_test_maintenance;

-- 维护账号只能读取流水，以便确认定向清理不会违反追加式审计约束。
REVOKE ALL ON TABLE inventory_transactions FROM pantrypilot_test_maintenance;
GRANT SELECT ON TABLE inventory_transactions TO pantrypilot_test_maintenance;

-- 防止未来为该角色授予整个 schema 的默认权限。
\if :owner_role_exists
  ALTER DEFAULT PRIVILEGES FOR ROLE pantrypilot_owner IN SCHEMA public
    REVOKE ALL ON TABLES FROM pantrypilot_test_maintenance;
\endif
