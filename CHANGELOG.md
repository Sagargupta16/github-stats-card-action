# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/Sagargupta16/github-stats-card-action/releases/tag/v1.0.0
