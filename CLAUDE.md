# CLAUDE.md

> This file stacks on top of the workspace root at `C:\Code\GitHub\`:
> - Root [`CLAUDE.md`](../../CLAUDE.md) -- voice, rules, routing map, references, skills, slash commands, conventions.
> - Root [`MEMORY.md`](../../MEMORY.md) -- live facts across repos.
> - Root [`STATUS.md`](../../STATUS.md) -- live PR/CI/security dashboard.
> - [`.claude/resources/`](../../.claude/resources/README.md) -- deep reference for collaboration, workflow, git, OSS, debugging, voice.
>
> Read those first. The guidance below only adds **repo-specific context** -- it does not override anything in the root.

## Project

Composite GitHub Action that renders a self-hosted, animated GitHub stats card (one SVG) into the caller's repo, so a profile README never depends on a hosted widget.

Built 2026-09-25 by extracting `render_github` from [`brand/Sagargupta16/scripts/render-svgs.py`](../../brand/Sagargupta16/scripts/render-svgs.py) and generalizing it. Published as `Sagargupta16/github-stats-card-action@v1` under the Marketplace name "Self-hosted GitHub Stats Card" (the `github-stats-card` slug was already taken). Releases: v1.0.0 (2026-09-25), v1.1.0 (2026-10-11), v1.3.0 (2026-10-25, commit `6490d5b`; it also shipped 1.1.1 and 1.2.0, which were never tagged). A release is: tag `vX.Y.Z` on the merge commit, move `v1` to it, publish the GitHub release, then copy `github_stats_card.py` into `Sagargupta16/Sagargupta16/scripts/vendor/` and record the revision in its README, keeping the profile's one local `repo_stars` line.

## Stack

- **Language**: Python, stdlib only. `action.yml` installs 3.13; CI tests 3.12, 3.13 and 3.14
- **Framework**: GitHub Actions composite action (`action.yml`)
- **Database**: none
- **Package manager**: none for the action; `uv`/`uvx` for local lint and tests
- **Deploy target**: consumed via `uses:` in other repos' workflows; releases are git tags

## Run

```
GITHUB_TOKEN=$(gh auth token) INPUT_USERNAME=Sagargupta16 INPUT_OUTPUT=/tmp/card.svg python github_stats_card.py
```

Set the token inline in the same command and never echo it. Without `INPUT_OUTPUT` the script writes `assets/github-stats.svg` under the current directory.

The README preview and the gallery render offline from `examples/stats-snapshot.json`:

```
python scripts/render_examples.py            # write examples/github-stats.svg and examples/gallery/*.svg
python scripts/render_examples.py --check    # exit 1 if a committed example is stale
GITHUB_TOKEN=$(gh auth token) python scripts/render_examples.py --refresh Sagargupta16   # new snapshot first
```

After `--refresh`, update the fetch date under the preview in `README.md`, rerun `python scripts/measure.py` (add `--live Sagargupta16` with a token for the request count), and copy the new table into the README "Measured" section. `uv run scripts/screenshot_phone.py` (Playwright plus Pillow via inline script metadata, uses installed Chrome) regenerates `docs/phone-wide-vs-compact.webp`.

## Test

```
uvx ruff@0.17.1 check .
uv run --no-project --with pytest==9.1.1 pytest -v
```

`test_github_stats_card.py` never touches the network: `serve()` replaces `fetch` with canned GraphQL replies, and the allowlist test stubs `urlopen`. It covers streaks (including an empty today), level cuts, contrast (every calendar level, language swatch and the title against the card, for light, dark and mid accents), XML validity via `xml.dom.minidom`, escaping of `<&"` in usernames, titles and language names, pagination, exclude-repos, accent handling, card height, the keep-or-exit fallback, input validation, and that the token never reaches stdout or stderr. It also covers every theme in both layouts (contrast on the theme's background and tiles, calendar levels ordered away from the background), the compact layout (26 weeks, no text under 9 px, height per legend row), the theme and layout inputs, and that every committed example equals what `scripts/render_examples.py` renders from the snapshot.

`.github/workflows/ci.yml` runs three jobs on every push to `main` and every PR: `lint` (ruff, 3.13), `test` (pytest on 3.12, 3.13, 3.14), and `action`, the only job that loads `action.yml`. It runs `uses: ./` for Sagargupta16 with `${{ github.token }}`, then asserts the SVG exists, parses, and all three outputs are numbers; then runs it again with `theme: light` and `layout: compact` and asserts a 400 px card on `#ffffff`.

`ruff==0.17.1` and `pytest==9.1.1` are pinned inline in `ci.yml` because Renovate does not read `run:` text; bump them by hand. There is deliberately no `ruff.toml`: the tree passes ruff's full default ruleset.

## Entry points

- `action.yml` -- action contract: inputs and outputs, sets up Python 3.13, maps inputs to env vars, runs the script
- `github_stats_card.py` -- all logic: read inputs, paginated GraphQL fetch, stats, SVG render, fallback, `$GITHUB_OUTPUT`

## Key files

- `github_stats_card.py` -- `THEMES` (the presets), `fetch_stats` (API to stats dict), `render_card` (stats dict to SVG, via `wide_card` or `compact_card`), `main` (inputs, fallback, write, outputs)
- `examples/github-stats.svg`, `examples/gallery/*.svg` -- the README preview and gallery, rendered from `examples/stats-snapshot.json` by `scripts/render_examples.py`
- `scripts/measure.py` -- the numbers in the README "Measured" section
- `README.md` -- consumer docs; its inputs and outputs tables must match `action.yml`

## Gotchas

- Adding an input touches three places in sync: `action.yml` `inputs`, the `env` block of the `card` step (`INPUT_<NAME>`, hyphens become underscores), and `read_input("<NAME>")` in the script. The token is the exception: it arrives as `GITHUB_TOKEN`.
- Composite outputs need `value: ${{ steps.card.outputs.<name> }}` plus `id: card` on the step that writes `$GITHUB_OUTPUT`. A description alone silently resolves to an empty string, which is the bug credly-badge-readme-action shipped in its v1.0.0.
- The default accent is a special case on purpose: `deep_shade("#60a5fa")` returns the original hand-picked `#2563eb`. Any other accent derives its deep shade by scaling HLS lightness by `DEEP_LIGHTNESS` (0.79).
- Calendar levels come from `calendar_shades(accent)`: the empty-day tint, then four solid shades from the deep shade at 60% over `BG` (lifted to 3:1) up to the accent (held to 4.5:1), the two middle ones mixed evenly between. Translucent level fills were the 1.0.0 contrast bug (`#2563eb99` was 2.05:1); keep the levels solid. Default ramp: `#2459c6`, `#3872d7`, `#4c8ce9`, `#60a5fa` (3.03 to 7.53:1).
- `ensure_contrast(color, minimum, bg)` moves lightness away from `bg`: lighter on a dark background (white always passes), darker on a light one (black always passes). Language colors, the accent and each theme's hex text colors go through it in `render_card`, so `fetch_stats` still returns linguist's raw colors. Text colors are held on both `theme.bg` and `theme.card` (tiles); the title only on `bg`.
- Theme borders and empty-day fills are rgba tints on purpose: svg-forge's validator treats a solid low-contrast stroke as a graphic that needs 3:1, and these are decorative. Light themes use `LIGHT_PEAK_MIN` (7:1) for the busiest calendar level so the ramp has room above 3:1.
- The default `dark` theme with the `wide` layout must stay byte-identical to 1.3.x; any change to shared helpers (`card_head`, `tile`, `calendar_cells`, `language_block`) has to keep that. 1.3.0 broke it on purpose: every wide label went to 10.5 px (2026-10-25).
- Text floors: 10.5 px on the wide card (it reads at about 10.4 px in an 831 px README column), 9 px on compact except its 10.5 px title. At 10.5 px with the 1.2 px tracking a label takes about 7.5 px per character, so a wide tile fits 17 and the streak panel 18; check new labels against that.
- 1.0.0's default output was verified identical to `render_github` in render-svgs.py (2026-09-25). Since 1.1.0 the calendar shades and any too-dark language color differ on purpose. The profile imports a pinned copy of this script from `Sagargupta16/Sagargupta16/scripts/vendor/` (no `uses:` of this action), so a release only reaches the profile when it is copied there again.
- `REPOS` filters `privacy:PUBLIC`, so stars and languages come out the same whichever token runs it. Measured 2026-09-25: a `gh auth token` run gave 272 stars over 58 repos, matching the profile workflow's `GITHUB_TOKEN` run, while the same user token without the filter sees 65 repos and 278 stars (7 private repos).
- Card height is `300 + 20 * max(2, legend rows)`: 340 for up to six languages, then 20 px more per extra row of three. Compact is `376 + 20 * (rows - 1)` with two per row: 416 for six languages.
- No shebang on purpose: the action runs `python <script>`, and a shebang without mode 100755 in git fails ruff's `EXE001` in CI.
- Quote any `run:` value containing `:all:`. A bare `:all: ` parses as a YAML mapping and kills the workflow.
- The SVG is written with `newline="\n"`, so a run on Windows does not produce CRLF.
- The fallback catches `OSError`, `ValueError`, `KeyError`, `TypeError` and `http.client.HTTPException`. GraphQL `errors` are raised as `ValueError`, so a mistyped username keeps an old card with a warning rather than failing the run.
- `v1` is a moving major tag. After tagging `v1.x.y`, move `v1` to the same commit and update `CHANGELOG.md`.

## Repo-specific rules

- Keep the script stdlib-only. `action.yml` has no install step, so any third-party import breaks every consumer.
- The SVG stays self-contained (no scripts, external fonts or images; CSS and SMIL only), keeps `role="img"` and `aria-label`, and passes every user- or API-supplied string through `html.escape`.
- Text, calendar levels and language swatches meet WCAG contrast on `BG` (the empty-day tint and the tile borders are decorative and exempt): `TEXT_MIN` (4.5:1) for small text, `GRAPHIC_MIN` (3:1) for cells and swatches. Route any new user- or API-supplied color through `ensure_contrast`. The same floors hold on every theme's own `bg`. To check a render: `python ../svg-forge/skills/animated-svg/scripts/validate_svg.py <file> --strict-contrast --theme dark` (`--theme light` for the light presets) must report 0 errors.
- `fetch` checks `ALLOWED_HOSTS` (`https://api.github.com/` only) before `urlopen`; keep the check and the `# nosec B310` on the urlopen line.

## Usage

- In a workflow: `uses: Sagargupta16/github-stats-card-action@v1`; the consumer commits the SVG itself (see the README Quick start).
- Standalone: see Run.

## Config

- No config file. Everything flows action input -> env var -> script: `INPUT_USERNAME`, `GITHUB_TOKEN`, `INPUT_OUTPUT`, `INPUT_THEME`, `INPUT_LAYOUT`, `INPUT_ACCENT`, `INPUT_TITLE`, `INPUT_LANGUAGES`, `INPUT_EXCLUDE_REPOS`.
