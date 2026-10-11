"""Tests for github_stats_card.py. No network: every test replaces fetch."""

from __future__ import annotations

import json
import urllib.error
import xml.dom.minidom
from pathlib import Path

import pytest

import github_stats_card as card

# 52 weeks of 0..6 plus a three-day current week whose last day (today) is empty
CALENDAR = [[0, 1, 2, 3, 4, 5, 6] for _ in range(52)] + [[1, 2, 0]]
STATS = {
    "contributions": 1234,
    "commits": 900,
    "prs": 80,
    "stars": 7,
    "followers": 42,
    "streak": 8,
    "longest": 8,
    "active_days": 314,
    "calendar": CALENDAR,
    "languages": [
        ["Python", 60.0, "#3572A5"],
        ["C++", 25.0, "#f34b7d"],
        ["Shell", 15.0, "#89e051"],
    ],
}


def repo(name: str, stars: int, *languages: tuple[str, int, str | None]) -> dict:
    edges = [
        {"size": size, "node": {"name": lang, "color": color}}
        for lang, size, color in languages
    ]
    return {"name": name, "stargazerCount": stars, "languages": {"edges": edges}}


def reply(repos: list[dict], end_cursor: str | None = None) -> dict:
    """A GraphQL reply for STATS_QUERY; a cursor means another page follows."""
    page = {"hasNextPage": end_cursor is not None, "endCursor": end_cursor}
    weeks = [
        {"contributionDays": [{"contributionCount": c} for c in week]}
        for week in CALENDAR
    ]
    return {
        "data": {
            "user": {
                "followers": {"totalCount": 42},
                "repositories": {"pageInfo": page, "nodes": repos},
                "contributionsCollection": {
                    "totalCommitContributions": 900,
                    "totalPullRequestContributions": 80,
                    "contributionCalendar": {
                        "totalContributions": 1234,
                        "weeks": weeks,
                    },
                },
            }
        }
    }


def serve(monkeypatch: pytest.MonkeyPatch, *replies: dict | Exception) -> list[dict]:
    """Replace fetch with canned replies, in order; returns the request bodies."""
    requests: list[dict] = []
    queue = list(replies)

    def fake_fetch(url: str, body: dict, token: str, timeout: int = 20) -> bytes:
        requests.append(body)
        answer = queue.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return json.dumps(answer).encode()

    monkeypatch.setattr(card, "fetch", fake_fetch)
    return requests


@pytest.fixture
def action_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """The environment action.yml gives the script, pointed at tmp_path."""
    output = tmp_path / "assets" / "github-stats.svg"
    github_output = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-value")
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setenv("INPUT_USERNAME", "octocat")
    monkeypatch.setenv("INPUT_OUTPUT", str(output))
    for name in ("ACCENT", "TITLE", "LANGUAGES", "EXCLUDE_REPOS"):
        monkeypatch.delenv(f"INPUT_{name}", raising=False)
    return output, github_output


def parse(svg: str) -> xml.dom.minidom.Element:
    return xml.dom.minidom.parseString(svg).documentElement


# ---------------------------------------------------------------- streaks


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        ([], (0, 0)),
        ([0], (0, 0)),
        ([0, 0, 0], (0, 0)),
        ([5], (1, 1)),
        ([1, 1, 1], (3, 3)),
        ([1, 0, 1, 1], (2, 2)),
        ([1, 1, 1, 1, 0, 1, 1], (2, 4)),
    ],
)
def test_streaks_current_and_longest(
    days: list[int], expected: tuple[int, int]
) -> None:
    assert card.streaks(days) == expected


def test_streaks_empty_today_does_not_break_the_streak() -> None:
    assert card.streaks([0, 1, 1, 1, 0]) == (3, 3)


def test_streaks_empty_today_and_yesterday_breaks_the_streak() -> None:
    assert card.streaks([1, 1, 1, 0, 0]) == (0, 3)


# ---------------------------------------------------------------- levels


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, 0), (1, 1), (2, 1), (3, 2), (5, 2), (6, 3), (9, 3), (10, 4), (500, 4)],
)
def test_level_counts_the_cuts_a_day_exceeds(count: int, expected: int) -> None:
    assert card.level(count, [2, 5, 9]) == expected


def test_level_zero_is_empty_even_when_cuts_are_zero() -> None:
    assert card.level(0, [0, 0, 0]) == 0


# ---------------------------------------------------------------- rendering


def test_card_is_valid_self_contained_svg() -> None:
    svg = card.render_card(STATS, "octocat", "GITHUB | @OCTOCAT", card.BLUE_LIGHT)

    root = parse(svg)

    assert root.tagName == "svg"
    assert root.getAttribute("role") == "img"
    assert "1234 contributions" in root.getAttribute("aria-label")
    for banned in ("<script", "<image", "<foreignObject", "href", "@import"):
        assert banned not in svg
    assert svg.count("http") == 1  # the xmlns, nothing fetched


def test_username_and_title_are_escaped() -> None:
    username = 'a<b&c"d'

    svg = card.render_card(STATS, username, f"GITHUB | @{username.upper()}", "#60a5fa")

    root = parse(svg)
    title = root.getElementsByTagName("text")[0].firstChild.data
    assert root.getAttribute("aria-label").startswith('GitHub stats for @a<b&c"d:')
    assert title == 'GITHUB | @A<B&C"D'
    assert "<b&c" not in svg


def test_injected_markup_stays_text() -> None:
    stats = {**STATS, "languages": [["</text><script>x</script>", 100.0, "#000000"]]}

    svg = card.render_card(stats, "octocat", "</text><script>x</script>", "#60a5fa")

    assert parse(svg).getElementsByTagName("script") == []


def test_default_accent_keeps_the_blue_family() -> None:
    svg = card.render_card(STATS, "octocat", "t", card.BLUE_LIGHT)

    shades = card.calendar_shades(card.BLUE_LIGHT)
    assert shades == [card.EMPTY_DAY, "#2459c6", "#3872d7", "#4c8ce9", "#60a5fa"]
    for shade in shades:
        assert f'rx="2" fill="{shade}"' in svg
    assert 'fill="#60a5fa" font-size="10"' in svg


def test_custom_accent_drives_title_and_calendar() -> None:
    svg = card.render_card(STATS, "octocat", "t", "#f59e0b")

    assert 'fill="#f59e0b" font-size="10"' in svg
    for shade in card.calendar_shades("#f59e0b"):
        assert f'rx="2" fill="{shade}"' in svg
    assert card.calendar_shades("#f59e0b")[-1] == "#f59e0b"
    assert "#2563eb" not in svg
    assert "#60a5fa" not in svg


# ---------------------------------------------------------------- contrast

ACCENTS = ["#60a5fa", "#f59e0b", "#22c55e", "#ef4444", "#1e3a8a", "#000000", "#ffffff"]
# linguist colors that fail 3:1 on the card (CSS, Assembly, Dockerfile, black)
DARK_LANGUAGES = [
    ["CSS", 40.0, "#663399"],
    ["Assembly", 30.0, "#6E4C13"],
    ["Dockerfile", 20.0, "#384d54"],
    ["Mystery", 10.0, "#000000"],
]


@pytest.mark.parametrize(
    ("a", "b", "ratio"),
    [
        ("#ffffff", "#000000", 21.0),
        ("#000000", "#000000", 1.0),
        ("#777777", "#ffffff", 4.48),
    ],
)
def test_contrast_matches_wcag_reference_values(a: str, b: str, ratio: float) -> None:
    assert card.contrast(a, b) == pytest.approx(ratio, abs=0.005)


def test_ensure_contrast_keeps_a_color_that_passes() -> None:
    assert card.ensure_contrast("#3572A5", card.GRAPHIC_MIN) == "#3572A5"


def test_ensure_contrast_lifts_a_failing_color_to_the_nearest_lighter_shade() -> None:
    lifted = card.ensure_contrast("#663399", card.GRAPHIC_MIN)

    assert card.contrast("#663399") < card.GRAPHIC_MIN <= card.contrast(lifted)
    assert lifted == "#7d3fbc"  # same purple hue, 0.06 lighter


@pytest.mark.parametrize("accent", ACCENTS)
def test_every_calendar_level_reaches_3_to_1_and_busier_is_brighter(
    accent: str,
) -> None:
    empty, *levels = card.calendar_shades(accent)

    assert empty == card.EMPTY_DAY
    assert all(card.contrast(shade) >= card.GRAPHIC_MIN for shade in levels)
    lums = [card.luminance(shade) for shade in levels]
    assert lums == sorted(lums)
    assert len(set(levels)) == 4


@pytest.mark.parametrize("accent", ACCENTS)
def test_every_solid_mark_on_the_card_reaches_3_to_1(accent: str) -> None:
    stats = {**STATS, "languages": STATS["languages"] + DARK_LANGUAGES}

    root = parse(card.render_card(stats, "octocat", "t", accent))

    marks = root.getElementsByTagName("rect") + root.getElementsByTagName("circle")
    fills = {m.getAttribute("fill") for m in marks} - {"", card.BG, card.CARD}
    assert fills - {card.EMPTY_DAY}
    for fill in fills - {card.EMPTY_DAY}:
        assert card.HEX_COLOR.fullmatch(fill), fill
        assert card.contrast(fill) >= card.GRAPHIC_MIN, fill


@pytest.mark.parametrize("accent", ACCENTS)
def test_title_reaches_4_5_to_1_for_any_accent(accent: str) -> None:
    root = parse(card.render_card(STATS, "octocat", "t", accent))

    title = root.getElementsByTagName("text")[0].getAttribute("fill")
    assert card.contrast(title) >= card.TEXT_MIN


def test_deep_shade_is_a_darker_hex_color() -> None:
    deep = card.deep_shade("#f59e0b")

    assert card.HEX_COLOR.fullmatch(deep)
    assert sum(int(deep[i : i + 2], 16) for i in (1, 3, 5)) < 0xF5 + 0x9E + 0x0B


@pytest.mark.parametrize(
    ("count", "height"), [(1, 340), (6, 340), (7, 360), (9, 360), (12, 380)]
)
def test_card_grows_one_row_per_three_extra_languages(count: int, height: int) -> None:
    stats = {**STATS, "languages": [[f"L{i}", 1.0, "#000000"] for i in range(count)]}

    root = parse(card.render_card(stats, "octocat", "t", "#60a5fa"))

    assert root.getAttribute("height") == str(height)


# ---------------------------------------------------------------- fetching


def test_fetch_stats_pages_through_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = reply([repo("one", 3, ("Python", 100, "#3572A5"))], end_cursor="c1")
    second = {
        "data": {
            "user": {
                "repositories": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [repo("two", 4, ("Python", 50, "#3572A5"))],
                }
            }
        }
    }
    requests = serve(monkeypatch, first, second)

    stats = card.fetch_stats("octocat", "t", 6, set())

    assert stats["stars"] == 7
    assert requests[1]["variables"] == {"login": "octocat", "cursor": "c1"}
    assert requests[1]["query"] == card.REPOS_QUERY


def test_fetch_stats_skips_excluded_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    serve(
        monkeypatch,
        reply(
            [
                repo("Keep", 5, ("Python", 100, "#3572A5")),
                repo("dotfiles", 50, ("Shell", 900, "#89e051")),
            ]
        ),
    )

    stats = card.fetch_stats(
        "octocat", "t", 6, card.parse_exclude(" octocat/Dotfiles , ")
    )

    assert stats["stars"] == 5
    assert [name for name, _, _ in stats["languages"]] == ["Python"]


def test_fetch_stats_ranks_languages_across_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    serve(
        monkeypatch,
        reply(
            [
                repo("a", 0, ("Go", 500, "#00ADD8"), ("Shell", 100, "#89e051")),
                repo("b", 0, ("Python", 300, "#3572A5"), ("Go", 100, "#00ADD8")),
            ]
        ),
    )

    stats = card.fetch_stats("octocat", "t", 2, set())

    assert stats["languages"] == [["Go", 60.0, "#00ADD8"], ["Python", 30.0, "#3572A5"]]


@pytest.mark.parametrize("color", [None, "", "red", '#fff"/><script>'])
def test_fetch_stats_replaces_a_missing_or_odd_language_color(
    monkeypatch: pytest.MonkeyPatch, color: str | None
) -> None:
    serve(monkeypatch, reply([repo("a", 0, ("Mystery", 10, color))]))

    stats = card.fetch_stats("octocat", "t", 6, set())

    assert stats["languages"] == [["Mystery", 100.0, card.UNKNOWN_LANGUAGE_COLOR]]


def test_fetch_stats_reads_the_calendar(monkeypatch: pytest.MonkeyPatch) -> None:
    serve(monkeypatch, reply([]))

    stats = card.fetch_stats("octocat", "t", 6, set())

    assert (stats["streak"], stats["longest"], stats["active_days"]) == (8, 8, 314)
    assert stats["calendar"] == CALENDAR
    assert stats["languages"] == []


def test_graphql_errors_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    serve(
        monkeypatch,
        {
            "data": {"user": None},
            "errors": [{"message": "Could not resolve to a User"}],
        },
    )

    with pytest.raises(ValueError, match="Could not resolve to a User"):
        card.fetch_stats("nobody", "t", 6, set())


@pytest.mark.parametrize(
    "url",
    [
        "http://api.github.com/graphql",
        "https://api.github.com.evil.example/graphql",
        "https://example.com/graphql",
        "file:///etc/passwd",
    ],
)
def test_fetch_refuses_urls_outside_the_allowlist(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("urlopen must not be reached")

    monkeypatch.setattr(card.urllib.request, "urlopen", no_network)

    with pytest.raises(ValueError, match="refusing to fetch"):
        card.fetch(url, {}, "t")


# ---------------------------------------------------------------- main


def test_main_writes_the_card_and_the_outputs(
    action_env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    output, github_output = action_env
    serve(monkeypatch, reply([repo("a", 3, ("Python", 10, "#3572A5")), repo("b", 4)]))

    card.main()

    root = parse(output.read_text(encoding="utf-8"))
    assert root.getElementsByTagName("text")[0].firstChild.data == "GITHUB | @OCTOCAT"
    assert (
        github_output.read_text(encoding="utf-8")
        == "contributions=1234\nstreak=8\nstars=7\n"
    )


def test_main_keeps_the_existing_card_when_the_api_fails(
    action_env: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output, github_output = action_env
    output.parent.mkdir(parents=True)
    output.write_text("<svg>previous</svg>", encoding="utf-8")
    serve(monkeypatch, urllib.error.URLError("temporary failure"))

    card.main()

    assert output.read_text(encoding="utf-8") == "<svg>previous</svg>"
    assert "::warning::" in capsys.readouterr().out
    assert not github_output.exists()


def test_main_keeps_the_existing_card_on_graphql_errors(
    action_env: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output, _ = action_env
    output.parent.mkdir(parents=True)
    output.write_text("<svg>previous</svg>", encoding="utf-8")
    serve(monkeypatch, {"errors": [{"message": "Something went wrong"}]})

    card.main()

    assert output.read_text(encoding="utf-8") == "<svg>previous</svg>"
    assert "Something went wrong" in capsys.readouterr().out


def test_main_exits_1_when_the_api_fails_and_there_is_no_card(
    action_env: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output, _ = action_env
    serve(
        monkeypatch,
        urllib.error.HTTPError(
            "https://api.github.com/graphql", 502, "Bad Gateway", {}, None
        ),
    )

    with pytest.raises(SystemExit) as exc:
        card.main()

    assert exc.value.code == 1
    assert not output.exists()
    assert "does not exist yet" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ACCENT", "blue"),
        ("ACCENT", "#60a5f"),
        ("LANGUAGES", "0"),
        ("LANGUAGES", "six"),
        ("LANGUAGES", "-1"),
        ("USERNAME", ""),
    ],
)
def test_main_rejects_bad_inputs_before_calling_the_api(
    action_env: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(f"INPUT_{name}", value)
    requests = serve(monkeypatch)

    with pytest.raises(SystemExit) as exc:
        card.main()

    assert exc.value.code == 1
    assert requests == []


def test_main_rejects_a_missing_token(
    action_env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN")
    requests = serve(monkeypatch)

    with pytest.raises(SystemExit):
        card.main()

    assert requests == []


@pytest.mark.parametrize("value", ["f59e0b", "#F59E0B"])
def test_main_accepts_an_accent_with_or_without_the_hash(
    action_env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    output, _ = action_env
    monkeypatch.setenv("INPUT_ACCENT", value)
    serve(monkeypatch, reply([]))

    card.main()

    assert 'fill="#f59e0b" font-size="10"' in output.read_text(encoding="utf-8")


def test_main_never_prints_the_token(
    action_env: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    serve(
        monkeypatch,
        urllib.error.URLError("down"),
        reply([]),
        urllib.error.URLError("down"),
    )

    with pytest.raises(SystemExit):
        card.main()
    card.main()
    card.main()

    captured = capsys.readouterr()
    assert "test-token-value" not in captured.out + captured.err


# ---------------------------------------------------------------- example


def test_committed_example_is_valid_svg() -> None:
    example = Path(__file__).parent / "examples" / "github-stats.svg"

    root = parse(example.read_text(encoding="utf-8"))

    assert root.tagName == "svg"
    assert root.getAttribute("role") == "img"
