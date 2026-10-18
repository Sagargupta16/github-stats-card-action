# Contributing to github-stats-card-action

This repo is a composite GitHub Action that renders a self-hosted, animated GitHub stats card as one SVG file. Bug reports, fixes, doc corrections and new inputs that come with tests are welcome.

## Setup

The script is Python standard library only and `action.yml` has no install step, so there is nothing to install. Lint and tests run with `uv`/`uvx` locally; CI uses pip with pinned versions.

## Before you open a PR

CI (`.github/workflows/ci.yml`) runs three jobs on every push to `main` and every pull request:

- `lint`: `pip install --only-binary :all: ruff==0.17.1`, then `ruff check .` on Python 3.13
- `test`: `pip install --only-binary :all: pytest==9.1.1`, then `pytest -v` on Python 3.12, 3.13 and 3.14
- `action`: runs `action.yml` from the checkout with the workflow token, then asserts the SVG exists and parses and that all three outputs are numbers

Run the first two locally:

```bash
uvx ruff@0.17.1 check .
uv run --no-project --with pytest==9.1.1 pytest -v
```

To render a card by hand, pass a token inline and never echo it:

```bash
GITHUB_TOKEN=$(gh auth token) INPUT_USERNAME=<login> INPUT_OUTPUT=card.svg python github_stats_card.py
```

Without `INPUT_OUTPUT` the script writes `assets/github-stats.svg`. Do not commit either file. If your change alters the card, regenerate the README preview with `INPUT_OUTPUT=examples/github-stats.svg` and update the render date under the preview in `README.md`.

## Conventions

- Tests live in `test_github_stats_card.py` at the repo root and never touch the network: `serve()` replaces `fetch` with canned GraphQL replies. One test parses the committed `examples/github-stats.svg`.
- A new input touches three places in sync: `inputs` in `action.yml`, the `env` block of the `card` step (`INPUT_<NAME>`, hyphens become underscores), and `read_input("<NAME>")` in the script. The token is the exception: it arrives as `GITHUB_TOKEN`.
- The README Inputs and Outputs tables must match `action.yml`.
- Composite outputs need `value: ${{ steps.card.outputs.<name> }}` plus `id: card` on the step that writes `$GITHUB_OUTPUT`. Without both, an output silently resolves to an empty string.
- Keep the script standard library only. Any third-party import breaks every consumer.
- The SVG stays self-contained (no scripts, external fonts or images; CSS and SMIL only), keeps `role="img"` and `aria-label`, and passes every user- or API-supplied string through `html.escape`.
- Text and data colors meet WCAG contrast on the card background: 4.5:1 for small text, 3:1 for calendar cells and language swatches. Pass any new user- or API-supplied color through `ensure_contrast`, and keep the contrast tests green.
- `fetch` checks `ALLOWED_HOSTS` (`https://api.github.com/` only) before `urlopen`. Keep the check and the `# nosec B310` on that line, and never print the token.
- There is no `ruff.toml` on purpose: the tree passes ruff's full default ruleset. The script has no shebang on purpose too, since a shebang without mode 100755 in git fails ruff `EXE001`.
- `ruff` and `pytest` pins in `ci.yml` are bumped by hand. Renovate does not read versions inside `run:` blocks.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`).
- `CHANGELOG.md` follows Keep a Changelog and Semantic Versioning. Add your entry under a concrete next version, for example `## [1.0.1] - YYYY-MM-DD`, with a matching link reference at the bottom.

## Security issues

Do not report vulnerabilities in public issues. Follow [SECURITY.md](SECURITY.md).

## License

This project is released under the MIT License (see [LICENSE](LICENSE)). By contributing, you agree that your contributions are licensed under it.
