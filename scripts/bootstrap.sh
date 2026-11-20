#!/usr/bin/env bash
# 本地环境初始化：创建虚拟环境、安装依赖、准备 .env、启动数据库并迁移。
# 用法：bash scripts/bootstrap.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

info() { printf '\033[0;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[0;33m[!]\033[0m %s\n' "$1"; }
die()  { printf '\033[0;31m[x]\033[0m %s\n' "$1" >&2; exit 1; }

info "检查 Python 与 venv 可用性"
command -v python3 >/dev/null || die "未找到 python3"
python3 -c 'import sys; print("    Python", sys.version.split()[0])'
if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
  warn "当前 Python 缺少 ensurepip，python3 -m venv 会失败"
  warn "请先安装：sudo apt install python3-venv  （Debian/Ubuntu）"
  warn "或改用系统包：sudo apt install python3-pip python3-venv"
  die "缺少 venv 组件，已停止"
fi

info "准备环境变量"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    已生成 .env，请按需填写 SECRET_KEY / LLM_API_KEY 等（.env 不会被提交）"
else
  echo "    .env 已存在，跳过"
fi

info "初始化后端虚拟环境"
cd "$ROOT_DIR/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
# 开发工具直接安装，避免可编辑安装在不同 setuptools 版本下解析元数据失败
pip install "pytest>=8.0" "pytest-cov>=5.0" "ruff>=0.5" "mypy>=1.10"

info "初始化前端依赖"
cd "$ROOT_DIR/frontend"
npm install --no-audit --no-fund

info "启动数据库并执行迁移"
cd "$ROOT_DIR"
if command -v docker >/dev/null 2>&1; then
  docker compose -f deploy/docker-compose.yml up -d db
  docker compose -f deploy/docker-compose.yml run --rm backend alembic upgrade head
else
  warn "未检测到 docker，跳过数据库启动"
  warn "本机可自行准备 PostgreSQL 后执行：cd backend && alembic upgrade head"
fi

info "环境自检"
bash "$ROOT_DIR/scripts/check_env.sh" || true

cat <<'EOF'

初始化完成。
  后端：cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
  前端：cd frontend && npm run dev            # http://localhost:5200
  全部：docker compose -f deploy/docker-compose.yml up -d --build
  自检：bash scripts/check_env.sh
EOF
