import shlex
import subprocess
import sys
from collections.abc import Iterator, Sequence
from itertools import product

from pyutilkit.term import SGROutput

from eulertools.lib.constants import (
    CaseResult,
    NamedArgType,
    ParseResult,
    Prefix,
    UpdateMode,
)
from eulertools.lib.utils import (
    CaseId,
    Language,
    Problem,
    Summary,
    get_solution,
    get_summary,
    parse_answer_result,
    parse_timing_result,
    update_summary,
)


class Run:
    __slots__ = (
        "extra",
        "languages",
        "problems",
        "success",
        "summary",
        "times",
        "update_mode",
        "verbosity",
    )

    def __init__(
        self,
        languages: list[Language],
        problems: list[Problem],
        verbosity: int,
        times: int,
        update_mode: UpdateMode = UpdateMode.NONE,
        extra: Sequence[str] = (),
    ) -> None:
        self.success = True
        self.languages = languages
        self.problems = problems
        self.times = times
        self.verbosity = verbosity
        self.update_mode = update_mode
        self.summary = get_summary()
        self.extra = extra

    def run(self) -> None:
        for language, problem, _ in self.get_summaries(self.languages, self.problems):
            self._print_summary(language, problem)
            if not self.summary.success(language, problem):
                self.success = False
            if self.update_mode != UpdateMode.NONE:
                self._prepare_summary(language, problem)
        if self.update_mode != UpdateMode.NONE:
            update_summary(self.summary)
        if not self.success:
            sys.exit(81)

    def get_summaries(
        self, languages: list[Language], problems: list[Problem]
    ) -> Iterator[tuple[Language, Problem, Summary]]:
        for language, problem in product(languages, problems):
            solution = get_solution(language, problem)
            if not solution.exists():
                continue

            self._run_single_problem(language, problem)
            yield language, problem, self.summary

    def _run_single_problem(self, language: Language, problem: Problem) -> None:
        problem_summary = self.summary.get_or_create_problem(problem)
        problem_summary.result[language] = ParseResult.SUCCESS
        runner = language.runner
        problem_arg = problem.id if runner.use_ids else problem.name
        times_arg = str(self.times)
        match runner.named_arg_type:
            case NamedArgType.NONE:
                problem_args = [problem_arg]
                time_args = [times_arg]
            case NamedArgType.SHORT:
                problem_args = ["-p", problem_arg]
                time_args = ["-t", times_arg]
            case NamedArgType.LONG:
                problem_args = ["--problem", problem_arg]
                time_args = ["--times", times_arg]
        if self.verbosity > 3:  # noqa: PLR2004
            command = shlex.join(
                [
                    runner.path.as_posix(),
                    *runner.args,
                    *problem_args,
                    *time_args,
                    *self.extra,
                ]
            )
            SGROutput(["🔍 Running command:", command]).print()
        result = subprocess.run(  # noqa: PLW1510, S603
            [runner.path, *runner.args, *problem_args, *time_args, *self.extra],
            capture_output=True,
        )
        output = result.stdout.decode()
        error = result.stderr.decode()
        if self.verbosity > 3:  # noqa: PLR2004
            if output:
                SGROutput([output]).print()
            if error:
                SGROutput([error], is_error=True).print()
        if result.returncode != 0:
            problem_summary.result[language] = ParseResult.FAILURE
            problem_summary.parse_info[language] = ""
            return
        for line in output.splitlines():
            if line.startswith("Time"):
                _, case_key, timing = parse_timing_result(line)
                case_id = CaseId(problem, case_key)
                case_summary = problem_summary.get_or_create_case(case_id)
                case_summary.new_timings.setdefault(language, []).append(timing)
            elif line.startswith("Answer"):
                _, case_key, answer = parse_answer_result(line)
                case_id = CaseId(problem, case_key)
                case_summary = problem_summary.get_or_create_case(case_id)
                case_summary.new_answers.setdefault(language, set()).add(answer)
            elif line.lower().startswith("debug"):
                SGROutput(["🔍", line]).print()
            else:
                problem_summary.result[language] = ParseResult.FAILURE
                problem_summary.parse_info[language] = line
                return
        for case_summary in problem_summary.cases.values():
            new_answers = case_summary.new_answers.get(language, set())
            if len(new_answers) == 0:
                case_summary.result[language] = CaseResult.MISSING_KEY
            elif len(new_answers) > 1:
                case_summary.result[language] = CaseResult.NON_DETERMINISTIC
            elif case_summary.answer is None:
                case_summary.result[language] = CaseResult.NEW_RESPONSE
            elif case_summary.answer not in new_answers:
                case_summary.result[language] = CaseResult.WRONG_RESPONSE
            else:
                case_summary.result[language] = CaseResult.SUCCESS

    def _print_summary(self, language: Language, problem: Problem) -> None:
        problem_summary = self.summary.problems[problem]
        parse_result = problem_summary.result[language]
        if parse_result == ParseResult.FAILURE:
            parse_info = problem_summary.parse_info[language]
            SGROutput(
                [
                    Prefix.FAILURE,
                    f"Running {language.name} // {problem.id}... "
                    f"Cannot parse `{parse_info}`",
                ],
                is_error=True,
            )
            return
        for case_id, case_summary in sorted(problem_summary.cases.items()):
            case_key = case_id.case_key
            result = case_summary.result[language]
            run_text = f"Running {language.name} // {problem.id} // {case_key}... "
            answer = case_summary.answer
            try:
                new_answers = case_summary.new_answers[language]
            except KeyError:
                new_answer = None
            else:
                new_answer = next(iter(new_answers))
            if result == CaseResult.MISSING_KEY:
                SGROutput(
                    [Prefix.FAILURE, run_text, "Missing answer"], is_error=True
                ).print()
            elif case_summary.result[language] == CaseResult.NON_DETERMINISTIC:
                SGROutput(
                    [Prefix.FAILURE, run_text, "Not deterministic answer"],
                    is_error=True,
                ).print()
            elif case_summary.result[language] == CaseResult.NEW_RESPONSE:
                SGROutput(
                    [Prefix.WARNING, run_text, f"new response: `{new_answer}`"]
                ).print()
            elif case_summary.result[language] == CaseResult.WRONG_RESPONSE:
                SGROutput(
                    [
                        Prefix.FAILURE,
                        run_text,
                        f"expected: `{answer}`, got: `{new_answer}`",
                    ],
                    is_error=True,
                ).print()
            elif case_summary.result[language] == CaseResult.SUCCESS:
                SGROutput([Prefix.SUCCESS, run_text, f"response: `{answer}`"]).print()

    def _prepare_summary(self, language: Language, problem: Problem) -> None:
        problem_summary = self.summary.problems[problem]
        parse_result = problem_summary.result[language]
        if parse_result == ParseResult.FAILURE:
            return

        for case_summary in problem_summary.cases.values():
            case_result = case_summary.result[language]
            if case_result in {
                CaseResult.SUCCESS,
                CaseResult.MISSING_KEY,
                CaseResult.NON_DETERMINISTIC,
            }:
                continue
            if (
                case_result == CaseResult.WRONG_RESPONSE
                and self.update_mode == UpdateMode.APPEND
            ):
                continue
            new_answer = next(iter(case_summary.new_answers[language]))
            case_summary.answer = new_answer
