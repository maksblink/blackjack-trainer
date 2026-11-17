"""GUI interaction rules tested without importing Tkinter."""

import pytest

from blackjack_trainer.gui_controller import StrategyController
from blackjack_trainer.shoe import Shoe
from blackjack_trainer.training import StrategySession


def controller(**kwargs):
    return StrategyController(StrategySession(shoe=Shoe(shuffle=False)), **kwargs)


def test_first_hand_is_dealt():
    app = controller()
    assert app.session.question is not None
    assert app.session.shoe.position == 3
    assert app.can_answer
    assert not app.can_advance


def test_next_cannot_skip_an_unanswered_hand():
    app = controller()
    question = app.session.question
    assert not app.next_question()
    assert app.session.question is question
    assert app.session.shoe.position == 3


def test_answer_is_scored_once_then_next_is_enabled():
    app = controller()
    assert app.submit('H').correct
    assert not app.can_answer
    assert app.can_advance
    assert app.submit('S') is None
    assert app.session.answered == 1
    assert app.next_question()
    assert app.can_answer
    assert app.session.shoe.position == 6


def test_invalid_action_does_not_score():
    app = controller()
    with pytest.raises(ValueError):
        app.submit('?')
    assert app.session.answered == 0
    assert app.can_answer


def test_cancel_close_preserves_question_position_and_score():
    app = controller()
    question = app.session.question
    for _ in range(3):
        assert not app.request_close(lambda: False)
    assert not app.closed
    assert app.session.question is question
    assert app.session.shoe.position == 3
    assert app.session.answered == 0
    assert app.submit('H').correct


def test_cancel_close_after_answer_preserves_feedback():
    app = controller()
    feedback = app.submit('H')
    assert not app.request_close(lambda: False)
    assert app.session.feedback is feedback
    assert app.session.answered == 1
    assert app.can_advance


def test_accept_close_disables_actions_without_scoring():
    app = controller()
    assert app.request_close(lambda: True)
    assert app.closed
    assert not app.can_answer
    assert not app.can_advance
    assert app.submit('H') is None
    assert not app.next_question()
    assert app.session.answered == 0


def test_round_limit_keeps_final_feedback():
    app = controller(round_limit=1)
    feedback = app.submit('H')
    assert app.completed
    assert not app.can_answer
    assert not app.can_advance
    assert not app.next_question()
    assert app.session.feedback is feedback
    assert app.session.shoe.position == 3


@pytest.mark.parametrize('limit', [0, -1, 1.5, True])
def test_invalid_round_limit(limit):
    with pytest.raises(ValueError):
        controller(round_limit=limit)


def test_resuming_unanswered_question_does_not_draw_again():
    session = StrategySession()
    question = session.next_question()
    app = StrategyController(session)
    assert app.session.question is question
    assert session.shoe.position == 3


def test_existing_answers_do_not_consume_new_round_limit():
    session = StrategySession()
    session.next_question()
    session.submit('H')
    app = StrategyController(session, round_limit=1)
    assert not app.completed
    app.submit('H')
    assert app.completed
    assert session.answered == 2
