from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum, unique
from pathlib import Path
from typing import Any, Self

from dj_settings import SettingsParser

from eulertools.exceptions import (
    InvalidLanguageError,
    InvalidProblemError,
    MissingProjectRootError,
)

TIME_UNIT = re.compile(r"(\d+(?:\.\d+)?)\s?(.{0,2})")


@unique
class ANSIEscape(StrEnum):
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    FAIL = "\033[31m"
    OKGREEN = "\033[32m"
    OKBLUE = "\033[34m"
    WARNING = "\033[33m"


@unique
class Modes(StrEnum):
    TIMING = "timing"
    RUN = "run"


@dataclass(frozen=True, slots=True, order=True)
class Timing:
    time: Decimal = field(compare=False)
    unit: str = field(compare=False)
    nanoseconds: int = field(repr=False)

    @classmethod
    def from_nanoseconds(cls, nanoseconds: int) -> Self:
        if nanoseconds < 1000:
            return cls(time=Decimal(nanoseconds), unit="ns", nanoseconds=nanoseconds)
        microseconds = nanoseconds / 1000
        if microseconds < 1000:
            return cls(
                time=Decimal(f"{microseconds:.1f}"), unit="µs", nanoseconds=nanoseconds
            )
        milliseconds = microseconds / 1000
        if milliseconds < 1000:
            return cls(
                time=Decimal(f"{milliseconds:.1f}"), unit="ms", nanoseconds=nanoseconds
            )
        seconds = milliseconds / 1000
        return cls(time=Decimal(f"{seconds:.2f}"), unit="s", nanoseconds=nanoseconds)

    def __str__(self) -> str:
        return f"{self.time}{self.unit}"


@dataclass(frozen=True, slots=True, order=True)
class Language:
    name: str
    extension: str = field(repr=False, compare=False)
    path: Path = field(repr=False, compare=False)
    runner: Path = field(repr=False, compare=False)

    @classmethod
    def from_settings(cls, name: str) -> Self:
        project_root = _get_project_root()
        settings = get_settings()
        language = settings["languages"][name]
        return cls(
            name=name,
            extension=language.get("extension", name),
            path=project_root.joinpath(language.get("path", name)),
            runner=project_root.joinpath(language["runner"]),
        )

    def get_settings_root(self) -> Path:
        project_root = _get_project_root()
        project_settings_root = _get_settings_root()
        path = project_settings_root.joinpath(self.path.relative_to(project_root))
        if not path.exists():
            path.mkdir(parents=True)
        return path


def _get_project_root() -> Path:
    cwd = Path.cwd().resolve()
    while not cwd.joinpath(".euler").is_dir():
        if cwd.as_posix() == "/":
            message = f"Could not find .euler/euler.toml in {Path.cwd().resolve()} or any parent directory"
            raise MissingProjectRootError(message)
        cwd = cwd.parent
    return cwd


def _get_settings_root() -> Path:
    return _get_project_root().joinpath(".euler")


def _get_settings() -> Path:
    return _get_settings_root().joinpath("euler.toml")


def _get_answers() -> Path:
    file = _get_settings_root().joinpath("answers.txt")
    if not file.exists():
        file.touch(mode=0o644)
    return file


def _get_timings(language: Language) -> Path:
    file = language.get_settings_root().joinpath("timings.txt")
    if not file.exists():
        file.touch(mode=0o644)
    return file


def _get_statements_dir() -> Path:
    return _get_settings_root().joinpath("statements")


def _get_statement(problem: str) -> Path:
    return _get_statements_dir().joinpath(f"{problem}.toml")


def get_template(language: Language) -> Path:
    return language.get_settings_root().joinpath("solution.jinja")


def get_solution(language: Language, problem: str) -> Path:
    return language.path.joinpath("src", "solutions", f"{problem}.{language.extension}")


def get_statement(problem: str) -> dict[str, Any]:
    return SettingsParser(_get_statement(problem)).data


def get_settings() -> dict[str, Any]:
    return SettingsParser(_get_settings()).data


def get_line_timing(line: str) -> tuple[str, int, Timing]:
    prefix, run_id, timing = line.split(maxsplit=2)
    return prefix, int(run_id), Timing.from_nanoseconds(int(timing) or 1)


def get_line_answer(line: str) -> tuple[str, int, str]:
    prefix, run_id, *answers = line.split(maxsplit=2)
    try:
        answer = answers.pop()
    except IndexError:
        answer = ""
    return prefix, int(run_id), answer


def get_answers() -> dict[str, dict[int, str]]:
    answers = _get_answers()
    output: dict[str, dict[int, str]] = {}
    for line in answers.read_text().splitlines():
        problem, mode_id, answer = get_line_answer(line)
        output.setdefault(problem, {})[mode_id] = answer
    return output


def get_timings(language: Language) -> dict[str, dict[int, Timing]]:
    timings = _get_timings(language)
    output: dict[str, dict[int, Timing]] = {}
    for line in timings.read_text().splitlines():
        problem, mode_id, timing = get_line_timing(line)
        output.setdefault(problem, {})[mode_id] = timing
    return output


def get_context(language: Language, problem: str) -> dict[str, str]:
    statement = get_statement(problem)
    output = {"problem": problem}
    output |= statement.get(language.name, {})
    return output


def update_answers(answers: dict[str, dict[int, str]]) -> None:
    answers_path = _get_answers()
    with answers_path.open("w") as file:
        for problem in sorted(answers):
            for key in sorted(answers[problem]):
                answer = answers[problem][key]
                file.write(f"{problem} {key} {answer}\n")


def update_timings(language: Language, timings: dict[str, dict[int, Timing]]) -> None:
    timings_path = _get_timings(language)
    with timings_path.open("w") as file:
        for problem in sorted(timings):
            for key in sorted(timings[problem]):
                timing = timings[problem][key]
                file.write(f"{problem} {key} {timing.nanoseconds}\n")


def get_average(values: list[Timing]) -> Timing:
    if len(values) >= 3:
        values = sorted(values)[1:-1]
    average_ns = sum(value.nanoseconds for value in values) // len(values)
    return Timing.from_nanoseconds(average_ns)


def get_all_languages() -> list[Language]:
    languages = get_settings()["languages"]
    return sorted(Language.from_settings(language) for language in languages)


def get_all_problems(languages: list[Language] | None = None) -> list[str]:
    statement_dir = _get_statements_dir()
    if languages is None:
        languages = get_all_languages()
    return sorted(
        file.stem
        for file in statement_dir.iterdir()
        if any(
            get_statement(file.stem).get(language.name) is not None
            for language in languages
        )
    )


def get_all_keyed_problems() -> list[tuple[str, int]]:
    output = [
        (problem, key)
        for problem, problem_info in get_answers().items()
        for key in problem_info
    ]
    return sorted(output)


def filter_languages(parsed_languages: list[str] | None) -> list[Language]:
    all_languages = get_all_languages()
    if parsed_languages is None:
        return all_languages
    filtered_languages = []
    language_names = {language.name for language in all_languages}
    for language in parsed_languages:
        if language not in language_names:
            msg = f"{language} is not a valid language"
            raise InvalidLanguageError(msg)
        filtered_languages.append(Language.from_settings(language))
    return filtered_languages


def filter_problems(
    parsed_problems: list[str], languages: list[Language] | None = None
) -> list[str]:
    all_problems = get_all_problems(languages)
    if not parsed_problems:
        return sorted(all_problems)
    filtered_problems = []
    for problem in parsed_problems:
        if problem not in all_problems:
            if languages is None:
                msg = f"{problem} is not a valid problem for any language"
                raise InvalidProblemError(msg)
            msg = f"{problem} is not a valid problem for {', '.join(language.name for language in languages)}"
            raise InvalidProblemError(msg)
        filtered_problems.append(problem)
    return filtered_problems
