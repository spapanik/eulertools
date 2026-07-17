import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from eulertools.lib.constants import NamedArgType, UpdateMode
from eulertools.lib.utils import CaseId, Language, Problem, Runner, Summary
from eulertools.subcommands.run import Run

DEV_NULL = Path(os.devnull)


def completed_process(
    stdout: str = "", stderr: str = "", returncode: int = 0
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout.encode(), stderr=stderr.encode()
    )


@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_success(
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
    mock_subprocess_run.return_value = completed_process(
        "Time 1 100\nAnswer 1 233168\nTime 2 100\nAnswer 2 23331668\nDebug: info\n"
    )
    run_command = Run(languages[:1], problems[:1], verbosity=4, times=1)

    run_command.run()

    captured = capsys.readouterr()
    assert "response: `233168`" in captured.out
    assert "response: `23331668`" in captured.out
    assert "Debug: info" in captured.out
    assert mock_subprocess_run.call_args == mock.call(
        [DEV_NULL, "1", "1"], capture_output=True
    )


@pytest.mark.parametrize(
    ("named_arg_type", "use_ids", "expected_args"),
    [
        (NamedArgType.SHORT, True, ["-p", "42", "-t", "1"]),
        (NamedArgType.LONG, False, ["--problem", "p0042", "--times", "1"]),
    ],
)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_named_arguments(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    named_arg_type: NamedArgType,
    use_ids: bool,
    expected_args: list[str],
    summary: Summary,
    problems: list[Problem],
) -> None:
    runner = Runner(
        path=DEV_NULL, args=(), use_ids=use_ids, named_arg_type=named_arg_type
    )
    language = Language(
        name="c",
        suffix=".c",
        path=DEV_NULL,
        solutions_path=DEV_NULL,
        settings_path=DEV_NULL,
        runner=runner,
    )
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process("Answer 1 162\nTime 1 5\n")
    run_command = Run([language], problems[1:], verbosity=0, times=1)

    run_command.run()

    assert mock_subprocess_run.call_args == mock.call(
        [DEV_NULL, *expected_args], capture_output=True
    )


@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_with_failing_runner(
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
    mock_subprocess_run.return_value = completed_process(stderr="boom", returncode=1)
    run_command = Run(languages[:1], problems[:1], verbosity=4, times=1)

    with pytest.raises(SystemExit) as exc_info:
        run_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "boom" in captured.err


@mock.patch("eulertools.subcommands.run.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_with_unparsable_output(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    mock_update_summary: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = True
    mock_subprocess_run.return_value = completed_process("unparsable\n")
    run_command = Run(
        languages[:1],
        problems[:1],
        verbosity=0,
        times=1,
        update_mode=UpdateMode.UPDATE,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_command.run()

    assert exc_info.value.code == 81
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.run.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_with_wrong_response_and_update(
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
        "Time 1 5\nAnswer 1 999\nTime 2 5\nAnswer 2 23331668\n"
    )
    run_command = Run(
        languages[:1],
        problems[:1],
        verbosity=0,
        times=1,
        update_mode=UpdateMode.UPDATE,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "expected: `233168`, got: `999`" in captured.err
    case_id = CaseId(problem=problems[0], case_key="1")
    assert summary.problems[problems[0]].cases[case_id].answer == "999"
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.run.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_with_append_mode(
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
        "Time 1 5\nAnswer 1 999\nTime 3 5\nAnswer 3 7\n"
    )
    run_command = Run(
        languages[:1],
        problems[:1],
        verbosity=0,
        times=1,
        update_mode=UpdateMode.APPEND,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "Missing answer" in captured.err
    assert "new response: `7`" in captured.out
    problem_summary = summary.problems[problems[0]]
    case_1 = problem_summary.cases[CaseId(problem=problems[0], case_key="1")]
    case_3 = problem_summary.cases[CaseId(problem=problems[0], case_key="3")]
    assert case_1.answer == "233168"
    assert case_3.answer == "7"
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.run.update_summary", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_with_non_deterministic_answer(
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
        "Answer 1 a\nAnswer 1 b\nTime 1 5\nAnswer 2 23331668\nTime 2 5\n"
    )
    run_command = Run(
        languages[:1],
        problems[:1],
        verbosity=0,
        times=1,
        update_mode=UpdateMode.UPDATE,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_command.run()

    assert exc_info.value.code == 81
    captured = capsys.readouterr()
    assert "Not deterministic answer" in captured.err
    assert mock_update_summary.call_count == 1


@mock.patch("eulertools.subcommands.run.subprocess.run", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_solution", new_callable=mock.MagicMock)
@mock.patch("eulertools.subcommands.run.get_summary", new_callable=mock.MagicMock)
def test_run_skips_missing_solutions(
    mock_get_summary: mock.MagicMock,
    mock_get_solution: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    summary: Summary,
    languages: list[Language],
    problems: list[Problem],
) -> None:
    mock_get_summary.return_value = summary
    mock_get_solution.return_value.exists.return_value = False
    run_command = Run(languages, problems, verbosity=0, times=1)

    run_command.run()

    assert mock_subprocess_run.call_count == 0
