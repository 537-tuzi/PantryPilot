-- PantryPilot 应用账号（pantrypilot_app）最小权限模板。
--
-- 用法（由 PostgreSQL 管理员执行；密码请随后用 \password 交互设置）：
--   psql -d postgres -v dbname=pantrypilot -f scripts/provision-app-role.sql
--   psql -d postgres -v dbname=pantrypilot_test -f scripts/provision-app-role.sql
--
-- 说明：
--   * 不授予 SUPERUSER / CREATEDB / CREATEROLE，也不把角色加入 pantrypilot_owner；
--   * 业务表可读写，但 inventory_transactions 只允许 SELECT / INSERT；
--   * 不授予 TRUNCATE，也不授予 schema 的 CREATE 权限；
--   * 迁移（alembic upgrade head）必须由表所有者或迁移账号执行，不能用本账号。

\if :{?dbname}
\else
  \set dbname pantrypilot
\endif

SELECT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'pantrypilot_owner'
) AS owner_role_exists \gset
\if :owner_role_exists
\else
  CREATE ROLE pantrypilot_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOINHERIT NOREPLICATION NOBYPASSRLS;
\endif

SELECT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'pantrypilot_app'
) AS app_role_exists \gset
\if :app_role_exists
\else
  CREATE ROLE pantrypilot_app
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
\endif

-- 不把应用账号加入所有者角色，避免通过角色成员关系绕过表级权限。
REVOKE pantrypilot_owner FROM pantrypilot_app;
REVOKE ALL ON DATABASE :"dbname" FROM pantrypilot_app;
GRANT CONNECT ON DATABASE :"dbname" TO pantrypilot_app;

\connect :dbname

REVOKE ALL ON SCHEMA public FROM pantrypilot_app;
GRANT USAGE ON SCHEMA public TO pantrypilot_app;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM pantrypilot_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pantrypilot_app;

-- 追加式审计表：只读 + 只追加，显式收回修改与清空权限。
REVOKE ALL ON TABLE inventory_transactions FROM pantrypilot_app;
GRANT SELECT, INSERT ON TABLE inventory_transactions TO pantrypilot_app;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pantrypilot_app;

-- 未来由 owner 新建的表默认给应用账号 DML；新增审计表时仍需单独收回
-- UPDATE / DELETE / TRUNCATE。
ALTER DEFAULT PRIVILEGES FOR ROLE pantrypilot_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pantrypilot_app;
ALTER DEFAULT PRIVILEGES FOR ROLE pantrypilot_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO pantrypilot_app;

\echo '应用账号权限已配置。请执行下面命令为 pantrypilot_app 设置密码（交互输入，不出现在 shell 历史）：'
\echo '  \password pantrypilot_app'
