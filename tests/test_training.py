"""Session behavior independent of terminal input and output."""

import pytest

from blackjack_trainer.shoe import Shoe
from blackjack_trainer.strategy import Action, basic_strategy
from blackjack_trainer.training import StrategySession


def test_initial_statistics():
    session = StrategySession()
    assert (session.answered, session.correct, session.incorrect, session.accuracy) == (0, 0, 0, 0.0)


def test_deal_consumes_three_cards_in_order():
    shoe = Shoe(shuffle=False)
    expected = shoe.cards[:3]
    session = StrategySession(shoe=shoe)
    question = session.next_question()
    assert (*question.player_hand, question.dealer_upcard) == expected
    assert shoe.position == 3
    assert session.answered == 0


def test_scoring_correct_then_incorrect():
    session = StrategySession(seed=42)
    question = session.next_question()
    expected = basic_strategy(question.player_hand, question.dealer_upcard)
    assert session.submit(expected).correct
    question = session.next_question()
    expected = basic_strategy(question.player_hand, question.dealer_upcard)
    wrong = next(action for action in Action if action != expected)
    feedback = session.submit(wrong)
    assert not feedback.correct
    assert feedback.recommended == expected
    assert (session.answered, session.correct, session.incorrect, session.accuracy) == (2, 1, 1, 50.0)


def test_invalid_answer_keeps_question_and_statistics():
    session = StrategySession()
    question = session.next_question()
    with pytest.raises(ValueError):
        session.submit('invalid')
    assert session.question is question
    assert session.feedback is None
    assert session.answered == 0
    assert session.shoe.position == 3


def test_lowercase_and_whitespace_are_accepted():
    session = StrategySession()
    question = session.next_question()
    answer = basic_strategy(question.player_hand, question.dealer_upcard)
    assert session.submit(' ' + answer.value.lower() + ' ').correct


def test_no_answer_before_dealing():
    with pytest.raises(RuntimeError):
        StrategySession().submit('H')


def test_no_double_scoring_or_skipping():
    session = StrategySession()
    session.next_question()
    with pytest.raises(RuntimeError):
        session.next_question()
    session.submit('H')
    with pytest.raises(RuntimeError):
        session.submit('S')
    assert session.answered == 1


@pytest.mark.parametrize('remaining', [0, 1, 2])
def test_reshuffle_before_incomplete_deal(remaining):
    shoe = Shoe(shuffle=False)
    shoe.draw_many(shoe.remaining - remaining)
    session = StrategySession(shoe=shoe)
    session.next_question()
    assert session.shoe_number == 2
    assert shoe.position == 3
    assert shoe.remaining == 309


def test_exactly_three_cards_are_used_before_shuffle():
    shoe = Shoe(shuffle=False)
    shoe.draw_many(309)
    session = StrategySession(shoe=shoe)
    session.next_question()
    assert session.shoe_number == 1
    assert shoe.remaining == 0
    session.submit('S')
    session.next_question()
    assert session.shoe_number == 2
    assert session.answered == 1


def test_seeded_questions_are_reproducible():
    first, second = StrategySession(seed=42), StrategySession(seed=42)
    for _ in range(110):
        assert first.next_question() == second.next_question()
        first.submit('H')
        second.submit('H')
    assert first.shoe_number == second.shoe_number == 2
