from unittest import mock

import pytest

from eulertools.__main__ import main
from eulertools.subcommands.compare import Compare
from eulertools.subcommands.generate import Generate
from eulertools.subcommands.run import Run
from eulertools.subcommands.statement import Statement
from eulertools.subcommands.test import Test
from eulertools.subcommands.timing import Time


@pytest.mark.parametrize(
    ("subcommand", "command_class"),
    [
        ("compare", Compare),
        ("generate", Generate),
        ("statement", Statement),
        ("test", Test),
        ("time", Time),
    ],
)
@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_main(subcommand: str, command_class: object) -> None:
    with (
        mock.patch(
            "eulertools.__main__.parse_args",
            new=mock.MagicMock(return_value=mock.MagicMock(subcommand=subcommand)),
        ),
        mock.patch.object(command_class, "run", mock.MagicMock()) as mock_runner,
    ):
        main()
        assert mock_runner.call_count == 1
        calls = [mock.call()]
        assert mock_runner.call_args_list == calls


@mock.patch(
    "eulertools.__main__.parse_args",
    new=mock.MagicMock(return_value=mock.MagicMock(subcommand="run")),
)
@mock.patch("eulertools.subcommands.run.get_summary", new=mock.MagicMock())
@mock.patch.object(Run, "run", new_callable=mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_languages", mock.MagicMock())
@mock.patch("eulertools.lib.cli.filter_problems", mock.MagicMock())
def test_main_run(mock_runner: mock.MagicMock) -> None:
    main()
    assert mock_runner.call_count == 1
    calls = [mock.call()]
    assert mock_runner.call_args_list == calls
