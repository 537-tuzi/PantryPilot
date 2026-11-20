#!/usr/bin/env bash
# 本地环境初始化：创建虚拟环境、安装依赖、准备 .env、启动数据库。
# 用法：bash scripts/bootstrap.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> 准备环境变量"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "已生成 .env，请按需填写 SECRET_KEY / LLM_API_KEY 等（.env 不会被提交）"
else
  echo ".env 已存在，跳过"
fi

echo "==> 初始化后端虚拟环境"
cd "$ROOT_DIR/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "==> 安装开发依赖"
pip install -e ".[dev]"

echo "==> 启动数据库"
cd "$ROOT_DIR"
docker compose -f deploy/docker-compose.yml up -d db

echo "==> 执行数据库迁移"
docker compose -f deploy/docker-compose.yml run --rm backend alembic upgrade head

cat <<'EOF'

初始化完成。
  后端：cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
  前端：cd frontend && npm install && npm run dev
  全部：docker compose -f deploy/docker-compose.yml up -d --build
EOF
