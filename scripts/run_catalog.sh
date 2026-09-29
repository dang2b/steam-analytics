#!/usr/bin/env bash
# Weekly job: make sure Postgres is up, then load the full SteamSpy catalogue.
# Takes over an hour. If it fails, rerunning resumes from the next page.
# Run by the systemd timer from install_schedule.sh, or by hand.
set -euo pipefail

cd "$(dirname "$0")/.."

scripts/start_db.sh
.venv/bin/python catalog.py
