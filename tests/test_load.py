import pytest

import load


class FakeCursor:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def executemany(self, sql, rows):
        self.events.append(("executemany", sql, list(rows)))


class FakeConnection:
    """Mimics psycopg2: `with conn` commits or rolls back but doesn't close."""

    def __init__(self):
        self.events = []

    def cursor(self):
        return FakeCursor(self.events)

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


@pytest.mark.parametrize(
    "load_fn, table",
    [(load.load_games, "games"), (load.load_catalog_page, "games_catalog")],
)
def test_game_loads_upsert_into_their_own_table(fake_conn, load_fn, table):
    load_fn([(730,) * 15])

    (_, sql, rows), *after = fake_conn.events
    assert f"INSERT INTO {table} (" in sql
    assert "ON CONFLICT (appid) DO UPDATE" in sql
    assert rows == [(730,) * 15]
    assert after == ["commit", "close"]
