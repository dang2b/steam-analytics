import extract_friends
from extract_friends import parse_player_summaries


def test_parses_players_into_load_order(player_summaries_sample):
    players = parse_player_summaries(player_summaries_sample)

    assert players[0] == (
        "76561190000000001",
        "test_player_one",
        "https://steamcommunity.com/profiles/76561190000000001/",
        0,
    )
    assert len(players) == 3


def test_no_players_returns_empty_list():
    assert parse_player_summaries({"response": {"players": []}}) == []


def test_summaries_request_joins_ids(monkeypatch, player_summaries_sample):
    calls = []

    def fake_get_json(url, params=None):
        calls.append(params)
        return player_summaries_sample

    monkeypatch.setattr(extract_friends, "get_json", fake_get_json)

    extract_friends.get_friend_summaries(["1", "2", "3"])

    assert calls[0]["steamids"] == "1,2,3"
