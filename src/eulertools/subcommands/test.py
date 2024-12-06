import sys
from collections.abc import Sequence

from pyutilkit.term import SGROutput

from eulertools.lib.constants import CaseResult, ParseResult, Prefix
from eulertools.lib.utils import Language, Problem, Summary
from eulertools.subcommands.run import Run


class Test:
    __slots__ = (
        "extra",
        "languages",
        "problems",
        "success",
        "times",
        "verbosity",
    )

    def __init__(
        self,
        languages: list[Language],
        problems: list[Problem],
        times: int,
        verbosity: int,
        extra: Sequence[str] = (),
    ) -> None:
        self.success = True
        self.languages = languages
        self.problems = problems
        self.times = times
        self.verbosity = verbosity
        self.extra = extra

    def run(self) -> None:
        runner = Run(
            self.languages,
            self.problems,
            verbosity=self.verbosity,
            times=self.times,
            extra=self.extra,
        )
        for language, problem, summary in runner.get_summaries(
            self.languages, self.problems
        ):
            if not summary.success(language, problem):
                self.success = False
            self._print_summary(language, problem, summary)
        if not self.success:
            sys.exit(81)

    def _print_summary(
        self, language: Language, problem: Problem, summary: Summary
    ) -> None:
        problem_summary = summary.problems[problem]
        parse_result = problem_summary.result[language]
        if parse_result == ParseResult.FAILURE:
            SGROutput(
                [
                    Prefix.FAILURE,
                    f"Testing {language.name} // {problem.id}...",
                    "Failed to parse results",
                ],
                is_error=True,
            ).print()
            return
        for case_id, case_summary in sorted(problem_summary.cases.items()):
            case_key = case_id.case_key
            result = case_summary.result[language]
            test_text = f"Testing {language.name} // {problem.id} // {case_key}... "
            answer = case_summary.answer
            try:
                new_answers = case_summary.new_answers[language]
            except KeyError:
                new_answer = None
            else:
                new_answer = next(iter(new_answers))
            if result == CaseResult.MISSING_KEY:
                SGROutput([Prefix.FAILURE, test_text, "Missing answer"], is_error=True)
            elif case_summary.result[language] == CaseResult.NON_DETERMINISTIC:
                SGROutput(
                    [Prefix.FAILURE, test_text, "Not deterministic answer"],
                    is_error=True,
                )
            elif case_summary.result[language] == CaseResult.NEW_RESPONSE:
                SGROutput([Prefix.WARNING, test_text, "new response"])
            elif case_summary.result[language] == CaseResult.WRONG_RESPONSE:
                SGROutput(
                    [
                        Prefix.FAILURE,
                        test_text,
                        f"expected: `{answer}`, got: `{new_answer}`",
                    ],
                    is_error=True,
                )
            elif case_summary.result[language] == CaseResult.SUCCESS:
                SGROutput([Prefix.SUCCESS, test_text, "success"])
