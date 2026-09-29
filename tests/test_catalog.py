import pytest

import catalog
from extract_steamspy import CATALOG_PAGE_SIZE

PAGES = [(0, {"a": {}, "b": {}}), (1, {"c": {}}), (2, {"d": {}})]


@pytest.fixture
def fake_pipeline(monkeypatch):
    """Serve PAGES and record every call to the load functions, in order.

    Set calls.run to the (run_id, next_page, resumed) the run lookup returns,
    and calls.fail_at to a page number to make fetching it fail.
    """

    class Calls(list):
        run = (1, 0, False)
        fail_at = None

    calls = Calls()

    def get_catalog_pages(start_page, wait_first):
        calls.append(("fetch", start_page, wait_first))
        for page, raw in PAGES[start_page:]:
            if page == calls.fail_at:
                raise RuntimeError(f"page {page} failed")
            yield page, raw

    monkeypatch.setattr(catalog.extract_steamspy, "get_catalog_pages", get_catalog_pages)
    monkeypatch.setattr(catalog.extract_steamspy, "parse_games", lambda raw: list(raw))
    monkeypatch.setattr(catalog.load, "start_or_resume_catalog_run", lambda: calls.run)
    monkeypatch.setattr(
        catalog.load,
        "load_catalog_page",
        lambda run_id, page, games: calls.append(("load", run_id, page, games)),
    )
    monkeypatch.setattr(
        catalog.load,
        "finish_catalog_run",
        lambda run_id, list_size: calls.append(("finish", run_id, list_size)),
    )
    return calls


def test_new_run_loads_every_page_then_finishes(fake_pipeline):
    total = catalog.run()

    assert fake_pipeline == [
        ("fetch", 0, False),
        ("load", 1, 0, ["a", "b"]),
        ("load", 1, 1, ["c"]),
        ("load", 1, 2, ["d"]),
        # two pages before the last one, which holds one game
        ("finish", 1, 2 * CATALOG_PAGE_SIZE + 1),
    ]
    assert total == 4


def test_resumed_run_continues_from_next_page_and_waits_first(fake_pipeline):
    fake_pipeline.run = (9, 2, True)

    catalog.run()

    # the list size comes from the last page, even when earlier pages were
    # loaded by a previous attempt
    assert fake_pipeline == [
        ("fetch", 2, True),
        ("load", 9, 2, ["d"]),
        ("finish", 9, 2 * CATALOG_PAGE_SIZE + 1),
    ]


def test_failed_run_is_not_marked_finished(fake_pipeline):
    fake_pipeline.fail_at = 1

    with pytest.raises(RuntimeError):
        catalog.run()

    # page 0 stays loaded and checkpointed; no finish, so the next run resumes
    assert fake_pipeline == [("fetch", 0, False), ("load", 1, 0, ["a", "b"])]
