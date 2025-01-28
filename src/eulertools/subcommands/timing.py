import sys
from collections.abc import Sequence

from pyutilkit.term import SGROutput

from eulertools.lib.constants import CaseResult, ParseResult, Prefix, UpdateMode
from eulertools.lib.utils import Language, Problem, Summary, get_average, update_summary
from eulertools.subcommands.run import Run


class Time:
    __slots__ = (
        "extra",
        "languages",
        "problems",
        "success",
        "times",
        "update_mode",
        "verbosity",
    )

    def __init__(
        self,
        languages: list[Language],
        problems: list[Problem],
        times: int,
        verbosity: int,
        update_mode: UpdateMode,
        extra: Sequence[str] = (),
    ) -> None:
        self.success = True
        self.languages = languages
        self.problems = problems
        self.times = times
        self.verbosity = verbosity
        self.update_mode = update_mode
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
            if self.update_mode != UpdateMode.NONE:
                self._prepare_summary(language, problem, summary)
        if self.update_mode != UpdateMode.NONE:
            update_summary(summary)
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
                    f"Timing {language.name} // {problem.id}... ",
                    "Failed to parse results",
                ],
                is_error=True,
            ).print()
            return
        for case_id, case_summary in problem_summary.cases.items():
            case_key = case_id.case_key
            time_text = f"Timing {language.name} // {problem.id} // {case_key}... "
            if case_summary.result.get(language) in {
                CaseResult.WRONG_RESPONSE,
                CaseResult.MISSING_KEY,
                CaseResult.NON_DETERMINISTIC,
            }:
                SGROutput(
                    [Prefix.FAILURE, time_text, "Unsuccessful run"], is_error=True
                ).print()
                continue
            old_timing = case_summary.timings.get(language)
            raw_timings = case_summary.new_timings[language]
            new_timing = get_average(raw_timings)

            if old_timing is None:
                general_prefix = Prefix.WARNING
                suffix = f"initial timing: {new_timing}"
            elif old_timing > new_timing:
                general_prefix = Prefix.SUCCESS
                suffix = f"timing changed from {old_timing} to {new_timing}"
            elif old_timing < new_timing:
                general_prefix = Prefix.FAILURE
                suffix = f"timing changed from {old_timing} to {new_timing}"
            else:
                general_prefix = Prefix.NO_CHANGE
                suffix = f"timing remained unchanged at: {new_timing}"
            SGROutput(
                [general_prefix, time_text, suffix if self.verbosity == 0 else ""]
            ).print()
            if self.verbosity > 0:
                padding = "    "
                prefix = "⏱️ "
                if old_timing:
                    SGROutput([padding, prefix, "Old timing: ", old_timing]).print()
                SGROutput([padding, prefix, "New timing: ", new_timing]).print()
                if old_timing is not None:
                    old_nanoseconds = old_timing.nanoseconds
                    new_nanoseconds = new_timing.nanoseconds
                    change = 100 * (old_nanoseconds - new_nanoseconds) / old_nanoseconds
                    SGROutput(
                        [
                            padding,
                            general_prefix,
                            "Performance difference: ",
                            f"{change:.2f}%",
                        ]
                    ).print()
                if self.verbosity > 1:
                    SGROutput(f"{prefix} Detailed new timings:").print()
                    for i, timing in enumerate(raw_timings):
                        if old_timing is None:
                            prefix = "  "
                        elif timing > old_timing:
                            prefix = "⬆️ "
                        elif timing < old_timing:
                            prefix = "⬇️ "
                        else:
                            prefix = "↔️ "
                        SGROutput(
                            [padding * 2, prefix, f"Run {i + 1} took:", timing]
                        ).print()

    def _prepare_summary(
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
                CaseResult.WRONG_RESPONSE,
                CaseResult.NEW_RESPONSE,
            }:
                continue
            if (
                case_summary.timings.get(language)
                and self.update_mode == UpdateMode.APPEND
            ):
                continue
            new_timing = get_average(case_summary.new_timings[language])
            case_summary.timings[language] = new_timing
