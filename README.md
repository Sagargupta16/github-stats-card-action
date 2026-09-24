# Self-hosted GitHub Stats Card

A GitHub Action that renders an animated GitHub stats card as an SVG file in your own repo, so your profile README never depends on a hosted widget.

<img src="examples/github-stats.svg" alt="GitHub stats card for @Sagargupta16" width="100%">

Live data for [@Sagargupta16](https://github.com/Sagargupta16), rendered on 2026-09-25.

Public stats-widget hosts serve everyone from shared API quotas, and when a quota runs out your README shows an error instead of your stats. This action renders the card in your own workflow, with your own token, and commits a plain file that GitHub serves like any other file in your repo.

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

## Embed

```html
<img src="assets/github-stats.svg" alt="GitHub stats" width="100%">
```

The card is 840 px wide and scales down with `width="100%"`.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `username` | `${{ github.repository_owner }}` | GitHub user to render |
| `token` | `${{ github.token }}` | Token for the GraphQL API. The default is enough; see [Limits](#limits) |
| `output` | `assets/github-stats.svg` | Path of the SVG, relative to the workspace. Missing folders are created |
| `accent` | `#60a5fa` | Hex color (`#rrggbb` or `rrggbb`) for the title and the contribution calendar. Quote it in YAML, where `#` starts a comment: `accent: "#f59e0b"` |
| `title` | `GITHUB \| @<USERNAME>` | Card title, rendered as given |
| `languages` | `6` | How many top languages to show, three per legend row. Past six, the card grows 20 px per extra row |
| `exclude-repos` | empty | Comma-separated repository names (`name` or `owner/name`, case-insensitive) left out of stars and languages |

## Outputs

| Output | Description |
| --- | --- |
| `contributions` | Contributions in the last year |
| `streak` | Current streak, in days |
| `stars` | Stars across the counted repositories |

All three are empty when the API call failed and the previous card was kept.

## How it works

1. The script queries the GitHub GraphQL API for the user's followers, contribution calendar and totals for the last year, and the public, non-fork repositories they own with their stars and top 10 languages by size, 100 repositories per request.
2. It renders the card: five stat tiles; the contribution calendar, one column per week, fading in left to right; current streak, longest streak and active days; and a stacked bar of the top languages by code size, with a legend.
3. It writes the SVG to `output` and sets the outputs. Your workflow commits the file.

Details:

- Calendar shades are quartiles of your own non-zero days, so the brightest cells are your busiest quarter of active days rather than a fixed count.
- When today has no contributions yet, the streak counts back from yesterday, so an early run does not reset it.
- If the API call fails and `output` already exists, the action keeps the old card, prints a warning and exits 0, so an outage never blanks your README. If there is no card yet, it exits 1.
- The SVG is self-contained: no scripts, no external fonts or images, CSS and SMIL animation only. Every string you pass in and every name from the API is HTML-escaped.
- The script is Python standard library only, and it connects to `https://api.github.com/` and nothing else.

## Limits

- Private contributions show up only if the user has turned on "Include private contributions on my profile" in their GitHub profile settings. The default `GITHUB_TOKEN` sees public data.
- Stars and languages count public, non-fork repositories the user owns, whichever token you pass. Organization repositories are left out.
- Contributions cover GitHub's rolling last-year calendar, not the calendar year.
- Languages are ranked by bytes of code, summed over the top 10 languages GitHub detects in each repository.
- github.com only; GitHub Enterprise Server is not supported.
- The card names its fonts with system fallbacks instead of embedding them, so text widths vary slightly between viewers.

## License

[MIT](LICENSE)
