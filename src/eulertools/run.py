import subprocess
import sys
from itertools import product

from eulertools.exceptions import FailedRunError
from eulertools.utils import (
    Language,
    Modes,
    Timing,
    get_answers,
    get_line_answer,
    get_line_timing,
    get_solution,
    update_answers,
)


class Run:
    def __init__(
        self,
        languages: list[Language],
        problems: list[str],
        verbosity: int,
        *,
        run_update: bool = False,
        times: int = 1,
        mode: str = Modes.RUN,
    ):
        self.languages = languages
        self.problems = problems
        self.mode = mode
        self.times = times
        self.verbosity = verbosity
        self.expected_answers = get_answers()
        self.run_update = run_update

    def run(self) -> dict[Language, dict[str, dict[int, list[Timing]]]]:
        output: dict[Language, dict[str, dict[int, list[Timing]]]] = {}
        for language, problem in product(self.languages, self.problems):
            timings = self.run_single_problem(language, problem)
            output.setdefault(language, {})[problem] = timings
        if self.run_update:
            update_answers(self.expected_answers)
        return output

    def run_single_problem(
        self, language: Language, problem: str
    ) -> dict[int, list[Timing]]:
        solution = get_solution(language, problem)
        if not solution.exists():
            return {}
        raw_output = subprocess.run(
            [language.runner, problem, str(self.times)],  # noqa: S603
            capture_output=True,
            check=True,
        )
        output = raw_output.stdout.decode()
        if self.verbosity > 3:
            print(output)
        actual_answers: dict[int, set[str]] = {}
        timings: dict[int, list[Timing]] = {}
        for line in output.splitlines():
            if line.startswith("Time"):
                _, run_id, timing = get_line_timing(line)
                timings.setdefault(run_id, []).append(timing)
            elif line.startswith("Answer"):
                _, run_id, answer = get_line_answer(line)
                actual_answers.setdefault(run_id, set()).add(answer)
            else:
                print(
                    f"🔴 Running {language.name}/{problem}... Cannot parse `{line}`.",
                    file=sys.stderr,
                )
                msg = f"Unsuccessful run of {language.name}/{problem}"
                raise FailedRunError(msg)
        expected_answers = self.expected_answers.setdefault(problem, {})
        if missing_answers := {
            answer for answer in expected_answers if answer not in actual_answers
        }:
            print(
                f"🔴 Running {language.name}/{problem}... Missing answers with keys {missing_answers}.",
                file=sys.stderr,
            )
            msg = f"Unsuccessful run of {language.name}/{problem}"
            raise FailedRunError(msg)
        success = True
        for key, values in actual_answers.items():
            value = values.pop()
            if len(values) != 0:
                success = False
                print(
                    f"🔴 Running {language.name}/{problem}/{key}... Not deterministic answer.",
                    file=sys.stderr,
                )
            elif key not in expected_answers:
                if self.mode != Modes.TIMING:
                    print(
                        f"🟠 Running {language.name}/{problem}/{key}... new response: {value}"
                    )
                expected_answers[key] = value
            elif value != expected_answers[key]:
                success = False
                print(
                    f"🔴 Running {language.name}/{problem}/{key}... expected: {expected_answers[key]}, got: {value}",
                    file=sys.stderr,
                )
            elif self.mode != Modes.TIMING:
                print(f"🟢 Running {language.name}/{problem}/{key}... {value}")
        if not success:
            msg = f"Unsuccessful run of {language.name}/{problem}"
            raise FailedRunError(msg)
        return timings
