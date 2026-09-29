import pytest

import catalog


@pytest.fixture
def loaded(monkeypatch):
    """Serve two fake pages and record what gets loaded."""
    pages = [(0, {"a": {}, "b": {}}), (1, {"c": {}})]
    loaded = []

    monkeypatch.setattr(
        catalog.extract_steamspy, "get_catalog_pages", lambda start_page: iter(pages[start_page:])
    )
    monkeypatch.setattr(catalog.extract_steamspy, "parse_games", lambda raw: list(raw))
    monkeypatch.setattr(catalog.load, "load_catalog_page", loaded.append)
    return loaded


def test_each_page_is_loaded_before_the_next(loaded):
    total = catalog.run()

    assert loaded == [["a", "b"], ["c"]]
    assert total == 3


def test_start_page_is_passed_through(loaded):
    catalog.run(start_page=1)

    assert loaded == [["c"]]


def test_pages_before_a_failure_stay_loaded(monkeypatch):
    loaded = []

    def pages(start_page):
        yield 0, {"a": {}}
        raise RuntimeError("page 1 failed")

    monkeypatch.setattr(catalog.extract_steamspy, "get_catalog_pages", pages)
    monkeypatch.setattr(catalog.extract_steamspy, "parse_games", lambda raw: list(raw))
    monkeypatch.setattr(catalog.load, "load_catalog_page", loaded.append)

    with pytest.raises(RuntimeError):
        catalog.run()

    assert loaded == [["a"]]
