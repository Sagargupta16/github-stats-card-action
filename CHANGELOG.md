# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-11-14

A flat style and a 320 px phone card, both opt-in. With no new inputs set, every
theme and layout renders byte-identical to 1.3.0 (961 renders compared against
1.3.0 over five data sets, six themes, two layouts, eight accents and two titles).

### Added

- `style` input: `classic` (default, the card as in 1.3.0) or `flat`, the look of the profile README the card comes from. Cards and tiles have one fill and one hairline border, with no gradient or glow; labels are mono at 10.5 px, numerals and language names sans. The current streak sits beside the title, green with a pulsing dot while it is live. Every entrance holds its start value from 0 s and rests on the element's own attributes, so a still frame (a link preview, a viewer without SMIL) shows the whole card where the classic card shows empty tiles and an empty calendar.
- The flat wide card's calendar enters one week at a time: 65 animated elements where the classic card has 371 (svg-forge's count). A column outline steps across the year once every 12 s and the busiest day ripples every 2 s; every loop lasts 2 or 12 s.
- `layout: phone`: a 320 px card with six tiles of the past 12 months, the last 20 weeks of the calendar, total stars and followers on one line, and the top languages, with no label under 11.5 px. It exists only in the flat style, so it is drawn flat whatever `style` says, and `style: flat` with `layout: compact` draws it too.
- `fetch_stats()` returns `repo_stars`, the stars of each counted repository by name, from the same paginated query. The card does not draw it; the profile README's vendored copy had added it locally.
- `examples/gallery/flat.svg`, `flat-phone.svg`, `flat-light.svg` and `flat-light-phone.svg`, rendered from the snapshot like the other examples. All 18 report 0 errors under svg-forge's `validate_svg.py --strict-contrast`.
- CI runs the action a third time with `style: flat` and `layout: phone` and asserts the 320 px flat card.

### Documentation

- README: the `style` input and the `phone` layout, a Flat style section, a `<picture>` embed with the 840 px card in a `(min-width: 1012px)` source and the phone card as the `<img>`, and the flat rows in the Measured table.

## [1.3.0] - 2026-10-25

Larger labels on the wide card. The wide layout keeps every theme, input and
size from 1.2.0; only its text grows, so the default card is no longer
byte-identical to 1.1.x.

### Changed

- No text on the wide card is under 10.5 px. The title, tile labels, the streak panel, the languages heading and the legend were 8 to 10 px; at 840 px in a README column they read at about 7.9 px. A 10.5 px label holds 10.4 px in an 831 px column.
- The first tile reads `CONTRIBUTIONS`; `CONTRIBUTIONS, LAST YEAR` is 180 px at 10.5 px, wider than its 130 px tile, and the calendar beside it already shows the year.
- The streak panel stacks `LONGEST` and `ACTIVE` on two lines, since one line at 10.5 px is wider than the panel. The panel and card keep their size (840 x 340 for six languages).
- The compact layout's title is 10.5 px too; its other text keeps its 9 px floor.
- Checked in a browser on eight themes and layouts: no text crosses its tile, panel or the card edge, and no two lines overlap. svg-forge's `validate_svg.py --strict-contrast` reports 0 errors on all 14 examples.

## [1.2.0] - 2026-10-18

Themes and a compact phone layout. With no new inputs set, the card is
byte-identical to 1.1.x (checked against 1.1.0 renders for four accents).

### Added

- `theme` input with six presets: `dark` (default), `dim`, `light`, `dracula`, `nord` and `solarized-light`. Each preset's text colors, calendar levels and language swatches go through the contrast pass on that theme's own background and tiles, so every preset meets 4.5:1 for text and 3:1 for graphics. All 14 example SVGs report 0 errors under svg-forge's `validate_svg.py --strict-contrast`.
- `layout` input: `wide` (default, 840 px) or `compact` (400 px): six tiles in a 3 by 2 grid with the streak as the sixth, the last 26 weeks of the calendar, a two-column language legend, and no text under 9 px. Drawn 360 px wide, its smallest text is 8.1 px on screen against 3.4 px for the wide card.
- `examples/gallery/`: every theme in both layouts plus one custom accent, rendered offline from `examples/stats-snapshot.json` by `scripts/render_examples.py` (`--check` to verify, `--refresh <user>` to fetch a new snapshot). A test fails if a committed example drifts from the code.
- `scripts/measure.py`: card size, SVG bytes, on-screen text size at 360 px, render time and (with `--live`) GraphQL requests per run. Its results are in the README "Measured" section.
- `scripts/screenshot_phone.py` and `docs/phone-wide-vs-compact.webp`: the wide and compact cards in a 375 px phone viewport.
- CI runs the action a second time with `theme: light` and `layout: compact` and asserts the card is 400 px wide on the light background.

### Changed

- `accent` now defaults to empty, meaning the theme's accent. For the default `dark` theme that is still `#60a5fa`.
- `ensure_contrast` takes the background to measure against and darkens on a light background instead of lightening.

### Documentation

- README: themes and layouts gallery, a multi-variant workflow, a `<picture>` embed that picks the compact or light card by screen width and color scheme, the Measured table, and Limits lines for the compact calendar window.

## [1.1.1] - 2026-10-18

Docs and CI only; `action.yml` and the script are unchanged, so the card renders
exactly as in 1.1.0.

### Changed

- CI lints with ruff 0.17.1 (was 0.16.6). The tree passes the new release's default ruleset unchanged.

### Documentation

- README: CI, release, Marketplace and license badges, and a link to the Marketplace listing.
- README: a "Why not a hosted widget" comparison, a mermaid diagram of the pipeline under "How it works", and a "Design decisions" section.
- README: a note on pinning the action to a full commit SHA.
- README Limits: the fixed 840 px layout gets hard to read at phone widths, and the action leaves Python 3.13 first on `PATH` for later steps in your job.

## [1.1.0] - 2026-10-11

Text, calendar levels and language swatches now meet WCAG contrast on the card
background. The README preview went from 80 contrast errors to 0 under svg-forge's
`validate_svg.py --strict-contrast`; layout, quartile cuts and motion are
unchanged.

### Fixed

- Contribution calendar levels reach 3:1 on the card (WCAG 1.4.11). The four levels are now solid shades running from the deep shade to the accent, instead of the deep shade at 33%, 60% and 87% opacity, where the 33% and 60% levels measured 1.40:1 and 2.05:1 on the default card. On the default card they are `#2459c6`, `#3872d7`, `#4c8ce9` and `#60a5fa`. Empty days keep their faint tint.
- A language color too dark for the card is drawn at the nearest lighter shade of the same hue that reaches 3:1, in the bar and the legend. CSS (`#663399`, 2.27:1) becomes `#7d3fbc`. Colors that already pass are unchanged.
- An `accent` too dark to read is lightened to the nearest shade that reaches 4.5:1 for the title, and the busiest calendar level uses the same shade. Accents that already pass, including the default, are unchanged.

## [1.0.0] - 2026-09-25

Initial release. The card design comes from the stats card on
[@Sagargupta16's profile README](https://github.com/Sagargupta16/Sagargupta16).

### Added

- Composite action that renders an animated GitHub stats card into an SVG file in the caller's repo (default `assets/github-stats.svg`): five stat tiles, a contribution calendar that fades in column by column, current and longest streak, and a stacked bar of the top languages by code size.
- Inputs `username`, `token`, `output`, `accent`, `title`, `languages` and `exclude-repos`; outputs `contributions`, `streak` and `stars`.
- Stars and languages count the public, non-fork repositories the user owns, paging through them 100 at a time.
- When the GitHub API call fails, the existing card is kept and the action exits 0 with a warning; with no card to keep, it exits 1.
- Self-contained SVG (no scripts, external fonts or images), with every user-supplied string HTML-escaped.
- CI: ruff, pytest on Python 3.12, 3.13 and 3.14, and a job that runs `action.yml` against live data.

[1.4.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.4.0
[1.3.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.3.0
[1.2.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.2.0
[1.1.1]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.1.1
[1.1.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.1.0
[1.0.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.0.0
