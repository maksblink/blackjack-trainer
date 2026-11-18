"""Hi-Lo running-count practice over a finite shoe."""

from dataclasses import dataclass
import random
import re

from blackjack_trainer.cards import Card
from blackjack_trainer.shoe import Shoe


def hi_lo_value(card: Card) -> int:
    if card.rank in ('2', '3', '4', '5', '6'):
        return 1
    if card.rank in ('7', '8', '9'):
        return 0
    return -1


@dataclass(frozen=True)
class CountFeedback:
    chosen: int
    expected: int

    @property
    def correct(self) -> bool:
        return self.chosen == self.expected


class CountingSession:
    """One check per card; incorrect answers never alter the actual count."""

    def __init__(self, *, seed: int | None = None, shoe: Shoe | None = None,
                 round_limit: int | None = None) -> None:
        if round_limit is not None:
            if isinstance(round_limit, bool) or not isinstance(round_limit, int):
                raise TypeError('round_limit must be an integer')
            if round_limit < 1:
                raise ValueError('round_limit must be positive')
        if shoe is not None and shoe.position != 0:
            raise ValueError('Counting practice requires an undrawn shoe')
        self.shoe = shoe if shoe is not None else Shoe(rng=random.Random(seed))
        self.round_limit = round_limit
        self.shoe_number = 1
        self.running_count = 0
        self.answered = 0
        self.correct = 0
        self.card: Card | None = None
        self.feedback: CountFeedback | None = None
        self.next_card()

    @property
    def completed(self) -> bool:
        return self.round_limit is not None and self.answered >= self.round_limit

    @property
    def accuracy(self) -> float:
        return 100 * self.correct / self.answered if self.answered else 0.0

    def next_card(self) -> bool:
        if self.completed or (self.card is not None and self.feedback is None):
            return False
        if self.shoe.remaining == 0:
            self.shoe.shuffle()
            self.shoe_number += 1
            self.running_count = 0
        self.card = self.shoe.draw()
        self.running_count += hi_lo_value(self.card)
        self.feedback = None
        return True

    def submit(self, answer: str) -> CountFeedback:
        if self.completed or self.feedback is not None:
            raise ValueError('This card has already been answered')
        if not isinstance(answer, str) or re.fullmatch(r'[+-]?[0-9]+', answer.strip()) is None:
            raise ValueError('Enter a whole number, for example -2, 0, or +3.')
        try:
            chosen = int(answer.strip())
        except ValueError as error:
            raise ValueError('Enter a shorter whole number.') from error
        self.feedback = CountFeedback(chosen, self.running_count)
        self.answered += 1
        self.correct += self.feedback.correct
        return self.feedback
