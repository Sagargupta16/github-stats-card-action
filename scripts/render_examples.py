"""Render the README preview and the theme gallery from a committed stats snapshot.

    python scripts/render_examples.py            # write every example SVG
    python scripts/render_examples.py --check    # exit 1 if any committed SVG is stale
    GITHUB_TOKEN=<token> python scripts/render_examples.py --refresh   # new snapshot first

The snapshot (examples/stats-snapshot.json) is the stats dict fetch_stats returned
for one real user on one day, so every example renders offline, needs no token,
and comes out byte-identical on every machine. That doubles as a demo mode: point
SNAPSHOT at your own JSON to preview a card without calling the API.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import github_stats_card as card

EXAMPLES = ROOT / "examples"
SNAPSHOT = EXAMPLES / "stats-snapshot.json"
GALLERY = EXAMPLES / "gallery"
# one custom accent next to the presets, to show the contrast pass on a user color
CUSTOM_ACCENT = "#f59e0b"


def load_snapshot(path: Path = SNAPSHOT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_all(snapshot: dict) -> dict[Path, str]:
    """Every example file and its content, keyed by path."""
    stats, username = snapshot["stats"], snapshot["username"]
    title = f"GITHUB | @{username.upper()}"

    def draw(theme: str, layout: str, accent: str = "") -> str:
        accent = accent or card.THEMES[theme].accent
        return card.render_card(stats, username, title, accent, theme, layout) + "\n"

    files = {EXAMPLES / "github-stats.svg": draw("dark", "wide")}
    for theme in card.THEMES:
        files[GALLERY / f"{theme}.svg"] = draw(theme, "wide")
        files[GALLERY / f"{theme}-compact.svg"] = draw(theme, "compact")
    files[GALLERY / "dark-amber.svg"] = draw("dark", "wide", CUSTOM_ACCENT)
    return files


def refresh(username: str) -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise SystemExit("--refresh needs GITHUB_TOKEN")
    stats = card.fetch_stats(username, token, int(card.DEFAULT_LANGUAGES), set())
    snapshot = {
        "username": username,
        "fetched": dt.datetime.now(dt.UTC).date().isoformat(),
        "stats": stats,
    }
    SNAPSHOT.write_text(
        json.dumps(snapshot, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote {SNAPSHOT.relative_to(ROOT)} for @{username}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="fail if any example is stale"
    )
    parser.add_argument(
        "--refresh", metavar="USERNAME", help="fetch a new snapshot first"
    )
    args = parser.parse_args()

    if args.refresh:
        refresh(args.refresh)
    files = render_all(load_snapshot())
    if args.check:
        stale = [
            path
            for path, svg in files.items()
            if not path.exists() or path.read_text(encoding="utf-8") != svg
        ]
        for path in stale:
            print(
                f"::error::{path.relative_to(ROOT)} is stale; run python scripts/render_examples.py"
            )
        raise SystemExit(1 if stale else 0)
    for path, svg in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8", newline="\n")
        print(f"{path.relative_to(ROOT).as_posix()}: {len(svg.encode()):,} bytes")


if __name__ == "__main__":
    main()
