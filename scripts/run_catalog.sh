#!/usr/bin/env bash
# Weekly job: make sure Postgres is up, then load the full SteamSpy catalogue.
# Takes over an hour. If it fails, rerunning resumes from the next page.
# Run by the systemd timer from install_schedule.sh, or by hand.
set -euo pipefail

cd "$(dirname "$0")/.."

scripts/start_db.sh

# block automatic suspend while the load runs: on the first run, requests
# timed out after the laptop woke up, and every failure costs a retry.
# Closing the lid still suspends, because logind ignores inhibitors for it
systemd-inhibit --what=sleep --who=steam-catalog \
    --why="Full Steam catalogue load in progress" \
    .venv/bin/python catalog.py
