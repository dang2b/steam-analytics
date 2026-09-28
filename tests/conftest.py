import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def steamspy_sample():
    return read_fixture("steamspy_top100_sample.json")


@pytest.fixture
def player_summaries_sample():
    return read_fixture("player_summaries_sample.json")
