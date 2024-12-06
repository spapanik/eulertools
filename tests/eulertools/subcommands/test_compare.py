import os
from unittest import mock

from eulertools.lib.utils import Language, Problem, Summary
from eulertools.subcommands.compare import Compare


@mock.patch("eulertools.subcommands.compare.get_summary", new_callable=mock.MagicMock)
def test_compare_two_languages(
    mock_get_summary: mock.MagicMock,
    summary: Summary,
    problems: list[Problem],
    languages: list[Language],
    capsys: mock.MagicMock,
) -> None:
    mock_get_summary.return_value = summary
    statement_command = Compare(languages=languages, problems=problems)

    statement_command.run()
    captured = capsys.readouterr()
    expected_output_lines = (
        "┌──────────┬──────────┬──────────┬──────────┐",
        "│ problem  │ case_key │    c     │  python  │",
        "├──────────┼──────────┼──────────┼──────────┤",
        "│    p0001 │        1 │     44ns │    662ns │",
        "│    p0001 │        2 │     48ns │    721ns │",
        "│    p0042 │        1 │      N/A │    1.4ms │",
        "└──────────┴──────────┴──────────┴──────────┘",
    )

    assert captured.out.strip() == os.linesep.join(expected_output_lines)
    assert captured.err == ""
