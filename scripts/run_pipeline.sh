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

# build even if the load partly failed, so games already loaded still get
# snapshotted that day; rerunning on unchanged data is harmless. The job
# still exits non-zero afterwards so the failure shows in systemctl
status=0
.venv/bin/python main.py || status=$?

cd steam_analytics
../.venv/bin/dbt build

exit "$status"
