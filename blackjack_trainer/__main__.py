"""Command-line entry point with optional, lazily imported GUI support."""

import argparse

from blackjack_trainer import __version__
from blackjack_trainer.cli import run_cli
from blackjack_trainer.training import StrategySession


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description="Practice blackjack opening decisions in a terminal or GUI.")
    parser.add_argument("mode", nargs="?", choices=["cli", "gui"], default="cli")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--seed", type=int, help="Use a reproducible shuffle sequence")
    parser.add_argument("--rounds", type=positive_integer, help="Finish after this many answered questions")
    args = parser.parse_args()
    if args.mode == "gui":
        try:
            from blackjack_trainer.gui import launch_gui
        except ModuleNotFoundError as error:
            if error.name not in ("tkinter", "_tkinter"):
                raise
            parser.exit(2, "GUI mode requires Tkinter for the selected Python interpreter. "
                           "Check it with: python -m tkinter\n")
        try:
            launch_gui(seed=args.seed, round_limit=args.rounds)
        except RuntimeError as error:
            parser.exit(2, f"{error}\n")
    else:
        run_cli(StrategySession(seed=args.seed), round_limit=args.rounds)


if __name__ == "__main__":
    main()
