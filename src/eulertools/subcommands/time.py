import sys

from eulertools.lib.utils import (
    CaseResult,
    Language,
    ParseResult,
    Problem,
    Summary,
    UpdateMode,
    get_average,
    update_summary,
)
from eulertools.subcommands.run import Run


class Time:

    __slots__ = (
        "success",
        "languages",
        "problems",
        "times",
        "verbosity",
        "update_mode",
    )

    def __init__(
        self,
        languages: list[Language],
        problems: list[Problem],
        times: int,
        verbosity: int,
        update_mode: UpdateMode,
    ):
        self.success = True
        self.languages = languages
        self.problems = problems
        self.times = times
        self.verbosity = verbosity
        self.update_mode = update_mode

    def run(self) -> None:
        runner = Run(
            self.languages, self.problems, verbosity=self.verbosity, times=self.times
        )
        for language, problem, summary in runner.get_summaries(
            self.languages, self.problems
        ):
            if not summary.problem_successful(language, problem):
                self.success = False
            self.print_summary(language, problem, summary)
            if self.update_mode != UpdateMode.NONE:
                self.prepare_summary(language, problem, summary)
        if self.update_mode != UpdateMode.NONE:
            update_summary(summary)
        if not self.success:
            sys.exit(81)

    def print_summary(
        self, language: Language, problem: Problem, summary: Summary
    ) -> None:
        problem_summary = summary.problems[problem]
        parse_result = problem_summary.result[language]
        if parse_result == ParseResult.FAILURE:
            print(
                f"🔴 Timing {language.name} // {problem.id}... Failed to parse results",
                file=sys.stderr,
            )
            return
        for case_id, case_summary in problem_summary.cases.items():
            case_key = case_id.case_key
            time_text = f"Timing {language.name} // {problem.id} // {case_key}..."
            if case_summary.result.get(language) in {
                CaseResult.WRONG_RESPONSE,
                CaseResult.MISSING_KEY,
                CaseResult.NON_DETERMINISTIC,
            }:
                print(f"🔴 {time_text}... Unsuccessful run", file=sys.stderr)
                continue
            old_timing = case_summary.timings.get(language)
            raw_timings = case_summary.new_timings[language]
            new_timing = get_average(raw_timings)

            if old_timing is None:
                general_prefix = "🟠"
                suffix = f"initial timing: {new_timing}"
            elif old_timing > new_timing:
                general_prefix = "🟢"
                suffix = f"timing changed from {old_timing} to {new_timing}"
            elif old_timing < new_timing:
                general_prefix = "🔴"
                suffix = f"timing changed from {old_timing} to {new_timing}"
            else:
                general_prefix = "🔵"
                suffix = f"timing remained unchanged at: {new_timing}"
            print(
                f"{general_prefix} {time_text} {suffix if self.verbosity == 0 else ''}"
            )
            if self.verbosity > 0:
                prefix = "    ⏱️"
                if old_timing:
                    print(f"{prefix} Old timing: {old_timing}")
                print(f"{prefix} New timing: {new_timing}")
                if old_timing is not None:
                    old_nanoseconds = old_timing.nanoseconds
                    new_nanoseconds = new_timing.nanoseconds
                    change = 100 * (old_nanoseconds - new_nanoseconds) / old_nanoseconds
                    print(f"    {general_prefix} Performance difference: {change:.2f}%")
                if self.verbosity > 1:
                    print(f"{prefix} Detailed new timings:")
                    for i, timing in enumerate(raw_timings):
                        if old_timing is None:
                            prefix = "         "
                        elif timing > old_timing:
                            prefix = "       ⬆️"
                        elif timing < old_timing:
                            prefix = "       ⬇️"
                        else:
                            prefix = "       ↔️"
                        print(f"{prefix} Run {i + 1} took: {timing}")

    def prepare_summary(
        self, language: Language, problem: Problem, summary: Summary
    ) -> None:
        problem_summary = summary.problems[problem]
        parse_result = problem_summary.result[language]
        if parse_result == ParseResult.FAILURE:
            return

        for case_summary in problem_summary.cases.values():
            case_result = case_summary.result[language]
            if case_result in {
                CaseResult.MISSING_KEY,
                CaseResult.NON_DETERMINISTIC,
            }:
                continue
            if (
                case_result in {CaseResult.SUCCESS, CaseResult.WRONG_RESPONSE}
                and self.update_mode == UpdateMode.APPEND
            ):
                continue
            new_timing = get_average(case_summary.new_timings[language])
            case_summary.timings[language] = new_timing
