#!/usr/bin/env bash
# Daily job: make sure Postgres is up, load fresh data, rebuild dbt models,
# back up the raw tables and history.
# Run by the systemd timer from install_schedule.sh, or by hand.
set -euo pipefail

cd "$(dirname "$0")/.."

# dbt reads credentials from the environment, not from .env
set -a
source .env
set +a

scripts/start_db.sh

# build even if the load partly failed, so games already loaded still get
# snapshotted that day; rerunning on unchanged data is harmless. The job
# still exits non-zero afterwards so the failure shows in systemctl
status=0
.venv/bin/python main.py || status=$?

(cd steam_analytics && ../.venv/bin/dbt build)

# after the build, so the backup includes today's snapshot
scripts/backup_db.sh

exit "$status"
