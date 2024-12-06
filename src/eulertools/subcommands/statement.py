import os

from pyutilkit.term import SGRCodes, SGROutput, SGRString

from eulertools.lib.utils import Problem, get_statement


class Statement:
    __slots__ = ("problems", "show_hints")

    def __init__(self, problems: list[Problem], *, show_hints: bool) -> None:
        self.problems = problems
        self.show_hints = show_hints

    def run(self) -> None:
        for problem in self.problems:
            self._print_statement(problem)

    def _print_statement(self, problem: Problem) -> None:
        statement = get_statement(problem.statement)["common"]
        title = statement.get("title", problem.name)
        self._print_title(title, sgr_codes=[SGRCodes.GREEN])
        SGROutput([statement["description"].strip(), os.linesep]).print()
        if self.show_hints:
            if hint := statement.get("hint"):
                self._print_title(f"Hint for `{title}`", sgr_codes=[SGRCodes.BLUE])
                SGROutput([hint.strip(), os.linesep]).print()
            elif hints := statement.get("hints"):
                self._print_title(f"Hints for `{title}`", sgr_codes=[SGRCodes.BLUE])
                SGROutput([*(hint.strip() for hint in hints), os.linesep]).print()

    @staticmethod
    def _print_title(title: str, sgr_codes: list[SGRCodes]) -> None:
        SGRString(title, params=sgr_codes).print()
        SGRString("~" * len(title), params=sgr_codes).print()
