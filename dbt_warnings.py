"""Report dbt warnings, which don't fail the daily job and would otherwise go unseen.

Warning-level tests (catalogue coverage, stale SteamSpy stats) and source
freshness warnings leave dbt's exit code at 0, so systemd's failure
notification never fires for them. This reads dbt's result files, prints
every warning to the job log and sends one desktop notification.

Usage: python dbt_warnings.py <run_results.json> <sources.json>
"""
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("dbt_warnings")


def _name(unique_id):
    # e.g. test.steam_analytics.assert_catalog_coverage -> assert_catalog_coverage
    return unique_id.split(".")[2]


def build_warnings(run_results):
    warnings = []
    for result in run_results["results"]:
        if result["status"] == "warn":
            rows = result.get("failures")
            detail = f"{rows} rows" if rows is not None else result.get("message") or "warning"
            warnings.append(f"test {_name(result['unique_id'])}: {detail}")
    return warnings


def freshness_warnings(sources):
    warnings = []
    for result in sources["results"]:
        if result["status"] == "warn":
            # source.steam_analytics.raw.games -> raw.games
            source = ".".join(result["unique_id"].split(".")[2:])
            hours = result["max_loaded_at_time_ago_in_s"] / 3600
            warnings.append(f"source {source}: last loaded {hours:.0f} hours ago")
    return warnings


def _read(path, parse):
    try:
        return parse(json.loads(Path(path).read_text()))
    except FileNotFoundError:
        # the step didn't get far enough to write it; the job's own
        # failure notification covers that case
        logger.warning("%s not found, skipping", path)
        return []


def notify(warnings):
    if not shutil.which("notify-send"):
        return
    summary = f"Steam pipeline: {len(warnings)} dbt warning{'s' if len(warnings) > 1 else ''}"
    subprocess.run(["notify-send", "--urgency=normal", summary, "\n".join(warnings)], check=False)


def main(run_results_path, sources_path):
    warnings = _read(run_results_path, build_warnings) + _read(sources_path, freshness_warnings)
    for warning in warnings:
        logger.warning(warning)
    if warnings:
        notify(warnings)
    else:
        logger.info("no dbt warnings")
    return warnings


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    main(*sys.argv[1:3])
