# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.1.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.1.0
[1.0.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.0.0
