"""Command-line entry point for the Blackjack Trainer."""

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
    parser = argparse.ArgumentParser(description="Practice blackjack opening decisions in the terminal.")
    parser.add_argument("mode", nargs="?", choices=["cli"], default="cli")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--seed", type=int, help="Use a reproducible shuffle sequence")
    parser.add_argument("--rounds", type=positive_integer, help="Stop after this many answered questions")
    args = parser.parse_args()
    run_cli(StrategySession(seed=args.seed), round_limit=args.rounds)


if __name__ == "__main__":
    main()
