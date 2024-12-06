from collections.abc import Iterator

from pyutilkit.term import SGROutput

from eulertools.lib.constants import CASE_KEY, MISSING, PROBLEM
from eulertools.lib.utils import Language, Problem, format_cell, get_summary


class Compare:
    __slots__ = (
        "case_ids",
        "languages",
        "pad_length",
        "problems",
        "summary",
    )

    def __init__(self, languages: list[Language], problems: list[Problem]) -> None:
        self.languages = languages
        self.problems = problems

    def run(self) -> None:
        self._print_table(self._get_table())

    @property
    def _header(self) -> list[str]:
        return [PROBLEM, CASE_KEY, *(language.name for language in self.languages)]

    @property
    def _table_rows(self) -> Iterator[list[str]]:
        summary = get_summary()
        for problem in self.problems:
            problem_summary = summary.problems[problem]
            for case_id, case_summary in problem_summary.cases.items():
                yield [
                    case_id.problem.name,
                    case_id.case_key,
                    *(
                        str(case_summary.timings.get(language, MISSING))
                        for language in self.languages
                    ),
                ]

    def _get_table(self) -> list[list[str]]:
        return [self._header, *self._table_rows]

    def _print_table(self, table: list[list[str]]) -> None:
        n = len(self.languages) + 2
        cell_length = max(len(cell) for row in table for cell in row) + 2
        spacing = ["─" * cell_length for _ in range(n)]
        top = SGROutput(["┌", "┬".join(spacing), "┐"])
        mid = SGROutput(["├", "┼".join(spacing), "┤"])
        btm = SGROutput(["└", "┴".join(spacing), "┘"])
        top.print()
        for i, row in enumerate(table):
            if i % 4 == 1:
                mid.print()
            inner_row = "│".join(
                format_cell(item, cell_length, is_header=(i == 0)) for item in row
            )
            SGROutput(["│", inner_row, "│"]).print()
        btm.print()
