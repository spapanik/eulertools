from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

import yaml
from dj_settings import ConfigParser
from pyutilkit.timing import Timing

from eulertools.__version__ import __version__
from eulertools.lib.constants import (
    ANSWER,
    CASE_KEY,
    NULL_STRING,
    PROBLEM,
    SUPPORTED_SUFFIXES,
    CaseResult,
    NamedArgType,
    ParseResult,
)
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

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True, slots=True, order=True)
class Runner:
    path: Path
    args: tuple[str, ...]
    use_ids: bool = field(repr=False, compare=False)
    named_arg_type: NamedArgType = field(repr=False, compare=False)

    @classmethod
    def from_settings(cls, name: str) -> Self:
        project_root = _get_project_root()
        settings = get_settings()
        common = settings["languages"].get("$common", {})
        language = settings["languages"][name]
        relative_path = language.get("path", name)
        path = project_root.joinpath(relative_path)
        if common_runner := common.get("runner"):
            runner_path = project_root.joinpath(common_runner)
        else:
            runner_path = path.joinpath(language["runner"])
        runner_args = language.get("runner_args", [])
        use_ids = common.get("use_ids", True)
        named_args = common.get("named_arg_type", "none").lower()
        try:
            named_arg_type = NamedArgType[named_args.upper()]
        except KeyError:
            named_arg_type = NamedArgType.NONE
        return cls(
            path=runner_path,
            args=runner_args,
            use_ids=use_ids,
            named_arg_type=named_arg_type,
        )


@dataclass(frozen=True, slots=True, order=True)
class Language:
    name: str
    suffix: str = field(repr=False, compare=False)
    path: Path = field(repr=False, compare=False)
    solutions_path: Path = field(repr=False, compare=False)
    settings_path: Path = field(repr=False, compare=False)
    runner: Runner = field(repr=False, compare=False)

    @classmethod
    def from_settings(cls, name: str) -> Self:
        project_root = _get_project_root()
        settings = get_settings()
        project_settings_root = _get_settings_root()
        language = settings["languages"][name]
        relative_path = language.get("path", name)
        path = project_root.joinpath(relative_path)
        solutions = language.get("solutions", "src/solutions")
        settings_path = project_settings_root.joinpath(relative_path)
        extension = language.get("extension", name)
        suffix = extension if extension.startswith(".") else f".{extension}"
        return cls(
            name=name,
            suffix=suffix,
            path=path,
            runner=Runner.from_settings(name),
            solutions_path=path.joinpath(solutions),
            settings_path=settings_path,
        )


@dataclass(frozen=True, slots=True, order=True)
class Problem:
    id: str
    name: str
    statement: Path = field(repr=False)

    @classmethod
    def from_name(cls, name: str) -> Self:
        statement_dir = _get_statements_dir()
        base_path = statement_dir.joinpath(name)
        for suffix in SUPPORTED_SUFFIXES:
            path = base_path.with_suffix(suffix)
            if path.exists():
                break
        else:
            raise ProblemNotFoundError(name)
        file = statement_dir.joinpath(path)
        statement = get_statement(file)
        id_ = statement["common"].get("id", path.with_suffix("").as_posix())
        return cls(id=id_, name=name, statement=file)

    @classmethod
    def from_path(cls, path: Path, base_dir: Path) -> Self:
        relative_path = path.relative_to(base_dir)
        name = relative_path.with_suffix("").as_posix()
        return cls.from_name(name)


@dataclass(frozen=True, slots=True, order=True)
class CaseId:
    problem: Problem
    case_key: str


@dataclass(slots=True, order=True)
class Summary:
    problems: dict[Problem, ProblemSummary]

    def get_or_create_problem(self, problem: Problem) -> ProblemSummary:
        problem_summary = self.problems.get(problem)
        if problem_summary is None:
            problem_summary = ProblemSummary(problem=problem, cases={})
            self.problems[problem] = problem_summary
        return problem_summary

    def success(self, language: Language, problem: Problem) -> bool:
        problem_summary = self.problems.get(problem)
        if problem_summary is None:
            return False
        return problem_summary.success(language)


@dataclass(slots=True, order=True)
class ProblemSummary:
    problem: Problem
    cases: dict[CaseId, CaseSummary]
    result: dict[Language, ParseResult] = field(default_factory=dict, repr=False)
    parse_info: dict[Language, str] = field(default_factory=dict, repr=False)

    def get_or_create_case(self, case_id: CaseId) -> CaseSummary:
        case_summary = self.cases.get(case_id)
        if case_summary is None:
            case_summary = CaseSummary(case_id=case_id, timings={})
            self.cases[case_id] = case_summary
        return case_summary

    def as_dict(self) -> dict[str, dict[str, str | int]]:
        return {
            key: value
            for case in self.cases.values()
            for key, value in case.as_dict().items()
        }

    def success(self, language: Language) -> bool:
        if self.result.get(language) == ParseResult.FAILURE:
            return False
        return all(case.success(language) for case in self.cases.values())


@dataclass(slots=True, order=True)
class CaseSummary:
    case_id: CaseId
    answer: str | None = None
    timings: dict[Language, Timing] = field(default_factory=dict)
    result: dict[Language, CaseResult] = field(default_factory=dict, repr=False)
    new_timings: dict[Language, list[Timing]] = field(default_factory=dict, repr=False)
    new_answers: dict[Language, set[str]] = field(default_factory=dict, repr=False)

    def as_dict(self) -> dict[str, dict[str, str | int]]:
        if self.answer is None:
            info = [f"Case {self.case_id.case_key} has no answer"]
            raise InternalError(info)
        return {
            self.case_id.case_key: {
                ANSWER: self.answer,
                **{
                    language.name: timing.nanoseconds
                    for language, timing in self.timings.items()
                },
            }
        }

    def success(self, language: Language) -> bool:
        return self.result.get(language) not in {
            CaseResult.WRONG_RESPONSE,
            CaseResult.MISSING_KEY,
            CaseResult.NON_DETERMINISTIC,
        }


@dataclass(frozen=True, slots=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version: str) -> Version:
        version = re.sub("[^.0-9].*", "", version)
        if version.endswith("."):
            version += "0"
        while version.count(".") < 2:  # noqa: PLR2004
            version += ".0"
        major, minor, patch, *_ = map(int, version.split("."))
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def _get_project_root() -> Path:
    cwd = Path.cwd().resolve()
    while not cwd.joinpath(".euler").is_dir():
        if cwd.as_posix() == "/":
            raise MissingProjectRootError(cwd)
        cwd = cwd.parent
    return cwd


def _get_settings_root() -> Path:
    return _get_project_root().joinpath(".euler")


def _get_txt_summary() -> Summary:
    summary = Summary(problems={})
    answers = _get_settings_root().joinpath("answers.txt")
    with answers.open() as file:
        for line in file:
            problem_name, case_key, answer = parse_answer_result(line.strip())
            problem = Problem.from_name(problem_name)
            problem_summary = summary.get_or_create_problem(problem)
            case_id = CaseId(problem=problem, case_key=case_key)
            summary_case = problem_summary.get_or_create_case(case_id)
            summary_case.answer = answer
    answers.unlink()

    for language in get_all_languages():
        timings = language.settings_path.joinpath("timings.txt")
        with timings.open() as file:
            for line in file:
                problem_name, case_key, timing = parse_timing_result(line.strip())
                problem = Problem.from_name(problem_name)
                case_id = CaseId(problem=problem, case_key=case_key)
                case_summary = summary.problems[problem].cases[case_id]
                case_summary.timings[language] = timing
        timings.unlink()

    return summary


def _get_csv_summary() -> Summary:
    summary = Summary(problems={})
    results_file = _get_settings_root().joinpath("results.csv")
    languages = get_all_languages()
    with results_file.open() as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            problem = Problem.from_name(row[PROBLEM])
            problem_summary = summary.get_or_create_problem(problem)
            case_id = CaseId(problem=problem, case_key=row[CASE_KEY])
            case_summary = problem_summary.get_or_create_case(case_id)
            case_summary.answer = row[ANSWER]
            for language in languages:
                timing = row.get(language.name, NULL_STRING)
                if timing != NULL_STRING:
                    case_summary.timings[language] = Timing(nanoseconds=int(timing))
    results_file.unlink()
    return summary


def _create_summary(file: Path) -> None:
    file.mkdir()
    if _get_settings_root().joinpath("answers.txt").exists():
        summary = _get_txt_summary()
    if _get_settings_root().joinpath("results.csv").exists():
        summary = _get_csv_summary()
    else:
        summary = Summary(problems={})
    update_summary(summary)


def _get_summary() -> Path:
    directory = _get_settings_root().joinpath("results")
    if not directory.exists():
        _create_summary(directory)
    return directory


def _get_statements_dir() -> Path:
    return _get_settings_root().joinpath("statements")


def _get_templates_dir() -> Path:
    return _get_settings_root().joinpath("templates")


def get_template(language: Language) -> Path:
    template_dir = _get_templates_dir()
    suffix = f"{language.suffix}.jinja"
    newest_path = template_dir.joinpath("solution").with_suffix(suffix)
    if not newest_path.exists():
        new_path = template_dir.joinpath(f"{language.name}.jinja")
        if new_path.exists():
            new_path.rename(newest_path)
        else:
            template_dir.mkdir(parents=True, exist_ok=True)
            old_path = language.settings_path.joinpath("solution.jinja")
            old_path.rename(new_path)
    return newest_path


def get_solution(language: Language, problem: Problem) -> Path:
    return language.solutions_path.joinpath(problem.name).with_suffix(language.suffix)


def get_statement(path: Path) -> dict[str, Any]:  # type: ignore[misc]
    return ConfigParser([path]).data


def get_settings() -> dict[str, Any]:  # type: ignore[misc]
    settings_root = _get_settings_root()
    base_path = _get_settings_root().joinpath("euler")
    settings = [base_path.with_suffix(suffix) for suffix in SUPPORTED_SUFFIXES]
    data = ConfigParser(settings).data
    version_string = data.get("$meta", {}).get("version")
    if version_string is None:
        raise MissingVersionError(settings_root)
    min_version = Version.from_string(data["$meta"]["version"])
    if min_version > Version.from_string(__version__):
        raise InvalidVersionError(str(min_version))
    return data


def parse_timing_result(line: str) -> tuple[str, str, Timing]:
    prefix, response_key, timing = line.split(maxsplit=2)
    return prefix, response_key, Timing(nanoseconds=int(timing) or 1)


def parse_answer_result(line: str) -> tuple[str, str, str]:
    prefix, response_key, *answers = line.split(maxsplit=2)
    try:
        answer = answers.pop()
    except IndexError:
        answer = ""
    return prefix, response_key, answer


def get_summary() -> Summary:
    results_dir = _get_summary()
    languages = get_all_languages()
    summary = Summary(problems={})
    for results_file in results_dir.rglob("*.yaml"):
        with results_file.open() as file:
            data = yaml.safe_load(file)
        problem = Problem.from_path(results_file, results_dir)
        problem_summary = summary.get_or_create_problem(problem)
        for case_key, case_info in data.items():
            case_id = CaseId(problem=problem, case_key=case_key)
            case_summary = problem_summary.get_or_create_case(case_id)
            case_summary.answer = case_info[ANSWER]
            for language in languages:
                timing = case_info.get(language.name, NULL_STRING)
                if timing != NULL_STRING:
                    case_summary.timings[language] = Timing(nanoseconds=int(timing))
    return summary


def get_context(language: Language, problem: Problem) -> dict[str, Any]:  # type: ignore[misc]
    statement = get_statement(problem.statement)
    output = {"problem": problem.id}
    output |= statement.get(language.name, {})
    return output


def update_summary(summary: Summary) -> None:
    results_dir = _get_summary()
    for problem, problem_summary in summary.problems.items():
        results_file = results_dir.joinpath(f"{problem.name}.yaml")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with results_file.open("w+") as file:
            yaml.dump(problem_summary.as_dict(), file)


def get_average(values: list[Timing]) -> Timing:
    if not values:
        return Timing()
    if len(values) >= 3:  # noqa: PLR2004
        values = sorted(values)[1:-1]
    return sum(values, start=Timing()) // len(values)


def get_all_languages() -> list[Language]:
    languages = get_settings()["languages"]
    return sorted(
        Language.from_settings(language)
        for language in languages
        if language != "$common"
    )


def get_all_problems(languages: set[str]) -> dict[str, Problem]:
    statement_dir = _get_statements_dir()
    if not languages:
        languages = {language.name for language in get_all_languages()}

    output = {}
    for file in sorted(statement_dir.rglob("*")):
        if not file.is_file():
            continue
        problem = Problem.from_path(file, statement_dir)
        statement = get_statement(file)
        if any(statement.get(language) is not None for language in languages):
            if problem.id in output:
                raise DuplicateProblemError(problem.id)
            output[problem.id] = problem

    return output


def _filter_languages(parsed_languages: set[str]) -> Iterator[Language]:
    all_languages = get_all_languages()
    if not parsed_languages:
        yield from all_languages
        return

    language_names = {language.name for language in all_languages}
    exceptions = []
    for language in parsed_languages:
        if language in language_names:
            yield Language.from_settings(language)
        else:
            exceptions.append(InvalidLanguageError(language))
    if exceptions:
        msg = "Not all languages could be parsed"
        raise ExceptionGroup(msg, exceptions)


def _filter_problems(
    parsed_problems: set[str], parsed_languages: set[str]
) -> Iterator[Problem]:
    all_problems = get_all_problems(parsed_languages)
    if not parsed_problems:
        yield from all_problems.values()
        return

    exceptions = []
    for problem in parsed_problems:
        if problem in all_problems:
            yield all_problems[problem]
        else:
            exceptions.append(InvalidProblemError(problem, parsed_languages))
    if exceptions:
        msg = "Not all problems could be parsed"
        raise ExceptionGroup(msg, exceptions)


def filter_languages(languages: set[str]) -> list[Language]:
    return sorted(_filter_languages(languages))


def filter_problems(problems: set[str], languages: set[str]) -> list[Problem]:
    return sorted(
        _filter_problems(problems, languages), key=lambda problem: problem.statement
    )


def transpose(matrix: list[list[str]]) -> list[list[str]]:
    return [list(row) for row in zip(*matrix, strict=True)]


def format_cell(string: str, cell_length: int, *, is_header: bool) -> str:
    if is_header:
        return string.center(cell_length)
    return f"{string.rjust(cell_length - 1)} "
