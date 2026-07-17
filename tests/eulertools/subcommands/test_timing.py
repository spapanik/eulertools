import subprocess
from unittest import mock

import pytest
from pyutilkit.timing import Timing

from eulertools.lib.constants import UpdateMode
from eulertools.lib.utils import CaseId, Language, Problem, Summary
from eulertools.subcommands.timing import Time


def completed_process(stdout: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout.encode(), stderr=b""
    )


@mock.patch("eulertools.subcommands.timing.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_time_with_update(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    c = languages[0]
    problem = problems[0]
    problem_summary = summary.problems[problem]
    case_3 = problem_summary.get_or_create_case(CaseId(problem=problem, case_key="3"))
    case_3.answer = "833"
    case_3.timings[c] = Timing(nanoseconds=20)
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process(
        "Time 1 100\nAnswer 1 233168\n"
        "Time 2 10\nAnswer 2 23331668\n"
        "Time 3 20\nAnswer 3 833\n"
        "Time 4 55\nAnswer 4 new\n"
    )
    time_command = Time(
        [c], [problem], times=1, verbosity=0, update_mode=UpdateMode.UPDATE
    )

    time_command.run()

    captured = capsys.readouterr()
    assert "timing changed from 44ns to 100ns" in captured.out
    assert "timing changed from 48ns to 10ns" in captured.out
    assert "timing remained unchanged at: 20ns" in captured.out
    assert "initial timing: 55ns" in captured.out
    case_1 = problem_summary.cases[CaseId(problem=problem, case_key="1")]
    case_4 = problem_summary.cases[CaseId(problem=problem, case_key="4")]
    assert case_1.timings[c] == Timing(nanoseconds=100)
    assert c not in case_4.timings
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.timing.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_time_verbose(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process(
        "Time 1 44\nTime 1 100\nTime 1 30\nAnswer 1 233168\n"
        "Time 2 10\nAnswer 2 23331668\n"
        "Time 5 7\nAnswer 5 new\n"
    )
    time_command = Time(
        languages[:1],
        problems[:1],
        times=3,
        verbosity=2,
        update_mode=UpdateMode.NONE,
    )

    time_command.run()

    captured = capsys.readouterr()
    assert "Old timing:" in captured.out
    assert "New timing:" in captured.out
    assert "Performance difference:" in captured.out
    assert "0.00%" in captured.out
    assert "79.17%" in captured.out
    assert "Detailed new timings:" in captured.out
    assert "⬆️" in captured.out
    assert "⬇️" in captured.out
    assert "↔️" in captured.out
    assert mock_update_summary.call_count == 0


@mock.patch("eulertools.subcommands.timing.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_time_verbose_without_detailed_timings(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process(
        "Time 1 44\nAnswer 1 233168\nTime 2 48\nAnswer 2 23331668\n"
    )
    time_command = Time(
        languages[:1],
        problems[:1],
        times=1,
        verbosity=1,
        update_mode=UpdateMode.NONE,
    )

    time_command.run()

    captured = capsys.readouterr()
    assert "Old timing:" in captured.out
    assert "New timing:" in captured.out
    assert "Performance difference:" in captured.out
    assert "Detailed new timings:" not in captured.out
    assert mock_update_summary.call_count == 0


@mock.patch("eulertools.subcommands.timing.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_time_with_unparsable_output(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process("unparsable\n")
    time_command = Time(
        languages[:1],
        problems[:1],
        times=1,
        verbosity=0,
        update_mode=UpdateMode.UPDATE,
    )

    with pytest.raises(SystemExit) as exc_info:
        time_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "Failed to parse results" in captured.err
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.timing.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_time_with_unsuccessful_run(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
    capsys: mock.MagicMock,
) -> None:
    c = languages[0]
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process(
        "Time 1 5\nAnswer 1 999\nTime 2 5\nAnswer 2 23331668\n"
    )
    time_command = Time(
        [c], problems[:1], times=1, verbosity=0, update_mode=UpdateMode.UPDATE
    )

    with pytest.raises(SystemExit) as exc_info:
        time_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "Unsuccessful run" in captured.err
    problem_summary = summary.problems[problems[0]]
    case_1 = problem_summary.cases[CaseId(problem=problems[0], case_key="1")]
    case_2 = problem_summary.cases[CaseId(problem=problems[0], case_key="2")]
    assert case_1.timings[c] == Timing(nanoseconds=44)
    assert case_2.timings[c] == Timing(nanoseconds=5)
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.timing.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_time_with_append_mode(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
) -> None:
    c = languages[0]
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.side_effect = [
        completed_process("Time 1 5\nAnswer 1 233168\nTime 2 5\nAnswer 2 23331668\n"),
        completed_process("Time 1 5\nAnswer 1 162\n"),
    ]
    time_command = Time(
        [c], problems, times=1, verbosity=0, update_mode=UpdateMode.APPEND
    )

    time_command.run()

    p1_summary = summary.problems[problems[0]]
    p42_summary = summary.problems[problems[1]]
    case_1 = p1_summary.cases[CaseId(problem=problems[0], case_key="1")]
    case_42 = p42_summary.cases[CaseId(problem=problems[1], case_key="1")]
    assert case_1.timings[c] == Timing(nanoseconds=44)
    assert case_42.timings[c] == Timing(nanoseconds=5)
    assert mock_update_summary.call_count == 1
