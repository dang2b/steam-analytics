from extract_steamspy import parse_games

# column order load.load_games inserts in
APPID, OWNERS, PRICE, INITIAL_PRICE, DISCOUNT, CCU = 0, 6, 11, 12, 13, 14


def games_by_appid(raw):
    return {game[APPID]: game for game in parse_games(raw)}


def test_one_row_per_game(steamspy_sample):
    games = parse_games(steamspy_sample)

    assert len(games) == len(steamspy_sample)
    assert all(len(game) == 15 for game in games)


def test_prices_become_integer_cents(steamspy_sample):
    rust = games_by_appid(steamspy_sample)[252490]

    assert rust[PRICE] == 1999
    assert rust[INITIAL_PRICE] == 3999
    assert rust[DISCOUNT] == 50


def test_free_game_price_is_zero_not_null(steamspy_sample):
    cs = games_by_appid(steamspy_sample)[730]

    assert cs[PRICE] == 0


def test_missing_or_empty_price_becomes_null(steamspy_sample):
    game = dict(steamspy_sample["730"], price="", initialprice=None)
    del game["discount"]

    [parsed] = parse_games({"730": game})

    assert parsed[PRICE] is None
    assert parsed[INITIAL_PRICE] is None
    assert parsed[DISCOUNT] is None


def test_owners_bucket_kept_as_raw_text(steamspy_sample):
    # parsing the bucket into numbers is dbt staging's job
    cs = games_by_appid(steamspy_sample)[730]

    assert cs[OWNERS] == "100,000,000 .. 200,000,000"
