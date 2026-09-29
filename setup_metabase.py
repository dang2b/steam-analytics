"""Build the Steam Analytics dashboard in Metabase from code.

Safe to re-run: it creates the admin user and database connection only if
they're missing, and rebuilds every card and the dashboard from scratch.
"""
import logging
import sys
import time
from urllib.parse import quote

import requests

from config import (
    DB_NAME,
    DB_PASSWORD,
    DB_USER,
    MB_ADMIN_EMAIL,
    MB_ADMIN_PASSWORD,
    MB_URL,
)

logger = logging.getLogger("setup_metabase")

DATABASE_NAME = "Steam Pipeline"
COLLECTION_NAME = "Steam Analytics"
DASHBOARD_NAME = "Steam Top 100 Overview"
MART_TABLES = {
    "game_rankings",
    "publisher_summary",
    "game_daily_stats",
    "catalog_owners_distribution",
}

# the color scheme isn't set here: it's a per-user choice under Account
# settings > Profile > Theme (system default, dark or light), and setting it
# on every run would overwrite that choice
SETTINGS = {
    # no AI provider is configured, and the dashboard doesn't need Metabot:
    # turn off the assistant and the AI features. show-metabot (the home
    # page character) and metabot-show-illustrations need paid features
    # (whitelabel, ai-controls), so the open source edition can't change them
    "metabot-enabled?": False,
    "embedded-metabot-enabled?": False,
    "ai-features-enabled?": False,
}

# Metabase reaches Postgres over the compose network, so it uses the
# service name, not localhost
SOURCE_DB = {
    "host": "db",
    "port": 5432,
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
    # only expose the dbt marts, so charts are built on modeled data
    "schema-filters-type": "inclusion",
    "schema-filters-patterns": "public_marts",
}

# each card: (name, display, sql, visualization_settings, (col, row, width, height))
# the dashboard grid is 24 columns wide. Chart columns get quoted aliases
# because Metabase uses a native query's column names as axis titles,
# tooltips and table headers
CARDS = [
    (
        "Players online (top 100)",
        "scalar",
        "select sum(concurrent_users) as players from public_marts.game_rankings",
        {},
        (0, 0, 8, 3),
    ),
    (
        "Free-to-play share",
        "scalar",
        """
        select round(100.0 * count(*) filter (where is_free) / count(*), 1) as pct_free
        from public_marts.game_rankings
        """,
        {"column_settings": {'["name","pct_free"]': {"suffix": "%"}}},
        (8, 0, 8, 3),
    ),
    (
        "Games on discount",
        "scalar",
        """
        select count(*) filter (where is_discounted) as discounted
        from public_marts.game_rankings
        """,
        {},
        (16, 0, 8, 3),
    ),
    (
        "Top 10 games by concurrent players",
        "row",
        """
        select game_name as "Game", concurrent_users as "Concurrent players"
        from public_marts.game_rankings
        where ccu_rank <= 10
        order by ccu_rank
        """,
        {"graph.dimensions": ["Game"], "graph.metrics": ["Concurrent players"]},
        (0, 3, 12, 8),
    ),
    (
        "Top 10 publishers by concurrent players",
        "row",
        """
        select publisher as "Publisher", total_concurrent_users as "Concurrent players"
        from public_marts.publisher_summary
        where ccu_rank <= 10
        order by ccu_rank
        """,
        {"graph.dimensions": ["Publisher"], "graph.metrics": ["Concurrent players"]},
        (12, 3, 12, 8),
    ),
    (
        "Average positive review % by price tier",
        "bar",
        """
        select
            price_tier as "Price tier",
            round(100 * avg(positive_review_ratio), 1) as "Average positive reviews (%)"
        from public_marts.game_rankings
        group by price_tier
        order by min(price_usd)
        """,
        {
            "graph.dimensions": ["Price tier"],
            "graph.metrics": ["Average positive reviews (%)"],
            "graph.show_values": True,
        },
        (0, 11, 12, 7),
    ),
    (
        "Games by price tier",
        "pie",
        """
        select price_tier as "Price tier", count(*) as "Games"
        from public_marts.game_rankings
        group by price_tier
        """,
        {"pie.dimension": "Price tier", "pie.metric": "Games"},
        (12, 11, 12, 7),
    ),
    (
        "10 best reviewed games",
        "table",
        """
        select
            review_score_rank as "Rank",
            game_name as "Game",
            round(100 * positive_review_ratio, 1) as "Positive reviews (%)",
            total_reviews as "Total reviews",
            price_tier as "Price tier"
        from public_marts.game_rankings
        where review_score_rank <= 10
        order by review_score_rank
        """,
        {},
        (0, 18, 24, 9),
    ),
    (
        "Concurrent players over time: today's top 5",
        "line",
        """
        select
            d.snapshot_date as "Date",
            d.game_name as "Game",
            d.concurrent_users as "Concurrent players"
        from public_marts.game_daily_stats as d
        join public_marts.game_rankings as r on r.appid = d.appid
        where r.ccu_rank <= 5
        order by d.snapshot_date
        """,
        {
            "graph.dimensions": ["Date", "Game"],
            "graph.metrics": ["Concurrent players"],
        },
        (0, 27, 24, 8),
    ),
    (
        "Top 100's share of estimated owners (full catalogue)",
        "scalar",
        """
        select round(100 * sum(top100_owners_estimate) / nullif(sum(owners_estimate), 0), 1)
            as top100_share
        from public_marts.catalog_owners_distribution
        """,
        {"column_settings": {'["name","top100_share"]': {"suffix": "%"}}},
        (0, 35, 8, 8),
    ),
    (
        "Catalogue games vs. owners by owners range",
        "bar",
        """
        select
            owners_bucket as "Owners range",
            round(100 * share_of_games, 1) as "Share of games (%)",
            round(100 * share_of_owners, 1) as "Share of estimated owners (%)"
        from public_marts.catalog_owners_distribution
        order by owners_min
        """,
        {
            "graph.dimensions": ["Owners range"],
            "graph.metrics": ["Share of games (%)", "Share of estimated owners (%)"],
        },
        (8, 35, 16, 8),
    ),
]


class Metabase:
    def __init__(self, url):
        self.url = url.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        r = self.session.request(method, f"{self.url}/api/{path}", timeout=30, **kwargs)
        if not r.ok:
            raise RuntimeError(f"{method} {path} failed ({r.status_code}): {r.text[:300]}")
        return r.json() if r.content else None

    def wait_until_healthy(self, timeout=180):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if self.session.get(f"{self.url}/api/health", timeout=5).ok:
                    return
            except requests.ConnectionError:
                pass
            time.sleep(3)
        raise RuntimeError(f"Metabase not healthy at {self.url} after {timeout}s")

    def authenticate(self, email, password):
        props = self.request("GET", "session/properties")
        if not props.get("has-user-setup"):
            logger.info("first run: creating admin user %s", email)
            session = self.request("POST", "setup", json={
                "token": props["setup-token"],
                "user": {
                    "email": email,
                    "password": password,
                    "first_name": "Admin",
                    "last_name": "User",
                    "site_name": "Steam Analytics",
                },
                "prefs": {"site_name": "Steam Analytics", "allow_tracking": False},
            })
        else:
            session = self.request(
                "POST", "session", json={"username": email, "password": password}
            )
        self.session.headers["X-Metabase-Session"] = session["id"]

    def apply_settings(self, settings):
        for key, value in settings.items():
            # many keys end in '?', which would otherwise start a query string
            self.request("PUT", f"setting/{quote(key, safe='')}", json={"value": value})
        logger.info("applied %d settings", len(settings))

    def get_or_create_database(self):
        for db in self.request("GET", "database")["data"]:
            if db["name"] == DATABASE_NAME:
                return db["id"]
        logger.info("connecting Metabase to Postgres")
        db = self.request("POST", "database", json={
            "engine": "postgres",
            "name": DATABASE_NAME,
            "details": SOURCE_DB,
        })
        return db["id"]

    def sync(self, db_id, timeout=60):
        # pick up tables dbt created or changed since the last sync
        self.request("POST", f"database/{db_id}/sync_schema")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            tables = self.request("GET", f"database/{db_id}/metadata")["tables"]
            names = {t["name"] for t in tables}
            if names >= MART_TABLES:
                return
            time.sleep(2)
        raise RuntimeError("mart tables not found in Metabase; did `dbt build` run?")

    def reset_collection(self):
        for coll in self.request("GET", "collection"):
            if coll.get("name") == COLLECTION_NAME and not coll.get("archived"):
                items = self.request("GET", f"collection/{coll['id']}/items")["data"]
                for item in items:
                    if item["model"] in ("card", "dashboard"):
                        self.request("DELETE", f"{item['model']}/{item['id']}")
                logger.info("cleared %d items from existing collection", len(items))
                return coll["id"]
        return self.request("POST", "collection", json={"name": COLLECTION_NAME})["id"]

    def create_card(self, db_id, collection_id, name, display, sql, viz):
        card = self.request("POST", "card", json={
            "name": name,
            "display": display,
            "collection_id": collection_id,
            "dataset_query": {
                "type": "native",
                "native": {"query": sql.strip()},
                "database": db_id,
            },
            "visualization_settings": viz,
        })
        return card["id"]

    def create_dashboard(self, collection_id, placements):
        dashboard = self.request("POST", "dashboard", json={
            "name": DASHBOARD_NAME,
            "collection_id": collection_id,
            "description": (
                "Popularity, reviews and pricing across SteamSpy's top 100 games "
                "of the last two weeks, and how ownership spreads across the full "
                "catalogue."
            ),
        })
        dashcards = [
            # negative ids tell Metabase these are new dashcards
            {"id": -i, "card_id": card_id, "col": col, "row": row, "size_x": w, "size_y": h}
            for i, (card_id, (col, row, w, h)) in enumerate(placements, start=1)
        ]
        self.request(
            "PUT",
            f"dashboard/{dashboard['id']}",
            json={"dashcards": dashcards, "width": "full"},
        )
        return dashboard["id"]


def main():
    if not MB_ADMIN_EMAIL or not MB_ADMIN_PASSWORD:
        raise RuntimeError("set MB_ADMIN_EMAIL and MB_ADMIN_PASSWORD in .env")

    mb = Metabase(MB_URL)
    mb.wait_until_healthy()
    mb.authenticate(MB_ADMIN_EMAIL, MB_ADMIN_PASSWORD)

    mb.apply_settings(SETTINGS)

    db_id = mb.get_or_create_database()
    mb.sync(db_id)
    collection_id = mb.reset_collection()

    placements = []
    for name, display, sql, viz, position in CARDS:
        card_id = mb.create_card(db_id, collection_id, name, display, sql, viz)
        placements.append((card_id, position))
    logger.info("created %d cards", len(placements))

    dashboard_id = mb.create_dashboard(collection_id, placements)
    logger.info("dashboard ready: %s/dashboard/%d", MB_URL, dashboard_id)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    try:
        main()
    except Exception:
        logger.exception("metabase setup failed")
        sys.exit(1)
