from pathlib import Path

from eulertools.lib.exceptions import (
    DuplicateProblemError,
    InternalError,
    InvalidLanguageError,
    InvalidProblemError,
    InvalidVersionError,
    MissingProjectRootError,
    MissingVersionError,
    ProblemNotFoundError,
)


def test_duplicate_problem_error() -> None:
    assert str(DuplicateProblemError("42")) == "Duplicate problem id: 42"


def test_internal_error() -> None:
    error = InternalError(["reason"])

    assert str(error) == "eulertools reached an inconsistent state. Reasons:"
    assert error.__notes__ == ["    * reason"]


def test_invalid_language_error() -> None:
    assert str(InvalidLanguageError("rust")) == "rust is not a valid language"


def test_invalid_problem_error_with_languages() -> None:
    error = InvalidProblemError("p9999", {"python", "c"})

    assert str(error) == "p9999 is not a valid problem for c, python"


def test_invalid_problem_error_without_languages() -> None:
    error = InvalidProblemError("p9999", set())

    assert str(error) == "p9999 is not a valid problem for any language"


def test_invalid_version_error() -> None:
    error = InvalidVersionError("1.2.3")

    assert str(error) == "The project requires a eulertools >= v1.2.3"


def test_missing_project_root_error() -> None:
    error = MissingProjectRootError(Path("/a/b"))

    assert str(error) == "Couldn't find a project root directory"
    assert error.__notes__ == [
        "Locations searched:",
        "    * /a/.euler",
        "    * /.euler",
    ]


def test_missing_version_error() -> None:
    error = MissingVersionError(Path("/a/.euler"))

    assert str(error) == "Config in `/a/.euler` has no version info"


def test_problem_not_found_error() -> None:
    error = ProblemNotFoundError("p9999")

    assert str(error) == "Couldn't locate problem named `p9999`"
