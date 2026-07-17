import subprocess
from unittest import mock

import pytest

from eulertools.lib.utils import Language, Problem, Summary
from eulertools.subcommands import test as test_subcommand


def completed_process(stdout: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout.encode(), stderr=b""
    )


@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_test_success(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process(
        "Answer 1 233168\nAnswer 2 23331668\n"
    )
    test_command = test_subcommand.Test(
        languages[:1], problems[:1], times=2, verbosity=0
    )

    test_command.run()

    assert mock_subprocess_run.call_count == 1


@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_test_with_failing_cases(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process(
        "Answer 1 999\nAnswer 3 7\nAnswer 4 a\nAnswer 4 b\n"
    )
    test_command = test_subcommand.Test(
        languages[:1], problems[:1], times=2, verbosity=0
    )

    with pytest.raises(SystemExit) as exc_info:
        test_command.run()

    assert exc_info.value.code == 81


@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_test_with_unparsable_output(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process("unparsable\n")
    test_command = test_subcommand.Test(
        languages[:1], problems[:1], times=2, verbosity=0
    )

    with pytest.raises(SystemExit) as exc_info:
        test_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "Failed to parse results" in captured.err
