#!/usr/bin/env bash
# Install systemd user timers: the pipeline daily, the full catalogue weekly.
# Undo with:
#   systemctl --user disable --now steam-pipeline.timer steam-catalog.timer
# Needs notify-send (libnotify) for failure notifications, and systemd 254+
# for RestartMode (older versions notify on every retry, not just the last).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$UNIT_DIR"

# replaced by the steam-notify-failure@ template below
rm -f "$UNIT_DIR/steam-pipeline-failure.service"

# desktop notification when a job fails, so it isn't only in the journal.
# A template: %i is the unit that failed
cat > "$UNIT_DIR/steam-notify-failure@.service" <<UNIT
[Unit]
Description=Notify that %i failed

[Service]
Type=oneshot
ExecStart=/usr/bin/notify-send --urgency=critical "%i failed" "journalctl --user -u %i"
UNIT

cat > "$UNIT_DIR/steam-pipeline.service" <<UNIT
[Unit]
Description=Steam analytics pipeline (extract, load, dbt build)
OnFailure=steam-notify-failure@%n.service

[Service]
Type=oneshot
ExecStart=$REPO/scripts/run_pipeline.sh
TimeoutStartSec=15min
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

cat > "$UNIT_DIR/steam-catalog.service" <<UNIT
[Unit]
Description=Steam full catalogue load (about 1.5 hours, resumable)
OnFailure=steam-notify-failure@%n.service
# at most 3 attempts per run
StartLimitIntervalSec=12h
StartLimitBurst=3

[Service]
Type=oneshot
ExecStart=$REPO/scripts/run_catalog.sh
TimeoutStartSec=4h
# a dropped connection or a sleeping laptop shouldn't cost the week's load:
# retry later, and catalog.py resumes from the next page. RestartMode=direct
# skips OnFailure between attempts, so the notification only comes once
# all three have failed
Restart=on-failure
RestartMode=direct
RestartSec=15min
UNIT

cat > "$UNIT_DIR/steam-catalog.timer" <<UNIT
[Unit]
Description=Load the full Steam catalogue weekly

[Timer]
OnCalendar=Sun *-*-* 10:00
Persistent=true
RandomizedDelaySec=10min

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now steam-pipeline.timer steam-catalog.timer
systemctl --user list-timers 'steam-*'
