"""Record the README's dashboard GIF: scroll down in dark mode, back up in light mode.

Needs Playwright (kept out of requirements-dev.txt so CI doesn't install it),
Google Chrome, ffmpeg and ImageMagick:

    pip install playwright
    python scripts/capture_dashboard.py            # writes docs/images/dashboard.gif

It logs in with the MB_ADMIN_* credentials from .env, switches the admin
account's color scheme for each capture and puts it back afterwards.
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from playwright.sync_api import sync_playwright  # noqa: E402

import setup_metabase as mb_setup  # noqa: E402

CHROME = "/usr/bin/google-chrome"
OUT = REPO / "docs" / "images" / "dashboard.gif"

# the browser window is tall enough to render the whole dashboard at once,
# because Metabase scrolls an inner panel, not the page
WIDTH, TALL = 1440, 3000
VIEW = 900                 # height of the window the GIF scrolls
GIF_WIDTH, FPS = 880, 10
SCROLL_SECONDS, HOLD_SECONDS = 6, 1.5


def capture(mb, dashboard_id, theme, path):
    mb.request("PUT", "setting/color-scheme", json={"value": theme})
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={"width": WIDTH, "height": TALL})
        context.add_cookies([{
            "name": "metabase.SESSION",
            "value": mb.session.headers["X-Metabase-Session"],
            "domain": "localhost",
            "path": "/",
        }])
        page = context.new_page()
        page.goto(f"{mb.url}/dashboard/{dashboard_id}", wait_until="networkidle")
        time.sleep(6)  # let the charts finish drawing
        page.screenshot(path=path)
        browser.close()


def content_height(path):
    # bottom edge of the dashboard, ignoring the empty background below it
    geometry = subprocess.run(
        ["convert", path, "-fuzz", "3%", "-trim", "-format", "%h %Y", "info:"],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    height, top = int(geometry[0]), int(geometry[1].lstrip("+"))
    return top + height + 20


def scroll(start, direction):
    """ffmpeg crop expression: hold, ease over SCROLL_SECONDS, hold."""
    progress = f"clip((t-{start})/{SCROLL_SECONDS}\\,0\\,1)"
    eased = f"(3*pow({progress}\\,2)-2*pow({progress}\\,3))"
    return eased if direction == "down" else f"(1-{eased})"


def build_gif(dark, light, height, out):
    travel = height - VIEW
    down, up = scroll(HOLD_SECONDS, "down"), scroll(0.5, "up")
    frame = f"scale={GIF_WIDTH}:-1:flags=lanczos,setsar=1"
    graph = (
        f"[0]crop={WIDTH}:{VIEW}:0:{travel}*{down},{frame}[a];"
        f"[1]crop={WIDTH}:{VIEW}:0:{travel}*{up},{frame}[b];"
        "[a][b]concat=n=2:v=1[v];[v]split[x][y];"
        # one palette for both themes, so neither looks washed out
        "[x]palettegen=max_colors=128:stats_mode=full[p];"
        "[y][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
    )
    down_seconds = HOLD_SECONDS + SCROLL_SECONDS + 1
    up_seconds = 0.5 + SCROLL_SECONDS + HOLD_SECONDS
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-loop", "1", "-framerate", str(FPS), "-t", str(down_seconds), "-i", dark,
        "-loop", "1", "-framerate", str(FPS), "-t", str(up_seconds), "-i", light,
        "-filter_complex", graph, str(out),
    ], check=True)


def main():
    mb = mb_setup.Metabase(mb_setup.MB_URL)
    mb.authenticate(mb_setup.MB_ADMIN_EMAIL, mb_setup.MB_ADMIN_PASSWORD)
    dashboard_id = next(
        d["id"] for d in mb.request("GET", "dashboard")
        if d["name"] == mb_setup.DASHBOARD_NAME and not d.get("archived")
    )
    original = mb.request("GET", "session/properties")["color-scheme"]

    with tempfile.TemporaryDirectory() as tmp:
        dark, light = f"{tmp}/dark.png", f"{tmp}/light.png"
        try:
            capture(mb, dashboard_id, "dark", dark)
            capture(mb, dashboard_id, "light", light)
        finally:
            mb.request("PUT", "setting/color-scheme", json={"value": original})

        height = min(TALL, max(content_height(dark), content_height(light)))
        build_gif(dark, light, height, OUT)

    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()
