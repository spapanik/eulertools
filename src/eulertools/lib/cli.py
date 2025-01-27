import sys
from argparse import ArgumentParser, Namespace

from eulertools.__version__ import __version__
from eulertools.lib.constants import UpdateMode
from eulertools.lib.utils import filter_languages, filter_problems

sys.tracebacklimit = 0


def runner_specific(parser: ArgumentParser, default_times: int) -> None:
    parser.add_argument("-t", "--times", type=int, default=default_times)


def language_specific(parser: ArgumentParser) -> None:
    parser.add_argument("-l", "--language", nargs="*", dest="languages", default=[])


def problem_specific(parser: ArgumentParser) -> None:
    parser.add_argument("-p", "--problem", nargs="*", dest="problems", default=[])


def can_be_updated(parser: ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--append", action="store_true")
    group.add_argument("-u", "--update", action="store_true")


def update_mode(*, update: bool, append: bool) -> UpdateMode:
    if update:
        return UpdateMode.UPDATE
    if append:
        return UpdateMode.APPEND

    return UpdateMode.NONE


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="eulertools", description="Competitive programming CLI"
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the version and exit",
    )

    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="increase the level of verbosity",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    generate_parser = subparsers.add_parser("generate", parents=[parent_parser])
    language_specific(generate_parser)
    problem_specific(generate_parser)

    run_parser = subparsers.add_parser("run", parents=[parent_parser])
    runner_specific(run_parser, default_times=1)
    can_be_updated(run_parser)
    language_specific(run_parser)
    problem_specific(run_parser)

    time_parser = subparsers.add_parser("time", parents=[parent_parser])
    runner_specific(time_parser, default_times=10)
    can_be_updated(time_parser)
    language_specific(time_parser)
    problem_specific(time_parser)

    compare_parser = subparsers.add_parser("compare", parents=[parent_parser])
    language_specific(compare_parser)
    problem_specific(compare_parser)

    test_parser = subparsers.add_parser("test", parents=[parent_parser])
    runner_specific(test_parser, default_times=2)
    language_specific(test_parser)
    problem_specific(test_parser)

    statement_parser = subparsers.add_parser("statement", parents=[parent_parser])
    statement_parser.add_argument("-s", "--show-hints", action="store_true")
    problem_specific(statement_parser)

    args, extra = parser.parse_known_args()
    if args.verbosity > 0:
        sys.tracebacklimit = 1000
    if hasattr(args, "update") and hasattr(args, "append"):
        args.update_mode = update_mode(update=args.update, append=args.append)
    if hasattr(args, "languages"):
        parsed_problems = set(args.problems)
        parsed_languages = set(args.languages)
        args.problems = filter_problems(parsed_problems, parsed_languages)
        args.languages = filter_languages(parsed_languages)
    elif hasattr(args, "problems"):  # pragma: no branch
        parsed_problems = set(args.problems)
        args.problems = filter_problems(parsed_problems, set())
    if extra and extra[0] == "--":
        extra = extra[1:]
    args.extra = extra

    return args
