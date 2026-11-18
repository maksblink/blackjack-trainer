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
    parser = argparse.ArgumentParser(description="Practice blackjack basic strategy or Hi-Lo running counts.")
    parser.add_argument("mode", nargs="?", choices=["cli", "gui", "count", "count-series"], default="cli")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--seed", type=int, help="Use a reproducible shuffle sequence")
    parser.add_argument("--rounds", type=positive_integer, help="Finish after this many answered questions")
    parser.add_argument("--series-size", "-n", type=positive_integer, default=None,
                        help="Cards per series in count-series mode (default: 10)")
    args = parser.parse_args()
    if args.series_size is not None and args.mode != "count-series":
        parser.error("--series-size / -n is only available in count-series mode")
    if args.mode in ("gui", "count", "count-series"):
        try:
            if args.mode == "count-series":
                from blackjack_trainer.counting_series_gui import launch_counting_series_gui as launch_gui
            elif args.mode == "count":
                from blackjack_trainer.counting_gui import launch_counting_gui as launch_gui
            else:
                from blackjack_trainer.gui import launch_gui
        except ModuleNotFoundError as error:
            if error.name == "PIL":
                parser.exit(2, "GUI modes require Pillow. Install with: python -m pip install -e .\n")
            if error.name not in ("tkinter", "_tkinter"):
                raise
            parser.exit(2, "GUI mode requires Tkinter for the selected Python interpreter. "
                           "Check it with: python -m tkinter\n")
        try:
            if args.mode == "count-series":
                launch_gui(seed=args.seed, round_limit=args.rounds,
                           series_size=args.series_size if args.series_size is not None else 10)
            else:
                launch_gui(seed=args.seed, round_limit=args.rounds)
        except RuntimeError as error:
            parser.exit(2, f"{error}\n")
    else:
        run_cli(StrategySession(seed=args.seed), round_limit=args.rounds)


if __name__ == "__main__":
    main()
