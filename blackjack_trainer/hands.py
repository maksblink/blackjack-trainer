"""Evaluate blackjack hands independently of betting and dealer rules."""

from collections.abc import Sequence
from dataclasses import dataclass

from blackjack_trainer.cards import Card


@dataclass(frozen=True)
class HandEvaluation:
    """An immutable summary of a hand at the time of evaluation."""

    total: int
    is_soft: bool
    is_blackjack: bool
    is_bust: bool
    pair_rank: str | None


def card_value(card: Card) -> int:
    """Return the initial value of a card, treating an ace as 11."""
    if card.rank == "A":
        return 11
    if card.rank in ("10", "J", "Q", "K"):
        return 10
    return int(card.rank)


def pair_rank(cards: Sequence[Card]) -> str | None:
    """Return a two-card pair's rank, or None.

    Ten-valued cards are grouped as "10", including mixed ranks such as J/K.
    This describes the cards, not whether a table's split rules allow a split.
    """
    if len(cards) != 2:
        return None
    first, second = cards
    if card_value(first) == card_value(second) == 10:
        return "10"
    return first.rank if first.rank == second.rank else None


def evaluate_hand(cards: Sequence[Card], *, from_split: bool = False) -> HandEvaluation:
    """Choose the highest non-busting total, or the lowest total if all bust.

    A hand is soft only while an ace still counts as 11. Blackjack requires
    an unsplit two-card ace/ten combination. Pass from_split=True for a split
    hand; its 21 is not a natural blackjack. An empty hand has total zero.
    The input sequence is never modified.
    """
    total = sum(card_value(card) for card in cards)
    high_aces = sum(card.rank == "A" for card in cards)
    while total > 21 and high_aces:
        total -= 10
        high_aces -= 1
    return HandEvaluation(
        total=total,
        is_soft=high_aces > 0,
        is_blackjack=len(cards) == 2 and total == 21 and not from_split,
        is_bust=total > 21,
        pair_rank=pair_rank(cards),
    )


def hand_value(cards: Sequence[Card]) -> int:
    """Return the best blackjack total."""
    return evaluate_hand(cards).total


def is_soft(cards: Sequence[Card]) -> bool:
    """Return whether an ace currently counts as 11."""
    return evaluate_hand(cards).is_soft
