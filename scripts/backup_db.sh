#!/usr/bin/env bash
# Back up the data that can't be rebuilt: the raw tables and the history
# snapshot. The APIs don't serve past data, so a lost snapshot is lost for
# good. Staging and marts are left out: dbt build recreates them.
# Run by run_pipeline.sh after each daily build, or by hand.
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
source .env
set +a

BACKUP_DIR="${BACKUP_DIR:-$HOME/steam-pipeline-backups}"
KEEP="${BACKUP_KEEP:-14}"
mkdir -p "$BACKUP_DIR"

name="steam_pipeline_$(date +%Y-%m-%d_%H%M%S).dump"
tmp="$BACKUP_DIR/.$name.partial"
trap 'rm -f "$tmp"' EXIT

# pg_dump runs inside the container, so its version always matches the server
docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --format=custom --schema=public --schema=public_snapshots > "$tmp"

# check the dump is readable before it counts as a backup, then rename it
# in one step, so a half-written file never looks like a valid backup
docker compose exec -T db pg_restore --list < "$tmp" > /dev/null
mv "$tmp" "$BACKUP_DIR/$name"
echo "backup written: $BACKUP_DIR/$name ($(du -h "$BACKUP_DIR/$name" | cut -f1))"

# names sort by date, so everything before the newest $KEEP is older.
# Counted by hand because `head -n -N` only works with GNU head, not macOS
backups=$(find "$BACKUP_DIR" -maxdepth 1 -name 'steam_pipeline_*.dump' | sort)
count=$(printf '%s\n' "$backups" | grep -c . || true)
if [ "$count" -gt "$KEEP" ]; then
    printf '%s\n' "$backups" | head -n "$((count - KEEP))" \
        | while read -r old; do rm -- "$old" && echo "removed old backup: $old"; done
fi
