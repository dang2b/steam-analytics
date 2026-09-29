import pytest

import load


class FakeCursor:
    def __init__(self, events, results):
        self.events = events
        self.results = results

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def execute(self, sql, params=None):
        self.events.append(("execute", " ".join(sql.split()), params))

    def executemany(self, sql, rows):
        self.events.append(("executemany", " ".join(sql.split()), list(rows)))

    def fetchone(self):
        return self.results.pop(0)


class FakeConnection:
    """Mimics psycopg2: `with conn` commits or rolls back but doesn't close.

    results are returned by fetchone, one per call, in order.
    """

    def __init__(self):
        self.events = []
        self.results = []

    def cursor(self):
        return FakeCursor(self.events, self.results)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.events.append("rollback" if exc_type else "commit")

    def close(self):
        self.events.append("close")


@pytest.fixture
def fake_conn(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(load.psycopg2, "connect", lambda **kwargs: conn)
    return conn


def test_connection_commits_then_closes(fake_conn):
    with load.connect():
        pass

    assert fake_conn.events == ["commit", "close"]


def test_connection_rolls_back_then_closes_on_error(fake_conn):
    with pytest.raises(RuntimeError), load.connect():
        raise RuntimeError("insert failed")

    assert fake_conn.events == ["rollback", "close"]


def test_load_games_upserts_into_games(fake_conn):
    load.load_games([(730,) * 15])

    (_, sql, rows), *after = fake_conn.events
    assert sql.startswith("INSERT INTO games (")
    assert "ON CONFLICT (appid) DO UPDATE" in sql
    assert rows == [(730,) * 15]
    assert after == ["commit", "close"]


def test_catalog_page_and_checkpoint_commit_together(fake_conn):
    load.load_catalog_page(run_id=7, page=3, games=[(730,) * 15, (570,) * 15])

    upsert, checkpoint, *after = fake_conn.events
    assert upsert[1].startswith("INSERT INTO games_catalog (")
    assert checkpoint[1].startswith("UPDATE catalog_runs SET last_page")
    assert checkpoint[2] == (3, 2, 7)
    # one commit covers both statements
    assert after == ["commit", "close"]


def test_new_run_starts_at_page_zero(fake_conn):
    fake_conn.results.extend([None, (12,)])  # no unfinished run, then the new id

    assert load.start_or_resume_catalog_run() == (12, 0, False)
    assert fake_conn.events[1][1].startswith("INSERT INTO catalog_runs")


def test_unfinished_run_resumes_after_last_page(fake_conn):
    fake_conn.results.append((5, 3))

    assert load.start_or_resume_catalog_run() == (5, 4, True)


def test_run_that_failed_on_first_page_resumes_at_zero(fake_conn):
    fake_conn.results.append((5, None))

    assert load.start_or_resume_catalog_run() == (5, 0, True)


def test_finish_marks_run_finished(fake_conn):
    load.finish_catalog_run(5)

    _, sql, params = fake_conn.events[0]
    assert sql.startswith("UPDATE catalog_runs SET finished_at = now()")
    assert params == (5,)
