"""Load the test fixtures into Postgres through the real load functions.

CI uses this instead of the live APIs, so dbt has data to build and test
against. Don't point it at a database you care about: it upserts fixture
rows over real ones.
"""
import json
from pathlib import Path

import load
from extract_friends import parse_player_summaries
from extract_steamspy import parse_games

FIXTURES = Path(__file__).parent / "fixtures"


def main():
    games = json.loads((FIXTURES / "steamspy_top100_sample.json").read_text())
    players = json.loads((FIXTURES / "player_summaries_sample.json").read_text())

    load.load_games(parse_games(games))
    load.load_friends(parse_player_summaries(players))


if __name__ == "__main__":
    main()
