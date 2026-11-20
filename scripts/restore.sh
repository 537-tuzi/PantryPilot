#!/usr/bin/env bash
# 从备份文件恢复数据库。务必先在隔离环境验证备份可用（文档/08 §4）。
# 用法：bash scripts/restore.sh backups/pantrypilot-YYYYmmdd-HHMMSS.sql
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "用法：bash scripts/restore.sh <备份文件路径>" >&2
  exit 1
fi

POSTGRES_USER="${POSTGRES_USER:-pantry}"
POSTGRES_DB="${POSTGRES_DB:-pantrypilot}"

echo "将使用 $BACKUP_FILE 覆盖数据库 $POSTGRES_DB，继续？[y/N]"
read -r answer
if [ "$answer" != "y" ]; then
  echo "已取消"
  exit 0
fi

docker compose -f deploy/docker-compose.yml exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$BACKUP_FILE"

echo "恢复完成，请执行一次冒烟验证：curl http://localhost/health"
