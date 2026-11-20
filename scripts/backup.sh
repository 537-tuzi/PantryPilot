#!/usr/bin/env bash
# 备份数据库。备份文件存储在受控位置，不提交公开仓库（文档/08 §4）。
# 用法：bash scripts/backup.sh [输出目录]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="${1:-$ROOT_DIR/backups}"
mkdir -p "$OUT_DIR"

POSTGRES_USER="${POSTGRES_USER:-pantry}"
POSTGRES_DB="${POSTGRES_DB:-pantrypilot}"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$OUT_DIR/pantrypilot-$STAMP.sql"

docker compose -f deploy/docker-compose.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$OUT_FILE"

echo "备份完成：$OUT_FILE"
echo "提醒：恢复前必须先在隔离环境验证该备份文件。"
