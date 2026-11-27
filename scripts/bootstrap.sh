#!/usr/bin/env bash
# 一键初始化开发环境。
#
# 统一原则：后端基线是 Python 3.11+，而 Ubuntu 22.04 只有 3.10（jammy 仅提供 3.11.0rc1），
# 因此**容器是唯一受支持的后端运行环境**。本脚本优先走容器路径；
# 只有在 Docker 不可用且宿主机 Python ≥ 3.11 时，才退回宿主机 venv 方式。
#
# 用法：bash scripts/bootstrap.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

info() { printf '\033[0;36m==>\033[0m %s\n' "$1"; }
ok()   { printf '\033[0;32m[OK]\033[0m %s\n' "$1"; }
warn() { printf '\033[0;33m[!]\033[0m %s\n' "$1"; }
die()  { printf '\033[0;31m[x]\033[0m %s\n' "$1" >&2; exit 1; }

info "检查环境变量"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    已生成 .env，请务必修改 SECRET_KEY（默认占位符会导致服务拒绝启动）"
  python3 - <<'EOF' 2>/dev/null || true
import secrets
from pathlib import Path
p = Path(".env")
s = p.read_text()
s = s.replace("SECRET_KEY=change-me-to-a-long-random-string",
              f"SECRET_KEY={secrets.token_urlsafe(48)}")
p.write_text(s)
EOF
  # 必须回读校验：上面的 python 失败会被 `|| true` 吞掉，
  # 而后端在 SECRET_KEY 仍是占位符时会拒绝启动，错误点离失败点很远。
  if grep -q "^SECRET_KEY=change-me-to-a-long-random-string$" .env; then
    die "未能写入随机 SECRET_KEY（.env 中仍是占位符）。请手动执行："
    die "  sed -i \"s|^SECRET_KEY=.*|SECRET_KEY=\$(openssl rand -hex 32)|\" .env"
  fi
  ok "已生成 .env 并写入随机 SECRET_KEY"
else
  echo "    .env 已存在"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  info "容器模式：构建镜像、启动服务、迁移开发库与测试库"
  bash "$ROOT_DIR/scripts/dev.sh" up
  bash "$ROOT_DIR/scripts/dev.sh" test-db
  ok "容器环境就绪"
  cat <<'EOF'

下一步：
  开发：bash scripts/dev.sh up        启动服务（后端 http://localhost:8000，前端 http://localhost）
        bash scripts/dev.sh test      在容器内跑全部后端测试
        bash scripts/dev.sh logs      看日志
  前端热更新（可选）：cd frontend && npm install && npm run dev   # http://localhost:5200
  自检：bash scripts/check_env.sh
EOF
  exit 0
fi

warn "Docker 不可用（未安装或无权限）。安装：sudo bash scripts/install_docker.sh，之后 newgrp docker"
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)' 2>/dev/null; then
  die "宿主机 Python 低于 3.11 且无 Docker，后端无法运行。请安装 Docker 或 Python 3.11+"
fi

info "宿主机模式：创建虚拟环境并安装依赖"
cd "$ROOT_DIR/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt -r requirements-dev.txt
ok "依赖安装完成"
cd "$ROOT_DIR"

info "初始化前端依赖"
cd "$ROOT_DIR/frontend"
npm install --no-audit --no-fund
ok "前端依赖安装完成"

cat <<'EOF'

宿主机模式就绪。
  后端：cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
  前端：cd frontend && npm run dev            # http://localhost:5200
  测试：cd backend && python -m pytest        # 需要先配置 TEST_DATABASE_URL 并迁移测试库
  自检：bash scripts/check_env.sh
EOF
