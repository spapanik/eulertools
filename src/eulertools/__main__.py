from eulertools.lib.cli import parse_args
from eulertools.subcommands.compare import Compare
from eulertools.subcommands.generate import Generate
from eulertools.subcommands.run import Run
from eulertools.subcommands.statement import Statement
from eulertools.subcommands.test import Test
from eulertools.subcommands.timing import Time


def main() -> None:
    args = parse_args()
    match args.subcommand:
        case "generate":
            Generate(args.languages, args.problems).run()
        case "run":
            Run(
                args.languages,
                args.problems,
                args.verbosity,
                args.times,
                args.update_mode,
                args.extra,
            ).run()
        case "time":
            Time(
                args.languages,
                args.problems,
                args.times,
                args.verbosity,
                args.update_mode,
                args.extra,
            ).run()
        case "test":
            Test(
                args.languages, args.problems, args.times, args.verbosity, args.extra
            ).run()
        case "compare":
            Compare(args.languages, args.problems).run()
        case "statement":  # pragma: no branch
            Statement(args.problems, show_hints=args.show_hints).run()
