import re
from enum import Enum, auto, unique
from typing import cast

ANSWER = "answer"
PROBLEM = "problem"
CASE_KEY = "case_key"
MISSING = "N/A"
NULL_STRING = "(null)"
SUPPORTED_SUFFIXES = [".yaml", ".yml", ".toml", ".json"]
TIME_UNIT = re.compile(r"(\d+(?:\.\d+)?)\s?(.{0,2})")


class StrEnum(str, Enum):  # upgrade: py3.10: Import from enum
    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,  # noqa: ARG004
        count: int,  # noqa: ARG004
        last_values: list[object],  # noqa: ARG004
    ) -> str:
        return name.lower()

    def __str__(self) -> str:
        return cast("str", self.value)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, str):
            return str(self.value) == value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(str(self.value))

    def __ne__(self, value: object) -> bool:
        if isinstance(value, str):
            return not self.__eq__(value)
        return NotImplemented


@unique
class NamedArgType(StrEnum):
    NONE = auto()
    SHORT = auto()
    LONG = auto()


@unique
class UpdateMode(StrEnum):
    NONE = auto()
    APPEND = auto()
    UPDATE = auto()


@unique
class ParseResult(StrEnum):
    SUCCESS = auto()
    FAILURE = auto()


@unique
class CaseResult(StrEnum):
    SUCCESS = auto()
    NEW_RESPONSE = auto()
    WRONG_RESPONSE = auto()
    MISSING_KEY = auto()
    NON_DETERMINISTIC = auto()


@unique
class Prefix(StrEnum):
    NO_CHANGE = "🔵 "
    SUCCESS = "🟢 "
    WARNING = "🟠 "
    FAILURE = "🔴 "
