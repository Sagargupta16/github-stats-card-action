# Self-hosted GitHub Stats Card

[![CI](https://github.com/Sagargupta16/github-stats-card-action/actions/workflows/ci.yml/badge.svg)](https://github.com/Sagargupta16/github-stats-card-action/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Sagargupta16/github-stats-card-action)](https://github.com/Sagargupta16/github-stats-card-action/releases/latest)
[![Marketplace](https://img.shields.io/badge/Marketplace-Self--hosted%20GitHub%20Stats%20Card-2563eb?logo=github)](https://github.com/marketplace/actions/self-hosted-github-stats-card)
[![License: MIT](https://img.shields.io/github/license/Sagargupta16/github-stats-card-action)](LICENSE)

A GitHub Action that renders an animated GitHub stats card as an SVG file in your own repo, so your profile README never depends on a hosted widget.

<img src="examples/github-stats.svg" alt="GitHub stats card for @Sagargupta16" width="100%">

Real data for [@Sagargupta16](https://github.com/Sagargupta16), fetched 2026-10-18 into [examples/stats-snapshot.json](examples/stats-snapshot.json). Six themes and a compact phone layout are in the [gallery](#themes-and-layouts).

Public stats-widget hosts serve everyone from shared API quotas, and when a quota runs out your README shows an error instead of your stats. This action renders the card in your own workflow, with your own token, and commits a plain file that GitHub serves like any other file in your repo.

Install it from the GitHub Marketplace: [Self-hosted GitHub Stats Card](https://github.com/marketplace/actions/self-hosted-github-stats-card).

## Quick start

Add `.github/workflows/github-stats.yml` to the repo whose README shows the card (for a profile README, that is the `<username>/<username>` repo):

```yaml
name: GitHub stats card

on:
  schedule:
    - cron: "0 6 * * *" # daily at 06:00 UTC
  workflow_dispatch:

permissions:
  contents: write

jobs:
  card:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: Sagargupta16/github-stats-card-action@v1

      - name: Commit the card if it changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add assets/github-stats.svg
          if ! git diff --cached --quiet; then
            git commit -m "chore: refresh github stats card"
            git push
          fi
```

Run it once from the Actions tab so the file exists, then embed it.

To serve light-mode readers and phones too, add one step per variant (each costs one more GraphQL request) and commit all of them:

```yaml
      - uses: Sagargupta16/github-stats-card-action@v1
      - uses: Sagargupta16/github-stats-card-action@v1
        with:
          theme: light
          output: assets/github-stats-light.svg
      - uses: Sagargupta16/github-stats-card-action@v1
        with:
          layout: compact
          output: assets/github-stats-compact.svg
      - uses: Sagargupta16/github-stats-card-action@v1
        with:
          theme: light
          layout: compact
          output: assets/github-stats-compact-light.svg
```

Then `git add assets/` in the commit step instead of the single file.

The job gets a `contents: write` token, so for the strictest supply-chain setup pin a full commit SHA instead of the moving `v1` tag, and let Renovate or Dependabot bump it:

```yaml
      - uses: Sagargupta16/github-stats-card-action@4a7221cb12bbfb6e89d97c7a2623b60596bf105e # v1.1.0
```

## Embed

```html
<img src="assets/github-stats.svg" alt="GitHub stats" width="100%">
```

The wide card is 840 px and scales down with `width="100%"`. With the four variants above, a `<picture>` lets the browser pick by screen width and color scheme. It takes the first `<source>` whose `media` matches and falls back to the `<img>`:

```html
<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: light)" srcset="assets/github-stats-compact-light.svg">
  <source media="(max-width: 600px)" srcset="assets/github-stats-compact.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/github-stats-light.svg">
  <img src="assets/github-stats.svg" alt="GitHub stats" width="100%">
</picture>
```

Why the compact layout exists, in a 375 px phone viewport ([scripts/screenshot_phone.py](scripts/screenshot_phone.py)):

<img src="docs/phone-wide-vs-compact.webp" alt="The wide card scaled down to a phone column next to the compact card" width="320">

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `username` | `${{ github.repository_owner }}` | GitHub user to render |
| `token` | `${{ github.token }}` | Token for the GraphQL API. The default is enough; see [Limits](#limits) |
| `output` | `assets/github-stats.svg` | Path of the SVG, relative to the workspace. Missing folders are created |
| `theme` | `dark` | Color preset: `dark`, `dim`, `light`, `dracula`, `nord` or `solarized-light`. See [Themes and layouts](#themes-and-layouts) |
| `layout` | `wide` | `wide`: 840 px, the full year. `compact`: 400 px, the last 26 weeks, six tiles in a 3 by 2 grid with the streak as the sixth, no text under 9 px |
| `accent` | the theme's accent | Hex color (`#rrggbb` or `rrggbb`) for the title and the contribution calendar. A color that is hard to read on the theme's background is moved to the nearest shade of the same hue that reaches 4.5:1 (lighter on a dark theme, darker on a light one). Quote it in YAML, where `#` starts a comment: `accent: "#f59e0b"` |
| `title` | `GITHUB \| @<USERNAME>` | Card title, rendered as given |
| `languages` | `6` | How many top languages to show, three per legend row. Past six, the wide card grows 20 px per extra row; the compact card has two per row and grows 20 px per row past the first |
| `exclude-repos` | empty | Comma-separated repository names (`name` or `owner/name`, case-insensitive) left out of stars and languages |

## Outputs

| Output | Description |
| --- | --- |
| `contributions` | Contributions in the last year |
| `streak` | Current streak, in days |
| `stars` | Stars across the counted repositories |

All three are empty when the API call failed and the previous card was kept.

## Themes and layouts

Every preset goes through the same contrast pass as a custom accent, so a palette's own colors are kept where they pass and nudged where they do not: Dracula's comment purple and Nord's `nord3` gray are too dim for small text, so the muted labels come out a few shades lighter.

| `dark` (default) | `dim` |
| --- | --- |
| <img src="examples/gallery/dark.svg" alt="dark theme" width="100%"> | <img src="examples/gallery/dim.svg" alt="dim theme" width="100%"> |
| **`light`** | **`dracula`** |
| <img src="examples/gallery/light.svg" alt="light theme" width="100%"> | <img src="examples/gallery/dracula.svg" alt="dracula theme" width="100%"> |
| **`nord`** | **`solarized-light`** |
| <img src="examples/gallery/nord.svg" alt="nord theme" width="100%"> | <img src="examples/gallery/solarized-light.svg" alt="solarized-light theme" width="100%"> |

`layout: compact`, in `dark` and `light`:

<img src="examples/gallery/dark-compact.svg" alt="compact dark card" width="49%"> <img src="examples/gallery/light-compact.svg" alt="compact light card" width="49%">

Every theme also has a compact file in [examples/gallery/](examples/gallery/), plus `dark-amber.svg` with `accent: "#f59e0b"`. All of them render offline from the snapshot with `python scripts/render_examples.py`, and a test fails if a committed file drifts from what the code renders.

## Measured

From [scripts/measure.py](scripts/measure.py) on the 2026-10-18 snapshot (Python 3.13 on a Windows laptop; render time is the median of 50 renders). "At 360 px" is the on-screen size when the card is drawn 360 px wide, a phone-width README column.

| Variant | Size (px) | SVG bytes | Smallest text at 360 px | Stat values at 360 px | Render (median ms) |
| --- | --- | --- | --- | --- | --- |
| dark wide | 840 x 340 | 37,539 | 3.4 px | 9.4 px | 3.38 |
| dark compact | 400 x 416 | 22,032 | 8.1 px | 18.0 px | 2.96 |
| light wide | 840 x 340 | 37,133 | 3.4 px | 9.4 px | 8.38 |
| light compact | 400 x 416 | 21,642 | 8.1 px | 18.0 px | 8.13 |

- One live run for @Sagargupta16 (`--live`) made 1 GraphQL request and took 4.18 s to fetch; only accounts with more than 100 owned public repositories need a second page.
- All 14 example SVGs report 0 errors under svg-forge's `validate_svg.py --strict-contrast`.

## Why not a hosted widget

| | Shared hosted instance | This action |
| --- | --- | --- |
| API quota | One pool shared by every user of the instance | Your own workflow token |
| When a README is viewed | The instance calls the GitHub API (or serves its cache) | GitHub serves a committed file; no API call |
| When the API fails | The card fails to render | The old card stays, the run warns and exits 0 |
| Runtime dependency | The host has to be up on every view | None after the commit |

[github-readme-stats](https://github.com/anuraghazra/github-readme-stats), the hosted widget with about 80k stars, says this in its own README: "The public Vercel instance [...] is best-effort and can be unreliable due to rate limits and traffic spikes". It recommends self-hosting or generating cards in a GitHub Actions workflow instead, which is what this action does.

## How it works

```mermaid
flowchart TD
    A["schedule or workflow_dispatch"] --> B["action.yml: setup-python 3.13"]
    B --> C["github_stats_card.py: read INPUT_* and GITHUB_TOKEN"]
    C --> D["GraphQL: followers, contribution calendar, first 100 repos"]
    D --> E{"more repos?"}
    E -- yes --> F["GraphQL: next 100 repos"]
    F --> E
    E -- no --> G["stats: totals, streaks, top languages"]
    G --> H["render_card: contrast pass on accent and language colors, then the SVG"]
    H --> I["write output, set outputs"]
    I --> J["your workflow commits the file"]
    D -. "API error" .-> K{"output exists?"}
    F -. "API error" .-> K
    K -- yes --> L["keep the old card, warn, exit 0"]
    K -- no --> M["exit 1"]
```

1. The script queries the GitHub GraphQL API for the user's followers, contribution calendar and totals for the last year, and the public, non-fork repositories they own with their stars and top 10 languages by size, 100 repositories per request.
2. It renders the card: five stat tiles; the contribution calendar, one column per week, fading in left to right; current streak, longest streak and active days; and a stacked bar of the top languages by code size, with a legend.
3. It writes the SVG to `output` and sets the outputs. Your workflow commits the file.

Details:

- Calendar shades are quartiles of your own non-zero days, so the brightest cells are your busiest quarter of active days rather than a fixed count.
- Text and data colors meet WCAG contrast on the card: text reaches 4.5:1, and each calendar level and language swatch reaches 3:1 (WCAG 1.4.11). On a dark theme the four calendar levels are solid shades from a deep blue (or a deep shade of your accent) up to the accent; on a light theme they run from a pale tint of the accent, darkened to 3:1, to the accent, darkened where needed to reach 7:1. Empty days are a faint tint. A language color from GitHub that is too dark for a dark card, such as CSS purple, is drawn at the nearest lighter shade of the same hue, and one too pale for a light card at the nearest darker shade.
- When today has no contributions yet, the streak counts back from yesterday, so an early run does not reset it.
- If the API call fails and `output` already exists, the action keeps the old card, prints a warning and exits 0, so an outage never blanks your README. If there is no card yet, it exits 1.
- The SVG is self-contained: no scripts, no external fonts or images, CSS and SMIL animation only. Every string you pass in and every name from the API is HTML-escaped.
- The script is Python standard library only, and it connects to `https://api.github.com/` and nothing else.

## Design decisions

- **Composite action, standard library only.** There is no Docker image to pull, no `node_modules` or bundled `dist/` to commit, and no package install, so no PyPI or npm release can break a consumer's run. The whole action is `action.yml` plus one script.
- **A committed file instead of a hosted endpoint.** A README view never reaches the GitHub API. Each run costs one GraphQL request, plus one more per extra 100 repositories.
- **One allowed host.** `fetch` refuses any URL outside `https://api.github.com/` before it opens a connection, so the token can only go to GitHub.
- **Keep the old card or exit.** An API error or a mistyped username leaves the existing card in place with a warning and exit 0. A first run with nothing to keep exits 1, so a broken setup is visible.
- **Quartile shading.** Calendar levels are cut at the quartiles of your own non-zero days, so the brightest level marks your busiest quarter of active days (ties collapse levels together), whether a busy day for you means 3 contributions or 30. Fixed thresholds would leave a quiet profile all one shade.
- **Contrast floors, not hand-picked colors.** The accent, every language color and every theme's text colors go through `ensure_contrast`, which moves a color's lightness away from the background, keeping its hue, until it reaches 4.5:1 for text or 3:1 for graphics. Any accent, any theme and any color GitHub returns stay readable, and a new theme is ten colors with no hand-tuning.

## Limits

- Private contributions show up only if the user has turned on "Include private contributions on my profile" in their GitHub profile settings. The default `GITHUB_TOKEN` sees public data.
- Stars and languages count public, non-fork repositories the user owns, whichever token you pass. Organization repositories are left out.
- Contributions cover GitHub's rolling last-year calendar, not the calendar year.
- Languages are ranked by bytes of code, summed over the top 10 languages GitHub detects in each repository.
- github.com only; GitHub Enterprise Server is not supported.
- The card names its fonts with system fallbacks instead of embedding them, so text widths vary slightly between viewers.
- The wide card is a fixed 840 px layout that scales down as a whole. Shown 360 px wide, its smallest text is 3.4 px on screen, which a phone cannot show legibly. Use `layout: compact` (8.1 px at the same width) for phones, through the `<picture>` pattern in [Embed](#embed).
- The compact card shows the last 26 weeks of the calendar, and its shading is cut at the quartiles of those weeks. The longest streak and active days still cover the full year, as its `/ YEAR` label says.
- The action runs `actions/setup-python` with Python 3.13 in your job, and that Python stays first on `PATH` for the steps after it. If a later step needs another version, give it its own `setup-python` step.

## License

[MIT](LICENSE)
