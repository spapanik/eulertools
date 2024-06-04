import re
from enum import StrEnum, auto, unique

ANSWER = "answer"
PROBLEM = "problem"
CASE_KEY = "case_key"
MISSING = "N/A"
NULL_STRING = "(null)"
TIME_UNIT = re.compile(r"(\d+(?:\.\d+)?)\s?(.{0,2})")


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
