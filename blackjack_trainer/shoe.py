"""A finite shoe with explicit draws and full-shoe reshuffling."""

import random

from blackjack_trainer.cards import Card, create_deck


class ShoeExhaustedError(ValueError):
    """Raised when a requested draw exceeds the remaining cards."""


class Shoe:
    """Hold one or more decks, shuffled on creation by default.

    Inject random.Random(seed) for reproducible tests or experiments.
    Drawing never reshuffles automatically. shuffle() restores every card,
    shuffles the complete shoe, and resets the position to zero.
    """

    def __init__(self, number_of_decks: int = 6, *,
                 rng: random.Random | None = None, shuffle: bool = True) -> None:
        if isinstance(number_of_decks, bool) or not isinstance(number_of_decks, int):
            raise TypeError("number_of_decks must be an integer")
        if number_of_decks < 1:
            raise ValueError("number_of_decks must be positive")
        self._number_of_decks = number_of_decks
        self._rng = rng if rng is not None else random.Random()
        self._cards = create_deck() * number_of_decks
        self._position = 0
        if shuffle:
            self.shuffle()

    @property
    def number_of_decks(self) -> int:
        return self._number_of_decks

    @property
    def cards(self) -> tuple[Card, ...]:
        """Return an immutable snapshot of the full shoe in dealing order."""
        return tuple(self._cards)

    @property
    def position(self) -> int:
        """Index of the next undrawn card."""
        return self._position

    @property
    def remaining(self) -> int:
        return len(self._cards) - self._position

    @property
    def remaining_decks(self) -> float:
        return self.remaining / 52

    def draw(self) -> Card:
        """Draw one card or raise ShoeExhaustedError without changing state."""
        return self.draw_many(1)[0]

    def draw_many(self, count: int) -> list[Card]:
        """Draw count cards atomically; a failed draw consumes no cards."""
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError("count must be an integer")
        if count < 0:
            raise ValueError("count must not be negative")
        if count > self.remaining:
            raise ShoeExhaustedError(
                f"Cannot draw {count} cards: only {self.remaining} remain."
            )
        end = self._position + count
        drawn = self._cards[self._position:end]
        self._position = end
        return drawn

    def shuffle(self) -> None:
        """Restore and shuffle all decks, including previously drawn cards."""
        self._cards = create_deck() * self._number_of_decks
        self._rng.shuffle(self._cards)
        self._position = 0
