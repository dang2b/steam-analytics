#!/usr/bin/env bash
# Restore a backup made by backup_db.sh, then rebuild the dbt models.
# Replaces the raw tables and the history snapshot with the backup's contents.
# Usage: scripts/restore_db.sh <backup.dump> [--yes]
set -euo pipefail

cd "$(dirname "$0")/.."

dump="${1:?usage: scripts/restore_db.sh <backup.dump> [--yes]}"
[ -f "$dump" ] || { echo "no such file: $dump" >&2; exit 1; }

set -a
source .env
set +a

if [ "${2:-}" != "--yes" ]; then
    echo "This replaces the raw tables and the history snapshot in $DB_NAME"
    echo "with the contents of $dump."
    read -r -p "Continue? [y/N] " answer
    [ "$answer" = "y" ] || { echo "cancelled"; exit 1; }
fi

scripts/start_db.sh

# --clean drops each object before recreating it, so the result matches the
# backup rather than a mix of the backup and the current data
docker compose exec -T db pg_restore -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --no-owner < "$dump"
echo "restored $dump"

cd steam_analytics
../.venv/bin/dbt build
