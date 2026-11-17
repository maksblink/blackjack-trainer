"""Terminal interaction and module entry-point tests."""

import subprocess
import sys

import pytest

from blackjack_trainer.cards import Card
from blackjack_trainer.cli import describe_question, run_cli
from blackjack_trainer.shoe import Shoe
from blackjack_trainer.training import Question, StrategySession


def interaction(answers, **kwargs):
    messages = []
    iterator = iter(answers)
    def read(_prompt):
        try:
            return next(iterator)
        except StopIteration:
            raise AssertionError('Unexpected extra input request')
    session = kwargs.pop('session', StrategySession(shoe=Shoe(shuffle=False)))
    run_cli(session, input_func=read, output_func=messages.append, **kwargs)
    return session, '\n'.join(messages)


def test_quit_without_answer_is_not_scored():
    session, output = interaction(['q'])
    assert session.answered == 0
    assert 'SESSION SUMMARY' in output
    assert 'Accuracy: 0.0%' in output


def test_invalid_input_retries_same_question():
    # Ordered shoe starts player 2/3 against dealer 4: Hit.
    session, output = interaction(['?', ' h '], round_limit=1)
    assert session.answered == session.correct == 1
    assert session.shoe.position == 3
    assert 'Invalid action' in output
    assert 'Correct! Recommended: H (Hit).' in output


def test_wrong_answer_shows_recommendation():
    session, output = interaction(['s', 'q'])
    assert session.incorrect == 1
    assert 'Incorrect. Recommended: H (Hit).' in output


def test_continue_validation_and_two_round_limit():
    session, output = interaction(['h', 'wrong', '', 'h'], round_limit=2)
    assert session.answered == 2
    assert session.shoe.position == 6
    assert 'Press Enter to continue' in output


@pytest.mark.parametrize('exception', [EOFError, KeyboardInterrupt])
def test_input_interrupt_shows_summary_without_scoring(exception):
    messages = []
    def read(_prompt):
        raise exception()
    session = run_cli(input_func=read, output_func=messages.append)
    assert session.answered == 0
    assert 'SESSION SUMMARY' in '\n'.join(messages)


def test_interrupt_after_answer_keeps_score():
    calls = 0
    def read(_prompt):
        nonlocal calls
        calls += 1
        if calls == 1:
            return 'h'
        raise EOFError()
    session = run_cli(input_func=read, output_func=lambda _: None)
    assert session.answered == 1


@pytest.mark.parametrize('limit', [0, -1, True, 1.5])
def test_invalid_round_limit(limit):
    with pytest.raises(ValueError):
        run_cli(round_limit=limit)


def test_reshuffle_is_announced():
    shoe = Shoe(shuffle=False)
    shoe.draw_many(311)
    session, output = interaction(['q'], session=StrategySession(shoe=shoe))
    assert session.shoe_number == 2
    assert 'New shoe' in output


@pytest.mark.parametrize('ranks,label', [(('A', 'K'), 'Blackjack (21)'),
                                         (('A', '6'), 'Soft 17'),
                                         (('10', '6'), 'Hard 16'),
                                         (('8', '8'), 'Pair of 8')])
def test_hand_display(ranks, label):
    question = Question(tuple(Card(rank, '♠') for rank in ranks), Card('4', '♥'))
    output = describe_question(question)
    assert label in output
    assert 'Dealer upcard: 4♥' in output
    assert 'Recommended' not in output


@pytest.mark.parametrize('arguments', [[], ['cli'], ['--seed', '42'], ['--rounds', '2']])
def test_module_launch_and_quit(arguments):
    result = subprocess.run([sys.executable, '-m', 'blackjack_trainer', *arguments],
                            input='q\n', text=True, capture_output=True, timeout=10)
    assert result.returncode == 0
    assert 'SESSION SUMMARY' in result.stdout
    assert 'Answered: 0' in result.stdout


@pytest.mark.parametrize('arguments', [['--rounds', '0'], ['--rounds', '-1'],
                                      ['--rounds', 'abc'], ['unknown']])
def test_argument_errors(arguments):
    result = subprocess.run([sys.executable, '-m', 'blackjack_trainer', *arguments],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 2


def test_version_does_not_start_training():
    result = subprocess.run([sys.executable, '-m', 'blackjack_trainer', '--version'],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0
    assert '0.1.0' in result.stdout
    assert 'Your action' not in result.stdout
