#!/usr/bin/env bash
# Start Postgres if it's down and wait until it accepts connections.
# Shared by the daily and weekly jobs.
set -euo pipefail

cd "$(dirname "$0")/.."

# containers have no restart policy, so after a reboot the database is down
docker compose up -d db
for _ in $(seq 1 30); do
    docker compose exec -T db pg_isready -q && exit 0
    sleep 2
done
echo "postgres did not become ready" >&2
exit 1
