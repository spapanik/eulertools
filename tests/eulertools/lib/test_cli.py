from unittest import mock

import pytest

from eulertools.lib.cli import parse_args


@pytest.mark.parametrize(
    ("subcommand", "verbose", "expected_command", "expected_verbosity"),
    [
        ("test", "-v", "test", 1),
        ("run", "-vv", "run", 2),
        ("statement", "-vvvvv", "statement", 5),
    ],
)
@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_eulertools_verbose(
    subcommand: str, verbose: str, expected_command: str, expected_verbosity: int
) -> None:
    with mock.patch("sys.argv", ["euler", subcommand, verbose, "-p", "1"]):
        args = parse_args()

    assert args.subcommand == expected_command
    assert args.verbosity == expected_verbosity


@pytest.mark.parametrize(
    "subcommand",
    ["generate", "run", "time", "compare", "test", "statement"],
)
@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_eulertools(subcommand: str) -> None:
    with mock.patch("sys.argv", ["euler", subcommand]):
        args = parse_args()
    assert args.subcommand == subcommand
    assert args.verbosity == 0


@pytest.mark.parametrize(
    ("update_mode", "update", "append"),
    [("--update", True, False), ("--append", False, True)],
)
@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_eulertools_run_update_mode(
    update_mode: str, update: bool, append: bool
) -> None:
    with mock.patch("sys.argv", ["euler", "run", update_mode]):
        args = parse_args()
    assert args.update is update
    assert args.append is append
    assert args.verbosity == 0


@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_eulertools_run_with_extra_args() -> None:
    with mock.patch(
        "sys.argv",
        ["euler", "run", "-l", "rust", "-p", "python", "--", "--case", "c01"],
    ):
        args = parse_args()
    assert args.extra == ["--case", "c01"]
    assert args.verbosity == 0


@mock.patch("sys.argv", ["euler", "new_subcommand"])
@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_eulertools_unknown_subcommand() -> None:
    with pytest.raises(SystemExit, match="2"):
        parse_args()
