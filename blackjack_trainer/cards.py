"""Immutable playing cards and the standard 52-card deck."""

from dataclasses import dataclass

RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
SUITS = ("♠", "♥", "♦", "♣")


@dataclass(frozen=True)
class Card:
    """A rank and suit; equal cards may occur in a multi-deck shoe."""

    rank: str
    suit: str

    def __post_init__(self) -> None:
        if self.rank not in RANKS:
            raise ValueError(f"Invalid card rank: {self.rank!r}")
        if self.suit not in SUITS:
            raise ValueError(f"Invalid card suit: {self.suit!r}")

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


def create_deck() -> list[Card]:
    """Return a new, ordered 52-card deck without jokers."""
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]
