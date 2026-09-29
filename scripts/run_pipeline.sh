#!/usr/bin/env bash
# Daily job: make sure Postgres is up, load fresh data, rebuild dbt models,
# back up the raw tables and history, check source freshness, and report
# dbt warnings.
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

target=steam_analytics/target

# each later step runs even if an earlier one failed (a failing test, say),
# so the day still gets backed up and its warnings reported; the job still
# exits non-zero at the end. Result files are removed first, so a step that
# crashes can't leave yesterday's file to be reported as today's
rm -f "$target/run_results.json" "$target/sources.json"

(cd steam_analytics && ../.venv/bin/dbt build) || status=$?

# after the build, so the backup includes today's snapshot
scripts/backup_db.sh || status=$?

# fails the job when a source hasn't loaded for a week, warns after a day.
# It writes sources.json and leaves the build's run_results.json alone
(cd steam_analytics && ../.venv/bin/dbt source freshness) || status=$?

# warnings leave the exit code at 0, so systemd would never report them
.venv/bin/python dbt_warnings.py "$target/run_results.json" "$target/sources.json" \
    || status=$?

exit "$status"
