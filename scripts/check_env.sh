#!/usr/bin/env bash
# 环境自检：逐项检查本地配置是否正确可用。
# 用法：bash scripts/check_env.sh [--fast]
#   --fast 跳过前端 lint/类型检查/测试（约 15 秒），适合日常快速确认
# 退出码：0 = 全部通过；1 = 存在 FAIL 项
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FAST=0
for arg in "$@"; do
  case "$arg" in
    --fast) FAST=1 ;;
    -h|--help)
      echo "用法：bash scripts/check_env.sh [--fast]"
      echo "  --fast   跳过前端 lint/类型检查/测试"
      exit 0 ;;
    *) echo "未知参数：$arg（用 --help 查看用法）" >&2; exit 2 ;;
  esac
done

PASS=0; WARN=0; FAIL=0
ok()   { printf '  \033[0;32m[OK]\033[0m   %s\n' "$1"; PASS=$((PASS+1)); }
warn() { printf '  \033[0;33m[WARN]\033[0m %s\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  \033[0;31m[FAIL]\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
head() { printf '\n\033[1m%s\033[0m\n' "$1"; }

head "1. 工具链"
command -v python3 >/dev/null && ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)" || warn "未安装 python3（容器模式下非必需）"
PYVER=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo 0.0)
HAS_DOCKER=0
command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1 && HAS_DOCKER=1
if python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)' 2>/dev/null; then
  ok "宿主机 Python $PYVER 满足 3.11+（可在宿主机直接跑后端）"
elif [ "$HAS_DOCKER" -eq 1 ]; then
  warn "宿主机 Python $PYVER < 3.11，但容器可用 —— 后端请用容器跑：bash scripts/dev.sh up"
else
  bad "宿主机 Python $PYVER < 3.11 且无 Docker：后端无法运行（需 Python 3.11+ 或 Docker）"
fi
command -v node >/dev/null && ok "node $(node -v)" || bad "未安装 node（需要 20+）"
command -v npm >/dev/null && ok "npm $(npm -v)" || bad "未安装 npm"
if [ "$HAS_DOCKER" -eq 1 ]; then
  ok "docker $(docker -v 2>/dev/null | cut -d' ' -f3 | tr -d ',') 可用"
  if docker compose -f deploy/docker-compose.yml config >/dev/null 2>&1; then
    ok "compose 配置有效"
  else
    bad "compose 配置无效：docker compose -f deploy/docker-compose.yml config"
  fi
else
  warn "Docker 不可用（未安装或无权限）：执行 sudo bash scripts/install_docker.sh 后 newgrp docker"
fi

head "2. Git 状态"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
if [ "$BRANCH" = "main" ]; then
  bad "当前在 main 分支，请切到自己的开发分支：git switch dev/<你的名字>"
elif [[ "$BRANCH" == dev/* ]]; then
  ok "当前分支 $BRANCH"
else
  warn "当前分支 $BRANCH，不符合 dev/* 约定"
fi
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
[ -n "$UPSTREAM" ] && ok "已绑定上游 $UPSTREAM" || bad "未绑定上游：git branch --set-upstream-to=origin/$BRANCH"
if [ -n "$(git status --porcelain)" ]; then
  warn "工作区有未提交改动（提交后再推送）"
else
  ok "工作区干净"
fi
git fetch origin --quiet 2>/dev/null
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
if [ "$BEHIND" -gt 0 ]; then
  warn "落后 origin/main $BEHIND 个提交，请执行：git merge origin/main"
else
  ok "已包含 origin/main 的最新内容"
fi

head "3. 环境变量"
if [ -f .env ]; then
  ok ".env 存在"
  # shellcheck disable=SC1091
  set -a; . ./.env 2>/dev/null; set +a
  if [ -n "${SECRET_KEY:-}" ] && [ "$SECRET_KEY" != "change-me-to-a-long-random-string" ]; then
    ok "SECRET_KEY 已自定义"
  else
    warn "SECRET_KEY 仍为默认值，生成一个：python3 -c 'import secrets;print(secrets.token_urlsafe(48))'"
  fi
  if [ -n "${LLM_API_KEY:-}" ]; then ok "LLM_API_KEY 已配置（仅服务端）"
  else warn "LLM_API_KEY 为空：AI 功能不可用（可先用 Mock 跑通其余功能）"; fi
  if [ -n "${DATABASE_URL:-}" ]; then ok "DATABASE_URL 已配置"
  else bad "DATABASE_URL 未配置"; fi
else
  bad ".env 不存在，请执行：cp .env.example .env"
fi

head "4. 端口占用（5200 前端 / 8000 后端 / 5432 数据库）"
for port in 5200 8000 5432; do
  if command -v ss >/dev/null && ss -ltn 2>/dev/null | grep -q ":$port "; then
    warn "端口 $port 已被占用（若是你自己的服务可忽略）"
  else
    ok "端口 $port 可用"
  fi
done

head "5. 后端"
# 容器是唯一受支持的后端运行环境；宿主机 venv 仅用于 IDE 提示
if [ "$HAS_DOCKER" -eq 1 ]; then
  if docker compose -f deploy/docker-compose.yml ps --status running --services 2>/dev/null | grep -q backend; then
    ok "后端容器运行中"
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
      ok "后端健康检查通过（http://localhost:8000/health）"
    else
      warn "后端容器在跑但健康检查未通过，看日志：bash scripts/dev.sh logs backend"
    fi
  else
    warn "后端容器未启动：bash scripts/dev.sh up"
  fi
else
  warn "无 Docker，跳过容器侧检查"
fi

# 宿主机侧（仅当 Python 3.11+ 且有 venv 时才有意义）
if python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)' 2>/dev/null; then
  PY="python3"
  if [ -x "$ROOT_DIR/backend/.venv/bin/python" ]; then
    PY="$ROOT_DIR/backend/.venv/bin/python"
    ok "使用项目虚拟环境 backend/.venv"
  fi
  IMPORT_OUT="$(mktemp)"
  if (cd backend && "$PY" -c 'from app.main import app' >"$IMPORT_OUT" 2>&1); then
    ok "应用可正常导入（app.main）"
  elif grep -q "is not installed" "$IMPORT_OUT"; then
    warn "依赖缺失，执行：cd backend && pip install -r requirements.txt -r requirements-dev.txt"
  else
    warn "宿主机导入失败（不影响容器运行）：$(tail -1 "$IMPORT_OUT")"
  fi
  rm -f "$IMPORT_OUT"
else
  echo "  （宿主机 Python < 3.11，跳过宿主机侧检查——容器模式下不需要）"
fi

head "6. 前端"
if [ "$FAST" -eq 1 ]; then
  echo "  （--fast 模式，跳过前端 lint / 类型检查 / 测试）"
  [ -d frontend/node_modules ] && ok "node_modules 已安装" || warn "依赖未安装，执行：cd frontend && npm install"
else
  if [ -d frontend/node_modules ]; then ok "node_modules 已安装"
  else warn "依赖未安装，执行：cd frontend && npm install"; fi
  if (cd frontend && npm run lint --silent >/dev/null 2>&1); then ok "ESLint 通过"
  else warn "ESLint 未通过，执行：cd frontend && npm run lint"; fi
  if (cd frontend && npm run typecheck --silent >/dev/null 2>&1); then ok "类型检查通过"
  else warn "类型检查未通过，执行：cd frontend && npm run typecheck"; fi
  if (cd frontend && npm run test --silent >/dev/null 2>&1); then ok "前端测试通过"
  else warn "前端测试未通过，执行：cd frontend && npm run test"; fi
fi

head "7. 容器"
if [ "$HAS_DOCKER" -eq 1 ]; then
  docker compose -f deploy/docker-compose.yml ps --format '    {{.Service}}: {{.State}}' 2>/dev/null \
    || echo "    （未启动 compose 服务，执行：bash scripts/dev.sh up）"
else
  warn "Docker 不可用，容器侧检查已跳过"
fi

printf '\n\033[1m结果：PASS %d / WARN %d / FAIL %d\033[0m\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "存在 FAIL 项，请先修复再提交代码。"
  exit 1
fi
echo "环境自检通过。"
