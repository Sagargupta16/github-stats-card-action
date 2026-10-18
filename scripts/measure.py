"""Measure the numbers the README quotes, from the committed stats snapshot.

    python scripts/measure.py                          # offline: size, legibility, render time
    GITHUB_TOKEN=<token> python scripts/measure.py --live Sagargupta16   # plus API requests

Prints a markdown table per measurement. Legibility is the on-screen size of the
smallest text and of the stat values when the card is drawn 360 px wide, a
common phone width for a README column.
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from render_examples import load_snapshot

import github_stats_card as card

PHONE_WIDTH = 360
RUNS = 50


def font_sizes(svg: str) -> list[float]:
    root = xml.dom.minidom.parseString(svg).documentElement
    nodes = root.getElementsByTagName("text") + root.getElementsByTagName("tspan")
    return [float(n.getAttribute("font-size")) for n in nodes]


def render_ms(stats: dict, username: str, theme: str, layout: str) -> float:
    accent = card.THEMES[theme].accent
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        card.render_card(stats, username, "t", accent, theme, layout)
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)


def offline(snapshot: dict) -> None:
    stats, username = snapshot["stats"], snapshot["username"]
    title = f"GITHUB | @{username.upper()}"
    print(
        f"Snapshot: @{username}, fetched {snapshot['fetched']}; {RUNS} renders each\n"
    )
    print(
        f"| Variant | Size (px) | SVG bytes | Smallest text at {PHONE_WIDTH} px | "
        f"Stat values at {PHONE_WIDTH} px | Render (median ms) |"
    )
    print("| --- | --- | --- | --- | --- | --- |")
    for theme in ("dark", "light"):
        for layout in card.LAYOUTS:
            accent = card.THEMES[theme].accent
            svg = card.render_card(stats, username, title, accent, theme, layout) + "\n"
            root = xml.dom.minidom.parseString(svg).documentElement
            w, h = int(root.getAttribute("width")), int(root.getAttribute("height"))
            sizes = font_sizes(svg)
            scale = PHONE_WIDTH / w
            print(
                f"| {theme} {layout} | {w} x {h} | {len(svg.encode()):,} | "
                f"{min(sizes) * scale:.1f} px | {max(sizes) * scale:.1f} px | "
                f"{render_ms(stats, username, theme, layout):.2f} |"
            )


def live(username: str) -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise SystemExit("--live needs GITHUB_TOKEN")
    calls = 0
    fetch = card.fetch

    def counting_fetch(*args: object, **kwargs: object) -> bytes:
        nonlocal calls
        calls += 1
        return fetch(*args, **kwargs)

    card.fetch = counting_fetch
    start = time.perf_counter()
    stats = card.fetch_stats(username, token, int(card.DEFAULT_LANGUAGES), set())
    seconds = time.perf_counter() - start
    print(f"\nLive run for @{username}\n")
    print("| GraphQL requests | Fetch time (s) | Contributions | Stars |")
    print("| --- | --- | --- | --- |")
    print(
        f"| {calls} | {seconds:.2f} | {stats['contributions']:,} | {stats['stars']:,} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", metavar="USERNAME", help="also time one real fetch")
    args = parser.parse_args()
    offline(load_snapshot())
    if args.live:
        live(args.live)


if __name__ == "__main__":
    main()
