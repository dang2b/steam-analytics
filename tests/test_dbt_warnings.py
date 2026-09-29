import json

import dbt_warnings
from dbt_warnings import build_warnings, freshness_warnings

RUN_RESULTS = {
    "results": [
        {"unique_id": "model.steam_analytics.game_rankings", "status": "success"},
        {"unique_id": "test.steam_analytics.unique_game_rankings_appid.a1b2", "status": "pass",
         "failures": 0},
        {"unique_id": "test.steam_analytics.assert_catalog_coverage", "status": "warn",
         "failures": 1},
        # failures are reported by the job's failure notification, not here
        {"unique_id": "test.steam_analytics.assert_owners_range_valid", "status": "fail",
         "failures": 3},
    ]
}

SOURCES = {
    "results": [
        {"unique_id": "source.steam_analytics.raw.games", "status": "pass",
         "max_loaded_at_time_ago_in_s": 600},
        {"unique_id": "source.steam_analytics.raw.catalog_runs", "status": "warn",
         "max_loaded_at_time_ago_in_s": 9 * 24 * 3600},
    ]
}


def test_only_warning_tests_are_reported():
    assert build_warnings(RUN_RESULTS) == ["test assert_catalog_coverage: 1 rows"]


def test_stale_sources_are_reported_with_their_age():
    assert freshness_warnings(SOURCES) == ["source raw.catalog_runs: last loaded 216 hours ago"]


def test_main_reads_both_files_and_notifies_once(tmp_path, monkeypatch):
    (tmp_path / "run_results.json").write_text(json.dumps(RUN_RESULTS))
    (tmp_path / "sources.json").write_text(json.dumps(SOURCES))
    sent = []
    monkeypatch.setattr(dbt_warnings, "notify", sent.append)

    warnings = dbt_warnings.main(tmp_path / "run_results.json", tmp_path / "sources.json")

    assert len(warnings) == 2
    assert sent == [warnings]


def test_no_warnings_sends_nothing(tmp_path, monkeypatch):
    (tmp_path / "run_results.json").write_text(json.dumps({"results": []}))
    (tmp_path / "sources.json").write_text(json.dumps({"results": []}))
    sent = []
    monkeypatch.setattr(dbt_warnings, "notify", sent.append)

    assert dbt_warnings.main(tmp_path / "run_results.json", tmp_path / "sources.json") == []
    assert sent == []


def test_missing_file_is_skipped(tmp_path, monkeypatch):
    # e.g. dbt build crashed before writing anything
    (tmp_path / "sources.json").write_text(json.dumps(SOURCES))
    monkeypatch.setattr(dbt_warnings, "notify", lambda warnings: None)

    warnings = dbt_warnings.main(tmp_path / "missing.json", tmp_path / "sources.json")

    assert warnings == ["source raw.catalog_runs: last loaded 216 hours ago"]
