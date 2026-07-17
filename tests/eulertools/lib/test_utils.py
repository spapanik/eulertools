from pathlib import Path

import pytest
from exceptiongroup import ExceptionGroup  # upgrade: py3.10: remove import
from pyutilkit.timing import Timing

from eulertools.lib import utils
from eulertools.lib.constants import CaseResult, NamedArgType, ParseResult
from eulertools.lib.exceptions import (
    DuplicateProblemError,
    InternalError,
    InvalidLanguageError,
    InvalidProblemError,
    InvalidVersionError,
    MissingProjectRootError,
    MissingVersionError,
    ProblemNotFoundError,
)

SETTINGS = """\
$meta:
  version: "1.0"
languages:
  $common:
    named_arg_type: short
  c:
    path: c_lang
    extension: .c
    runner: run.sh
  python:
    extension: py
    runner: runner.py
    runner_args:
      - --fast
"""

SETTINGS_WITH_COMMON_RUNNER = """\
$meta:
  version: "1.0"
languages:
  $common:
    runner: runner.sh
    use_ids: false
    named_arg_type: fancy
  python:
    runner: runner.py
"""

P0001_STATEMENT = """\
common:
  id: "1"
  title: Multiples of 3 or 5
  description: Find the sum of all the multiples of 3 or 5 below 1000.
c:
  stub: solve
python:
  stub: solve
"""

P0042_STATEMENT = """\
common:
  description: Count the triangle words.
python:
  stub: solve
"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    euler = tmp_path.joinpath(".euler")
    statements = euler.joinpath("statements")
    statements.mkdir(parents=True)
    euler.joinpath("euler.yaml").write_text(SETTINGS)
    statements.joinpath("p0001.yaml").write_text(P0001_STATEMENT)
    statements.joinpath("p0042.yaml").write_text(P0042_STATEMENT)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_runner_from_settings(project: Path) -> None:
    runner = utils.Runner.from_settings("python")

    assert runner.path == project.joinpath("python", "runner.py")
    assert runner.args == ("--fast",)
    assert runner.use_ids is True
    assert runner.named_arg_type == NamedArgType.SHORT


def test_runner_from_settings_with_common_runner(project: Path) -> None:
    project.joinpath(".euler", "euler.yaml").write_text(SETTINGS_WITH_COMMON_RUNNER)

    runner = utils.Runner.from_settings("python")

    assert runner.path == project.joinpath("runner.sh")
    assert runner.args == ()
    assert runner.use_ids is False
    assert runner.named_arg_type == NamedArgType.NONE


def test_language_from_settings(project: Path) -> None:
    python = utils.Language.from_settings("python")
    c = utils.Language.from_settings("c")

    assert python.suffix == ".py"
    assert python.path == project.joinpath("python")
    assert python.solutions_path == project.joinpath("python", "src", "solutions")
    assert python.settings_path == project.joinpath(".euler", "python")
    assert c.suffix == ".c"
    assert c.path == project.joinpath("c_lang")
    assert c.settings_path == project.joinpath(".euler", "c_lang")


def test_problem_from_name(project: Path) -> None:
    problem = utils.Problem.from_name("p0001")

    assert problem.id == "1"
    assert problem.name == "p0001"
    assert problem.statement == project.joinpath(".euler", "statements", "p0001.yaml")


def test_problem_from_name_without_id(project: Path) -> None:  # noqa: ARG001
    assert utils.Problem.from_name("p0042").id == "p0042"


def test_problem_from_name_with_missing_statement(project: Path) -> None:  # noqa: ARG001
    with pytest.raises(ProblemNotFoundError):
        utils.Problem.from_name("p9999")


def test_problem_from_path(project: Path) -> None:
    statements = project.joinpath(".euler", "statements")

    problem = utils.Problem.from_path(statements.joinpath("p0001.yaml"), statements)

    assert problem.name == "p0001"


def test_summary_get_or_create_problem_is_idempotent(
    problems: list[utils.Problem],
) -> None:
    summary = utils.Summary(problems={})

    problem_summary = summary.get_or_create_problem(problems[0])

    assert summary.get_or_create_problem(problems[0]) is problem_summary


def test_summary_success_with_unknown_problem(
    problems: list[utils.Problem], languages: list[utils.Language]
) -> None:
    summary = utils.Summary(problems={})

    assert summary.success(languages[0], problems[0]) is False


def test_summary_success(
    summary: utils.Summary,
    problems: list[utils.Problem],
    languages: list[utils.Language],
) -> None:
    assert summary.success(languages[0], problems[0]) is True


def test_summary_success_with_failed_parse(
    summary: utils.Summary,
    problems: list[utils.Problem],
    languages: list[utils.Language],
) -> None:
    summary.problems[problems[0]].result[languages[0]] = ParseResult.FAILURE

    assert summary.success(languages[0], problems[0]) is False


def test_summary_success_with_wrong_response(
    summary: utils.Summary,
    problems: list[utils.Problem],
    languages: list[utils.Language],
) -> None:
    case_id = utils.CaseId(problem=problems[0], case_key="1")
    case_summary = summary.problems[problems[0]].cases[case_id]
    case_summary.result[languages[0]] = CaseResult.WRONG_RESPONSE

    assert summary.success(languages[0], problems[0]) is False


def test_problem_summary_get_or_create_case_is_idempotent(
    summary: utils.Summary, problems: list[utils.Problem]
) -> None:
    problem_summary = summary.problems[problems[0]]
    case_id = utils.CaseId(problem=problems[0], case_key="1")

    assert problem_summary.get_or_create_case(case_id) is problem_summary.cases[case_id]


def test_problem_summary_get_languages(
    summary: utils.Summary,
    problems: list[utils.Problem],
    languages: list[utils.Language],
) -> None:
    c, python = languages

    assert summary.problems[problems[0]].get_languages() == [c, c, python, python]


def test_problem_summary_populate(
    tmp_path: Path,
    problems: list[utils.Problem],
    languages: list[utils.Language],
) -> None:
    results_file = tmp_path.joinpath("p0001.yaml")
    results_file.write_text("'1':\n  answer: '233168'\n  c: 44\n  python: (null)\n")
    problem_summary = utils.ProblemSummary(problem=problems[0], cases={})

    problem_summary.populate(results_file, languages)

    case_id = utils.CaseId(problem=problems[0], case_key="1")
    case_summary = problem_summary.cases[case_id]
    assert case_summary.answer == "233168"
    assert case_summary.timings == {languages[0]: Timing(nanoseconds=44)}


def test_problem_summary_as_dict(
    summary: utils.Summary, problems: list[utils.Problem]
) -> None:
    assert summary.problems[problems[0]].as_dict() == {
        "1": {"answer": "233168", "c": 44, "python": 662},
        "2": {"answer": "23331668", "c": 48, "python": 721},
    }


def test_case_summary_as_dict_without_answer(problems: list[utils.Problem]) -> None:
    case_id = utils.CaseId(problem=problems[0], case_key="1")
    case_summary = utils.CaseSummary(case_id=case_id)

    with pytest.raises(InternalError):
        case_summary.as_dict()


@pytest.mark.parametrize(
    ("string", "expected"),
    [
        ("1.2.3", utils.Version(1, 2, 3)),
        ("1.2.3rc1", utils.Version(1, 2, 3)),
        ("1.", utils.Version(1, 0, 0)),
        ("5", utils.Version(5, 0, 0)),
        ("1.2.3.4", utils.Version(1, 2, 3)),
    ],
)
def test_version_from_string(string: str, expected: utils.Version) -> None:
    assert utils.Version.from_string(string) == expected


def test_version_str() -> None:
    assert str(utils.Version(1, 2, 3)) == "1.2.3"


def test_get_project_root_from_subdirectory(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subdir = project.joinpath("python", "src")
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)

    assert utils._get_project_root() == project


def test_get_project_root_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(MissingProjectRootError):
        utils._get_project_root()


def test_get_txt_summary(project: Path) -> None:
    euler = project.joinpath(".euler")
    euler.joinpath("answers.txt").write_text("p0001 1 233168\np0042 1\n")
    euler.joinpath("c_lang").mkdir()
    euler.joinpath("c_lang", "timings.txt").write_text("p0001 1 44\n")
    euler.joinpath("python").mkdir()
    euler.joinpath("python", "timings.txt").write_text("p0001 1 0\n")

    summary = utils._get_txt_summary()

    problem = utils.Problem.from_name("p0001")
    case_id = utils.CaseId(problem=problem, case_key="1")
    case_summary = summary.problems[problem].cases[case_id]
    c, python = utils.get_all_languages()
    assert case_summary.answer == "233168"
    assert case_summary.timings == {
        c: Timing(nanoseconds=44),
        python: Timing(nanoseconds=1),
    }
    assert not euler.joinpath("answers.txt").exists()
    assert not euler.joinpath("c_lang", "timings.txt").exists()


def test_get_csv_summary(project: Path) -> None:
    results = project.joinpath(".euler", "results.csv")
    results.write_text("problem,case_key,answer,c,python\np0001,1,233168,(null),662\n")

    summary = utils._get_csv_summary()

    problem = utils.Problem.from_name("p0001")
    case_id = utils.CaseId(problem=problem, case_key="1")
    case_summary = summary.problems[problem].cases[case_id]
    _, python = utils.get_all_languages()
    assert case_summary.answer == "233168"
    assert case_summary.timings == {python: Timing(nanoseconds=662)}
    assert not results.exists()


def test_get_summary_with_empty_project(project: Path) -> None:
    summary = utils.get_summary()

    assert summary.problems == {}
    assert project.joinpath(".euler", "results").is_dir()


def test_get_summary_migrates_txt_results(project: Path) -> None:
    euler = project.joinpath(".euler")
    euler.joinpath("answers.txt").write_text("p0001 1 233168\np0042 1\n")
    euler.joinpath("c_lang").mkdir()
    euler.joinpath("c_lang", "timings.txt").write_text("p0001 1 44\n")
    euler.joinpath("python").mkdir()
    euler.joinpath("python", "timings.txt").write_text("p0001 1 0\n")

    summary = utils.get_summary()

    problem = utils.Problem.from_name("p0001")
    case_id = utils.CaseId(problem=problem, case_key="1")
    case_summary = summary.problems[problem].cases[case_id]
    c, _ = utils.get_all_languages()
    assert case_summary.answer == "233168"
    assert case_summary.timings[c] == Timing(nanoseconds=44)
    assert euler.joinpath("results", "p0042.yaml").exists()


def test_get_summary_migrates_csv_results(project: Path) -> None:
    results = project.joinpath(".euler", "results.csv")
    results.write_text("problem,case_key,answer,c,python\np0001,1,233168,(null),662\n")

    summary = utils.get_summary()

    problem = utils.Problem.from_name("p0001")
    case_id = utils.CaseId(problem=problem, case_key="1")
    case_summary = summary.problems[problem].cases[case_id]
    _, python = utils.get_all_languages()
    assert case_summary.answer == "233168"
    assert case_summary.timings == {python: Timing(nanoseconds=662)}


def test_get_summary_with_existing_results(project: Path) -> None:
    results_dir = project.joinpath(".euler", "results")
    results_dir.mkdir()
    results_dir.joinpath("p0001.yaml").write_text("'1':\n  answer: '233168'\n  c: 44\n")

    summary = utils.get_summary()

    problem = utils.Problem.from_name("p0001")
    case_id = utils.CaseId(problem=problem, case_key="1")
    case_summary = summary.problems[problem].cases[case_id]
    c, _ = utils.get_all_languages()
    assert case_summary.answer == "233168"
    assert case_summary.timings == {c: Timing(nanoseconds=44)}


def test_get_template_with_existing_template(project: Path) -> None:
    python = utils.Language.from_settings("python")
    templates = project.joinpath(".euler", "templates")
    templates.mkdir()
    newest_path = templates.joinpath("solution.py.jinja")
    newest_path.write_text("template")

    assert utils.get_template(python) == newest_path


def test_get_template_renames_language_template(project: Path) -> None:
    python = utils.Language.from_settings("python")
    templates = project.joinpath(".euler", "templates")
    templates.mkdir()
    templates.joinpath("python.jinja").write_text("template")

    template = utils.get_template(python)

    assert template == templates.joinpath("solution.py.jinja")
    assert template.read_text() == "template"
    assert not templates.joinpath("python.jinja").exists()


def test_get_template_moves_legacy_template(project: Path) -> None:
    python = utils.Language.from_settings("python")
    python.settings_path.mkdir()
    python.settings_path.joinpath("solution.jinja").write_text("template")

    template = utils.get_template(python)

    templates = project.joinpath(".euler", "templates")
    assert template == templates.joinpath("solution.py.jinja")
    assert templates.joinpath("python.jinja").read_text() == "template"
    assert not python.settings_path.joinpath("solution.jinja").exists()


def test_get_solution(project: Path) -> None:
    python = utils.Language.from_settings("python")
    problem = utils.Problem.from_name("p0001")

    solution = utils.get_solution(python, problem)

    assert solution == project.joinpath("python", "src", "solutions", "p0001.py")


def test_get_settings_without_version(project: Path) -> None:
    project.joinpath(".euler", "euler.yaml").write_text("languages: {}\n")

    with pytest.raises(MissingVersionError):
        utils.get_settings()


def test_get_settings_with_newer_version(project: Path) -> None:
    project.joinpath(".euler", "euler.yaml").write_text(
        '$meta:\n  version: "999.0.0"\nlanguages: {}\n'
    )

    with pytest.raises(InvalidVersionError):
        utils.get_settings()


def test_get_context(project: Path) -> None:  # noqa: ARG001
    python = utils.Language.from_settings("python")
    problem = utils.Problem.from_name("p0001")

    assert utils.get_context(python, problem) == {"problem": "1", "stub": "solve"}


def test_get_context_without_language_section(project: Path) -> None:  # noqa: ARG001
    c = utils.Language.from_settings("c")
    problem = utils.Problem.from_name("p0042")

    assert utils.get_context(c, problem) == {"problem": "p0042"}


def test_update_results_file_skips_identical_content(
    tmp_path: Path, summary: utils.Summary, problems: list[utils.Problem]
) -> None:
    content = (
        '"1":\n  answer: "233168"\n  c: 44\n  python: 662\n'
        '"2":\n  answer: "23331668"\n  c: 48\n  python: 721\n'
    )
    results_file = tmp_path.joinpath("p0001.yaml")
    results_file.write_text(content)

    utils.update_results_file(results_file, summary.problems[problems[0]])

    assert results_file.read_text() == content


def test_update_results_file_writes_changed_content(
    tmp_path: Path, summary: utils.Summary, problems: list[utils.Problem]
) -> None:
    results_file = tmp_path.joinpath("p0001.yaml")
    results_file.write_text("'1':\n  answer: old\n")
    problem_summary = summary.problems[problems[0]]

    utils.update_results_file(results_file, problem_summary)

    rewritten = utils.ProblemSummary(problem=problems[0], cases={})
    rewritten.populate(results_file, problem_summary.get_languages())
    assert rewritten.as_dict() == problem_summary.as_dict()


def test_get_average_with_no_values() -> None:
    assert utils.get_average([]) == Timing()


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([1, 4, 3, 2], 2),
        ([1, 2, 3], 2),
        ([1, 2, 3, 4], 2),
        ([1, 45, 3, 34569], 24),
        ([4, 2], 3),
    ],
)
def test_get_average(values: list[int], expected: int) -> None:
    timings = [Timing(nanoseconds=value) for value in values]
    assert utils.get_average(timings) == Timing(nanoseconds=expected)


def test_get_all_languages(project: Path) -> None:  # noqa: ARG001
    languages = utils.get_all_languages()

    assert [language.name for language in languages] == ["c", "python"]


def test_get_all_problems_with_all_languages(project: Path) -> None:  # noqa: ARG001
    problems = utils.get_all_problems(set())

    assert sorted(problems) == ["1", "p0042"]


def test_get_all_problems_with_language_subset(project: Path) -> None:  # noqa: ARG001
    problems = utils.get_all_problems({"c"})

    assert sorted(problems) == ["1"]


def test_get_all_problems_with_subdirectory(project: Path) -> None:
    subdir = project.joinpath(".euler", "statements", "extra")
    subdir.mkdir()
    subdir.joinpath("p0100.yaml").write_text(P0042_STATEMENT)

    problems = utils.get_all_problems({"python"})

    assert sorted(problems) == ["1", "extra/p0100", "p0042"]


def test_get_all_problems_with_duplicate_ids(project: Path) -> None:
    statements = project.joinpath(".euler", "statements")
    statements.joinpath("p0002.yaml").write_text(P0001_STATEMENT)

    with pytest.raises(DuplicateProblemError):
        utils.get_all_problems(set())


def test_filter_languages_with_empty_set(project: Path) -> None:  # noqa: ARG001
    languages = utils.filter_languages(set())

    assert [language.name for language in languages] == ["c", "python"]


def test_filter_languages_with_subset(project: Path) -> None:  # noqa: ARG001
    languages = utils.filter_languages({"python"})

    assert [language.name for language in languages] == ["python"]


def test_filter_languages_with_invalid_language(project: Path) -> None:  # noqa: ARG001
    with pytest.raises(ExceptionGroup) as exc_info:
        utils.filter_languages({"python", "rust"})

    exceptions = exc_info.value.exceptions
    assert {type(exception) for exception in exceptions} == {InvalidLanguageError}


def test_filter_problems_with_empty_set(project: Path) -> None:  # noqa: ARG001
    problems = utils.filter_problems(set(), set())

    assert [problem.id for problem in problems] == ["1", "p0042"]


def test_filter_problems_with_subset(project: Path) -> None:  # noqa: ARG001
    problems = utils.filter_problems({"1"}, set())

    assert [problem.id for problem in problems] == ["1"]


def test_filter_problems_with_invalid_problem(project: Path) -> None:  # noqa: ARG001
    with pytest.raises(ExceptionGroup) as exc_info:
        utils.filter_problems({"1", "p9999"}, set())

    exceptions = exc_info.value.exceptions
    assert {type(exception) for exception in exceptions} == {InvalidProblemError}


def test_transpose() -> None:
    assert utils.transpose([["a", "b"], ["c", "d"]]) == [["a", "c"], ["b", "d"]]
