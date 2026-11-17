"""Command-line entry point for the Blackjack Trainer."""

import argparse

from blackjack_trainer import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Blackjack basic strategy and Hi-Lo counting practice tools."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()
    print("Blackjack Trainer")
    print("Project initialized. Training modes are coming next.")


if __name__ == "__main__":
    main()
