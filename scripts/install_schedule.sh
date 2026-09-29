#!/usr/bin/env bash
# Install a systemd user timer that runs run_pipeline.sh daily.
# Undo with: systemctl --user disable --now steam-pipeline.timer
# Needs notify-send (libnotify) for failure notifications.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/steam-pipeline.service" <<UNIT
[Unit]
Description=Steam analytics pipeline (extract, load, dbt build)
OnFailure=steam-pipeline-failure.service

[Service]
Type=oneshot
ExecStart=$REPO/scripts/run_pipeline.sh
TimeoutStartSec=15min
UNIT

# desktop notification when a run fails, so it isn't only in the journal
cat > "$UNIT_DIR/steam-pipeline-failure.service" <<UNIT
[Unit]
Description=Notify that the Steam analytics pipeline failed

[Service]
Type=oneshot
ExecStart=/usr/bin/notify-send --urgency=critical "Steam pipeline failed" "journalctl --user -u steam-pipeline.service"
UNIT

cat > "$UNIT_DIR/steam-pipeline.timer" <<UNIT
[Unit]
Description=Run the Steam analytics pipeline daily

[Timer]
OnCalendar=*-*-* 09:00
# if the machine was off at 09:00, run at the next boot instead of skipping
Persistent=true
RandomizedDelaySec=10min

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now steam-pipeline.timer
systemctl --user list-timers steam-pipeline.timer
