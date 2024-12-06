import sys
from collections.abc import Sequence

from eulertools.lib.constants import CaseResult, ParseResult
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
            print(
                f"🔴 Testing {language.name} // {problem.id}... Failed to parse results",
                file=sys.stderr,
            )
            return
        for case_id, case_summary in sorted(problem_summary.cases.items()):
            case_key = case_id.case_key
            result = case_summary.result[language]
            test_text = f"Testing {language.name} // {problem.id} // {case_key}..."
            answer = case_summary.answer
            try:
                new_answers = case_summary.new_answers[language]
            except KeyError:
                new_answer = None
            else:
                new_answer = next(iter(new_answers))
            if result == CaseResult.MISSING_KEY:
                print(f"🔴 {test_text} Missing answer", file=sys.stderr)
            elif case_summary.result[language] == CaseResult.NON_DETERMINISTIC:
                print(f"🔴 {test_text} Not deterministic answer", file=sys.stderr)
            elif case_summary.result[language] == CaseResult.NEW_RESPONSE:
                print(f"🟠 {test_text} new response")
            elif case_summary.result[language] == CaseResult.WRONG_RESPONSE:
                print(
                    f"🔴 {test_text} expected: `{answer}`, got: `{new_answer}`",
                    file=sys.stderr,
                )
            elif case_summary.result[language] == CaseResult.SUCCESS:
                print(f"🟢 {test_text} success")
