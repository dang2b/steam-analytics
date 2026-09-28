import pytest

import load


class FakeConnection:
    """Mimics psycopg2: `with conn` commits or rolls back but doesn't close."""

    def __init__(self):
        self.events = []

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
