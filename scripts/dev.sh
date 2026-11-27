#!/usr/bin/env bash
# PantryPilot 统一开发入口：所有后端操作都在容器内完成。
#
# 为什么统一到容器：
#   后端基线是 Python 3.11+（代码使用 datetime.UTC），而 Ubuntu 22.04 自带 3.10，
#   jammy 只有 3.11.0rc1（不适合作为开发基线）。因此**容器是唯一受支持的后端运行环境**，
#   宿主机 Python 版本不再是任何人的阻塞项；本地 venv 仅用于 IDE 提示，可选。
#
# 用法：bash scripts/dev.sh <命令>
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="deploy/docker-compose.yml"
PG_USER="${POSTGRES_USER:-pantry}"
PG_DB="${POSTGRES_DB:-pantrypilot}"
TEST_DB="${POSTGRES_TEST_DB:-pantrypilot_test}"

info() { printf '\033[0;36m==>\033[0m %s\n' "$1"; }
ok()   { printf '\033[0;32m[OK]\033[0m %s\n' "$1"; }
warn() { printf '\033[0;33m[!]\033[0m %s\n' "$1"; }
die()  { printf '\033[0;31m[x]\033[0m %s\n' "$1" >&2; exit 1; }

dc() { docker compose -f "$COMPOSE_FILE" "$@"; }
dc_test() { docker compose -f "$COMPOSE_FILE" --profile test "$@"; }

require_docker() {
  command -v docker >/dev/null 2>&1 || die "未安装 docker。安装：sudo bash scripts/install_docker.sh"
  docker info >/dev/null 2>&1 || die "无权访问 docker daemon。执行 newgrp docker 或注销后重新登录"
}

load_env() {
  [ -f .env ] || die "根目录缺少 .env。执行：cp .env.example .env 并填写 SECRET_KEY"
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
}

# 从 .env 的 TEST_MAINTENANCE_DATABASE_URL 中取出维护账号密码
maintenance_password() {
  local url pw
  url="$(grep -E '^TEST_MAINTENANCE_DATABASE_URL=' .env 2>/dev/null | cut -d= -f2- || true)"
  [ -n "$url" ] || return 1
  pw="$(printf '%s' "$url" | sed -E 's|^[a-z+]+://[^:]*:([^@]*)@.*$|\1|')"
  [ -n "$pw" ] || return 1
  printf '%s' "$pw"
}

# 生成容器内可用的维护账号连接串（把宿主机名改写为 compose 服务名 db）
maintenance_url_in_container() {
  local url
  url="$(grep -E '^TEST_MAINTENANCE_DATABASE_URL=' .env 2>/dev/null | cut -d= -f2- || true)"
  [ -n "$url" ] || return 1
  printf '%s' "$url" | sed -E "s|^(postgresql(\+psycopg)?://[^@]*)@[^/]+/|\1@db:5432/|"
}

cmd_up() {
  require_docker
  load_env
  info "构建镜像并启动服务（db / backend / frontend）"
  dc up -d --build
  info "等待数据库就绪"
  for _ in $(seq 1 30); do
    if dc exec -T db pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  cmd_migrate
  ok "服务已就绪：http://localhost/  （后端 http://localhost:8000）"
}

cmd_down() {
  require_docker
  if [ "${1:-}" = "--volumes" ]; then
    info "停止服务并删除数据卷（数据库数据会丢失）"
    dc down -v
  else
    info "停止服务（保留数据卷）"
    dc down
  fi
}

cmd_migrate() {
  require_docker
  load_env
  info "对开发库执行数据库迁移"
  dc exec -T backend alembic upgrade head
  ok "开发库迁移完成"
}

cmd_test_db() {
  require_docker
  load_env
  info "准备测试库 $TEST_DB"
  if ! dc exec -T db psql -U "$PG_USER" -d postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname='$TEST_DB'" | grep -q 1; then
    dc exec -T db psql -U "$PG_USER" -d postgres -c "CREATE DATABASE $TEST_DB"
    ok "测试库已创建"
  else
    ok "测试库已存在"
  fi

  # 迁移必须先于授权：授权脚本按表级权限 GRANT，业务表必须先存在，
  # 否则会报 relation "users" does not exist 并导致并发测试因权限不足而失败。
  # 顺序说明见 docs/test-database-setup.md §一。
  info "对测试库执行数据库迁移"
  dc_test run --rm -T backend-test alembic upgrade head
  ok "测试库迁移完成"

  if pw="$(maintenance_password)"; then
    info "配置测试维护账号（迁移之后授权）"
    # ON_ERROR_STOP=1：授权失败必须让脚本以非零码退出，不能静默成功。
    dc exec -T db psql -U "$PG_USER" -d postgres -v ON_ERROR_STOP=1 \
      -v maintenance_password="$pw" \
      -f /scripts/provision-test-maintenance-role.sql >/dev/null
    ok "维护账号已配置"
  else
    warn "未在 .env 填写 TEST_MAINTENANCE_DATABASE_URL，跳过维护账号配置"
    warn "（相关并发测试会自动跳过，不影响其他用例）"
  fi
}

cmd_test() {
  require_docker
  load_env
  cmd_test_db
  info "在容器内执行 pytest"
  local extra_env=()
  if url="$(maintenance_url_in_container)"; then
    extra_env=(-e "TEST_MAINTENANCE_DATABASE_URL=$url")
  fi
  dc_test run --rm -T ${extra_env[@]+"${extra_env[@]}"} backend-test
}

cmd_seed() {
  require_docker
  load_env
  info "写入演示种子数据"
  dc exec -T backend python scripts/seed.py
}

cmd_backup() {
  require_docker
  mkdir -p backups
  local stamp file tmp
  stamp="$(date +%Y%m%d-%H%M%S)"
  file="backups/pantrypilot-$stamp.sql"
  # 先写临时文件：pg_dump 失败时不要留下 0 字节的"备份"，
  # 否则它会被后续 restore 当成有效备份，把数据库清成空库。
  tmp="$file.partial"
  rm -f "$tmp"
  if ! dc exec -T db pg_dump -U "$PG_USER" "$PG_DB" > "$tmp"; then
    rm -f "$tmp"
    die "备份失败（pg_dump 报错），未生成备份文件"
  fi
  if [ ! -s "$tmp" ]; then
    rm -f "$tmp"
    die "备份失败：生成的文件为空，未保留任何备份"
  fi
  mv "$tmp" "$file"
  ok "备份完成：$file（恢复前请先在隔离环境验证）"
}

cmd_restore() {
  require_docker
  local file="${1:-}"
  [ -n "$file" ] && [ -f "$file" ] || die "用法：bash scripts/dev.sh restore <备份文件>"
  # 恢复会先清空 public schema。备份文件不可用时必须拒绝执行，
  # 否则会把数据库清成空库并报告"恢复完成"。
  [ -s "$file" ] || die "备份文件为空：$file（恢复会清空数据库，已拒绝执行）"
  grep -q "CREATE TABLE" "$file" \
    || die "备份文件内容不像 pg_dump 输出：$file（恢复会清空数据库，已拒绝执行）"
  printf '将覆盖数据库 %s（会先清空 public schema），继续？[y/N] ' "$PG_DB"
  read -r answer
  [ "$answer" = "y" ] || { echo "已取消"; exit 0; }
  dc exec -T db psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d "$PG_DB" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null
  dc exec -T db psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d "$PG_DB" < "$file"
  ok "恢复完成，请验证：curl http://localhost/api/v1/health 与一次真实查询（/health 不查库，库被清空也照样返回 ok）"
}

cmd_check() {
  # 必须用 "$@"：写成 "${@:-}" 会在无参数时传入一个空字符串，
  # check_env.sh 会把它当成未知参数并以退出码 2 结束，自检根本不会跑。
  bash "$ROOT_DIR/scripts/check_env.sh" "$@"
}

cmd_shell() {
  require_docker
  dc exec backend bash
}

cmd_logs() {
  require_docker
  if [ -n "${1:-}" ]; then dc logs -f "$1"; else dc logs -f --tail 100; fi
}

cmd_openapi() {
  cat <<'EOF'
接口地址：
  Swagger UI   http://localhost/docs
  OpenAPI JSON http://localhost/openapi.json
  健康检查     http://localhost/health  与  http://localhost:8000/health
EOF
}

usage() {
  cat <<'EOF'
用法：bash scripts/dev.sh <命令>

  up [--build]     构建镜像并启动 db/backend/frontend，并迁移开发库
  down [--volumes] 停止服务（--volumes 会删除数据库数据）
  restart          重启服务
  ps               查看服务状态
  logs [服务名]    查看日志（默认全部）
  migrate          对开发库执行 alembic upgrade head
  test-db          准备测试库：建库 → 授权维护账号 → 迁移（顺序固定）
  test             准备测试库并在容器内跑 pytest
  seed             写入演示种子数据
  backup           备份开发库到 backups/
  restore <文件>   从备份恢复开发库
  check [--fast]   环境自检
  shell            进入后端容器
  openapi          打印接口地址
EOF
}

case "${1:-help}" in
  up) shift; cmd_up "$@" ;;
  down) shift; cmd_down "$@" ;;
  restart) require_docker; dc restart ;;
  ps) require_docker; dc ps ;;
  logs) shift; cmd_logs "$@" ;;
  migrate) shift; cmd_migrate "$@" ;;
  test-db) shift; cmd_test_db "$@" ;;
  test) shift; cmd_test "$@" ;;
  seed) shift; cmd_seed "$@" ;;
  backup) shift; cmd_backup "$@" ;;
  restore) shift; cmd_restore "$@" ;;
  check) shift; cmd_check "$@" ;;
  shell) shift; cmd_shell "$@" ;;
  openapi) cmd_openapi ;;
  help|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
