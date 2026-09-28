#!/usr/bin/env bash
# Daily job: make sure Postgres is up, load fresh data, rebuild dbt models.
# Run by the systemd timer from install_schedule.sh, or by hand.
set -euo pipefail

cd "$(dirname "$0")/.."

# dbt reads credentials from the environment, not from .env
set -a
source .env
set +a

# containers have no restart policy, so after a reboot the database is down
docker compose up -d db
for _ in $(seq 1 30); do
    docker compose exec -T db pg_isready -q && break
    sleep 2
done
docker compose exec -T db pg_isready -q || { echo "postgres did not become ready" >&2; exit 1; }

.venv/bin/python main.py

cd steam_analytics
../.venv/bin/dbt build
