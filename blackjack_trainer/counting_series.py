"""Hi-Lo series practice: finite draws, hidden cards, one score per series."""

import random
import re

from blackjack_trainer.cards import Card
from blackjack_trainer.counting import CountFeedback, hi_lo_value
from blackjack_trainer.shoe import Shoe


class CountingSeriesSession:
    """The count spans series; a series never crosses a shoe boundary."""

    def __init__(self, *, series_size: int = 10, seed: int | None = None,
                 shoe: Shoe | None = None, round_limit: int | None = None) -> None:
        for name, value in (('series_size', series_size), ('round_limit', round_limit)):
            if value is None and name == 'round_limit':
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f'{name} must be an integer')
            if value < 1:
                raise ValueError(f'{name} must be positive')
        if shoe is not None and shoe.position != 0:
            raise ValueError('Counting practice requires an undrawn shoe')
        self.shoe = shoe if shoe is not None else Shoe(rng=random.Random(seed))
        self.series_size = series_size
        self.round_limit = round_limit
        self.shoe_number = 1
        self.running_count = 0
        self.answered = 0
        self.correct = 0
        self.total_cards_shown = 0
        self.checked_cards = 0
        self.streak = 0
        self.best_streak = 0
        self.total_absolute_error = 0
        self.card: Card | None = None
        self.feedback: CountFeedback | None = None
        self.phase = 'ready'
        self.start_series()

    @property
    def completed(self) -> bool:
        return self.round_limit is not None and self.answered >= self.round_limit

    @property
    def incorrect(self) -> int:
        return self.answered - self.correct

    @property
    def accuracy(self) -> float:
        return 100 * self.correct / self.answered if self.answered else 0.0

    @property
    def mean_absolute_error(self) -> float:
        return self.total_absolute_error / self.answered if self.answered else 0.0

    def start_series(self) -> bool:
        if self.completed or self.phase not in ('ready', 'feedback'):
            return False
        self.new_shoe = self.shoe.position == 0
        if self.shoe.remaining == 0:
            self.shoe.shuffle()
            self.shoe_number += 1
            self.running_count = 0
            self.new_shoe = True
        self.series_length = min(self.series_size, self.shoe.remaining)
        self.shown_in_series = 0
        self.feedback = None
        self.phase = 'showing'
        self._draw()
        return True

    def _draw(self) -> None:
        self.card = self.shoe.draw()
        self.running_count += hi_lo_value(self.card)
        self.shown_in_series += 1
        self.total_cards_shown += 1

    def advance(self) -> bool:
        """Show another card, or hide the last one and request an answer."""
        if self.phase != 'showing':
            return False
        if self.shown_in_series < self.series_length:
            self._draw()
        else:
            self.card = None
            self.phase = 'answer'
        return True

    def submit(self, answer: str) -> CountFeedback:
        if self.phase != 'answer':
            raise ValueError('Finish viewing the series before answering, and answer only once.')
        if not isinstance(answer, str) or re.fullmatch(r'[+-]?[0-9]+', answer.strip()) is None:
            raise ValueError('Enter a whole number, for example -2, 0, or +3.')
        try:
            chosen = int(answer.strip())
        except ValueError as error:
            raise ValueError('Enter a shorter whole number.') from error
        # Bound numeric input to keep error statistics finite and meaningful.
        if abs(chosen) > 1000000:
            raise ValueError('Enter a count between -1000000 and 1000000.')
        self.feedback = CountFeedback(chosen, self.running_count)
        self.answered += 1
        self.checked_cards += self.series_length
        self.correct += self.feedback.correct
        self.total_absolute_error += abs(chosen - self.running_count)
        self.streak = self.streak + 1 if self.feedback.correct else 0
        self.best_streak = max(self.best_streak, self.streak)
        self.phase = 'feedback'
        return self.feedback
