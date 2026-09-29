import extract_friends
from extract_friends import (
    get_player_games,
    parse_owned_games,
    parse_player_summaries,
    parse_recent_games,
)

PUBLIC, PRIVATE, EMPTY = "76561190000000001", "76561190000000002", "76561190000000003"


def test_parses_players_into_load_order(player_summaries_sample):
    players = parse_player_summaries(player_summaries_sample)

    assert players[0] == (
        "76561190000000001",
        "test_player_one",
        "https://steamcommunity.com/profiles/76561190000000001/",
        0,
        False,
    )
    assert len(players) == 3


def test_configured_user_is_flagged_as_self(player_summaries_sample):
    players = parse_player_summaries(player_summaries_sample, self_id=PRIVATE)

    assert [player[4] for player in players] == [False, True, False]


def test_no_players_returns_empty_list():
    assert parse_player_summaries({"response": {"players": []}}) == []


def test_summaries_request_includes_the_user(monkeypatch, player_summaries_sample):
    calls = []

    def fake_get_json(url, params=None):
        calls.append(params)
        return player_summaries_sample

    monkeypatch.setattr(extract_friends, "get_json", fake_get_json)

    extract_friends.get_player_summaries(["1", "2", "3"], self_id="0")

    assert calls[0]["steamids"] == "0,1,2,3"


def test_owned_games_keep_raw_playtime_and_last_played(player_games_sample):
    rows, visible = parse_owned_games(PUBLIC, player_games_sample["owned"][PUBLIC])

    assert visible
    assert rows == [
        (PUBLIC, 730, "Counter-Strike 2", 5423, 1790500000),
        # Steam's 0 is stored as-is. It means unknown, not never played: Steam
        # only gives the last-played date for the API key owner's own games
        (PUBLIC, 570, "Dota 2", 0, 0),
    ]


def test_private_library_is_not_visible(player_games_sample):
    assert parse_owned_games(PRIVATE, player_games_sample["owned"][PRIVATE]) == ([], False)
    assert parse_recent_games(PRIVATE, player_games_sample["recent"][PRIVATE]) == ([], False)


def test_empty_library_is_visible_but_has_no_games(player_games_sample):
    # owns nothing / played nothing recently, which isn't the same as private
    assert parse_owned_games(EMPTY, player_games_sample["owned"][EMPTY]) == ([], True)
    assert parse_recent_games(EMPTY, player_games_sample["recent"][EMPTY]) == ([], True)


def test_recent_games_parse_into_load_order(player_games_sample):
    rows, visible = parse_recent_games(PUBLIC, player_games_sample["recent"][PUBLIC])

    assert visible
    assert rows == [(PUBLIC, 730, "Counter-Strike 2", 312, 5423)]


def test_player_games_collects_every_player(player_games_sample):
    statuses, owned, recent = get_player_games(
        [PUBLIC, PRIVATE, EMPTY],
        fetch_owned=player_games_sample["owned"].get,
        fetch_recent=player_games_sample["recent"].get,
    )

    assert statuses == [
        (PUBLIC, True, 2, True, 1),
        (PRIVATE, False, 0, False, 0),
        (EMPTY, True, 0, True, 0),
    ]
    assert len(owned) == 2
    assert len(recent) == 1
