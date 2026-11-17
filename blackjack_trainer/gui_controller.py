"""Display-independent interaction rules for the strategy GUI."""

from collections.abc import Callable

from blackjack_trainer.strategy import Action
from blackjack_trainer.training import Feedback, StrategySession


class StrategyController:
    """Guard GUI actions while sharing the terminal trainer's session model."""

    def __init__(self, session: StrategySession | None = None, *,
                 round_limit: int | None = None) -> None:
        if round_limit is not None and (isinstance(round_limit, bool)
                                        or not isinstance(round_limit, int) or round_limit < 1):
            raise ValueError("round_limit must be a positive integer")
        self.session = session if session is not None else StrategySession()
        self.round_limit = round_limit
        self._initial_answers = self.session.answered
        self.closed = False
        if self.session.question is None or self.session.feedback is not None:
            self.session.next_question()

    @property
    def completed(self) -> bool:
        return (self.round_limit is not None
                and self.session.answered - self._initial_answers >= self.round_limit)

    @property
    def can_answer(self) -> bool:
        return not self.closed and not self.completed and self.session.feedback is None

    @property
    def can_advance(self) -> bool:
        return not self.closed and not self.completed and self.session.feedback is not None

    def submit(self, action: Action | str) -> Feedback | None:
        if not self.can_answer:
            return None
        return self.session.submit(action)

    def next_question(self) -> bool:
        if not self.can_advance:
            return False
        self.session.next_question()
        return True

    def request_close(self, confirm: Callable[[], bool]) -> bool:
        """Leave the session untouched when the user cancels the dialog."""
        if self.closed:
            return True
        if confirm():
            self.closed = True
            return True
        return False
