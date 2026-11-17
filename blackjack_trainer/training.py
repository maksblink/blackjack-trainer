"""UI-independent opening-decision practice and session statistics."""

from dataclasses import dataclass
import random

from blackjack_trainer.cards import Card
from blackjack_trainer.shoe import Shoe
from blackjack_trainer.strategy import Action, basic_strategy


@dataclass(frozen=True)
class Question:
    player_hand: tuple[Card, Card]
    dealer_upcard: Card


@dataclass(frozen=True)
class Feedback:
    chosen: Action
    recommended: Action

    @property
    def correct(self) -> bool:
        return self.chosen == self.recommended


class StrategySession:
    """Deal questions and score each answered question exactly once."""

    def __init__(self, *, seed: int | None = None, shoe: Shoe | None = None) -> None:
        self.shoe = shoe if shoe is not None else Shoe(rng=random.Random(seed))
        self.question: Question | None = None
        self.feedback: Feedback | None = None
        self.answered = 0
        self.correct = 0
        self.shoe_number = 1

    @property
    def incorrect(self) -> int:
        return self.answered - self.correct

    @property
    def accuracy(self) -> float:
        return 100.0 * self.correct / self.answered if self.answered else 0.0

    def next_question(self) -> Question:
        if self.question is not None and self.feedback is None:
            raise RuntimeError("Answer the current question before dealing another")
        if self.shoe.remaining < 3:
            self.shoe.shuffle()
            self.shoe_number += 1
        first, second, dealer = self.shoe.draw_many(3)
        self.question = Question((first, second), dealer)
        self.feedback = None
        return self.question

    def submit(self, answer: str | Action) -> Feedback:
        if self.question is None:
            raise RuntimeError("Deal a question before answering")
        if self.feedback is not None:
            raise RuntimeError("This question has already been answered")
        action = answer if isinstance(answer, Action) else Action(answer.strip().upper())
        recommended = basic_strategy(self.question.player_hand, self.question.dealer_upcard)
        self.feedback = Feedback(action, recommended)
        self.answered += 1
        self.correct += int(self.feedback.correct)
        return self.feedback
