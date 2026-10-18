# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright", "pillow"]
# ///
"""Screenshot the wide and the compact card in a 375 px wide phone viewport.

    uv run scripts/screenshot_phone.py    # writes docs/phone-wide-vs-compact.webp

Uses the installed Chrome (channel="chrome"); run `uv run --with playwright
playwright install chromium` and drop the channel argument if you have none.
Each card sits in a 16 px padded column, the width a README gets on a phone.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "examples" / "gallery"
OUT = ROOT / "docs" / "phone-wide-vs-compact.webp"
PAGE = """<!doctype html><meta name="viewport" content="width=device-width">
<body style="margin:0;padding:16px;background:#0d1117;color:#e6edf3;
font:600 14px -apple-system,'Segoe UI',sans-serif">
<p>layout: wide (840 px, scaled down)</p><img src="{wide}" width="100%">
<p style="margin-top:24px">layout: compact (400 px)</p><img src="{compact}" width="100%">
</body>"""
# long enough for the slowest entrance (the language bar) to finish
SETTLE_MS = 4000


def main() -> None:
    page_file = ROOT / "docs" / ".phone-preview.html"
    page_file.parent.mkdir(exist_ok=True)
    page_file.write_text(
        PAGE.format(
            wide=(GALLERY / "dark.svg").as_uri(),
            compact=(GALLERY / "dark-compact.svg").as_uri(),
        ),
        encoding="utf-8",
    )
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page(
                viewport={"width": 375, "height": 400}, device_scale_factor=2
            )
            page.goto(page_file.as_uri())
            page.wait_for_timeout(SETTLE_MS)
            png = page.screenshot(full_page=True)
            browser.close()
    finally:
        page_file.unlink()
    Image.open(io.BytesIO(png)).save(OUT, "WEBP", quality=85, method=6)
    print(f"Wrote {OUT.relative_to(ROOT).as_posix()} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
