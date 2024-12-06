import os
from unittest import mock

from eulertools.lib.utils import Problem
from eulertools.subcommands.statement import Statement


@mock.patch(
    "eulertools.subcommands.statement.get_statement", new_callable=mock.MagicMock
)
def test_statement_with_title_and_hint(
    mock_get_statement: mock.MagicMock,
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_statement.return_value = {
        "common": {"title": "Title", "description": "Desc", "hints": ["Hint"]}
    }
    statement_command = Statement(problems=problems[:1], show_hints=True)
    statement_command.run()

    captured = capsys.readouterr()
    expected_output_lines = [
        "Title",
        "~~~~~",
        "Desc",
        "",
        "Hints for `Title`",
        "~~~~~~~~~~~~~~~~~",
        "Hint",
    ]

    assert captured.out.strip() == os.linesep.join(expected_output_lines)
    assert captured.err == ""


@mock.patch(
    "eulertools.subcommands.statement.get_statement", new_callable=mock.MagicMock
)
def test_statement_with_title_but_not_hint(
    mock_get_statement: mock.MagicMock,
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_statement.return_value = {
        "common": {"title": "Title", "description": "Desc"}
    }
    statement_command = Statement(problems=problems[:1], show_hints=True)
    statement_command.run()

    captured = capsys.readouterr()
    expected_output_lines = ["Title", "~~~~~", "Desc"]

    assert captured.out.strip() == os.linesep.join(expected_output_lines)
    assert captured.err == ""


@mock.patch(
    "eulertools.subcommands.statement.get_statement", new_callable=mock.MagicMock
)
def test_statement_without_title_but_with_hint(
    mock_get_statement: mock.MagicMock,
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_statement.return_value = {
        "common": {"description": "Desc", "hints": ["Hint"]}
    }
    statement_command = Statement(problems=problems[:1], show_hints=True)
    statement_command.run()
    captured = capsys.readouterr()
    expected_output_lines = [
        "p0001",
        "~~~~~",
        "Desc",
        "",
        "Hints for `p0001`",
        "~~~~~~~~~~~~~~~~~",
        "Hint",
    ]

    assert captured.out.strip() == os.linesep.join(expected_output_lines)
    assert captured.err == ""


@mock.patch(
    "eulertools.subcommands.statement.get_statement", new_callable=mock.MagicMock
)
def test_statement_without_title_and_hint(
    mock_get_statement: mock.MagicMock,
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_statement.return_value = {"common": {"description": "Desc"}}
    statement_command = Statement(problems=problems[:1], show_hints=True)

    statement_command.run()
    captured = capsys.readouterr()
    expected_output_lines = ["p0001", "~~~~~", "Desc"]

    assert captured.out.strip() == os.linesep.join(expected_output_lines)
    assert captured.err == ""
